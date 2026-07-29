"""Parallel scheduler for the orchestration framework.

Executes independent tasks concurrently using a thread pool while honoring
dependency constraints imposed by the TaskDAG.  Tasks that are BLOCKED wait
until their predecessors complete, then automatically become eligible for
scheduling.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from typing import Any

from .dag import TaskDAG
from .models import OrchestratedTask, TaskStatus
from .retry import RetryManager

logger = logging.getLogger("forge.orchestration.scheduler")

# Type alias for the callable that actually runs a task
ExecuteFn = Callable[[OrchestratedTask], Any]


class Scheduler:
    """Runs tasks from a TaskDAG in parallel while respecting dependencies.

    The scheduler continuously polls for newly-ready tasks and submits them
    to a thread pool.  When a task finishes, it triggers a re-evaluation of
    all blocked tasks.  Retry logic is applied for FAILED tasks that have
    remaining budget according to the associated RetryManager.

    Example::

        dag = TaskDAG()
        # ... add tasks and dependencies ...
        dag.validate()

        scheduler = Scheduler(max_workers=4)
        summary = scheduler.run(dag, execute_fn=lambda task: agent.run(task.description))
    """

    def __init__(
        self,
        max_workers: int = 4,
        retry_manager: RetryManager | None = None,
    ) -> None:
        self._max_workers = max_workers
        self._retry_manager = retry_manager or RetryManager()
        self._logger = logger
        self._lock = threading.Lock()

    def run(self, dag: TaskDAG, execute_fn: ExecuteFn) -> list[OrchestratedTask]:
        """Execute all tasks in the DAG and return the completed task list.

        Independent tasks run concurrently; dependent tasks wait for their
        predecessors.  Failed tasks are retried according to the retry policy.

        Args:
            dag: The TaskDAG containing all tasks and their dependencies.
            execute_fn: Callable that accepts an OrchestratedTask and performs
                the actual work.  It may raise; the scheduler handles exceptions.

        Returns:
            All tasks (in their terminal state) after the run completes.
        """
        dag.validate()

        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            pending: dict[str, Future[Any]] = {}
            completed_ids: set[str] = set()

            while not dag.is_complete():
                ready = dag.get_ready_tasks()

                # Submit ready tasks that are not already in flight
                for task in ready:
                    if task.id not in pending:
                        task.mark_running()
                        future = executor.submit(self._run_task, task, execute_fn)
                        pending[task.id] = future
                        self._logger.info("Submitted task '%s' (%s).", task.title, task.id)

                if not pending:
                    # Nothing in-flight and DAG is not complete — check for failures
                    remaining = [
                        t for t in dag.all_tasks()
                        if t.status not in (TaskStatus.COMPLETED, TaskStatus.FAILED)
                    ]
                    if not remaining:
                        break
                    # All remaining tasks are either FAILED or permanently BLOCKED
                    self._logger.warning(
                        "Scheduler stalled: %d task(s) cannot proceed.", len(remaining)
                    )
                    break

                # Wait for at least one future to finish before re-looping
                done_ids = []
                for task_id, future in list(pending.items()):
                    if future.done():
                        done_ids.append(task_id)

                if not done_ids:
                    # Block until the next future completes
                    for future in as_completed(pending.values()):
                        break  # wake up and re-evaluate

                # Process completed futures
                for task_id in list(pending.keys()):
                    future = pending[task_id]
                    if not future.done():
                        continue

                    task = dag.get_task(task_id)
                    assert task is not None  # invariant: task is always registered

                    # Re-raise to surface unexpected errors; task state is authoritative
                    exc = future.exception()
                    if exc is not None:
                        self._logger.debug(
                            "Future for task '%s' raised: %s", task_id, exc
                        )

                    del pending[task_id]

                    if task.status == TaskStatus.COMPLETED:
                        completed_ids.add(task_id)
                        self._logger.info("Task '%s' completed.", task.title)
                    elif task.status == TaskStatus.FAILED:
                        if self._retry_manager.should_retry(task):
                            self._logger.info(
                                "Retrying task '%s' (attempt %d).",
                                task.title,
                                task.retry_count + 1,
                            )
                            self._retry_manager.prepare_retry(task)
                            # task is now QUEUED again; scheduler will pick it up
                        else:
                            self._logger.warning(
                                "Task '%s' failed permanently after %d attempt(s).",
                                task.title,
                                task.retry_count + 1,
                            )

        return dag.all_tasks()

    def _run_task(self, task: OrchestratedTask, execute_fn: ExecuteFn) -> None:
        """Worker function executed inside the thread pool.

        Args:
            task: The task to execute.
            execute_fn: The callable that performs the work.
        """
        try:
            result = execute_fn(task)
            task.mark_completed(result)
        except Exception as exc:  # pragma: no cover - defensive
            self._logger.exception("Task '%s' raised an exception.", task.title)
            task.mark_failed(str(exc))
