"""Dependency-aware task graph and scheduler primitives for Forge-AI."""

from __future__ import annotations

import time
from collections.abc import Callable, Iterable, Mapping, Sequence
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import dataclass
from types import MappingProxyType

from .agents import Task

TASK_STATUS_QUEUED = "queued"
TASK_STATUS_RUNNING = "running"
TASK_STATUS_BLOCKED = "blocked"
TASK_STATUS_COMPLETED = "completed"
TASK_STATUS_FAILED = "failed"


@dataclass(frozen=True)
class RetryPolicy:
    """Defines retry behavior for task execution."""

    max_retries: int = 0
    backoff_seconds: float = 0.0


@dataclass(frozen=True)
class SchedulerResult:
    """Represents the scheduler outcome for a task graph."""

    results: dict[str, object]
    states: dict[str, str]
    attempts: dict[str, int]


class TaskGraph:
    """Represents a directed acyclic graph of planned tasks."""

    def __init__(self, tasks: Sequence[Task]) -> None:
        self._tasks = {task.task_id: task for task in tasks}
        if len(self._tasks) != len(tasks):
            raise ValueError("Task identifiers must be unique")
        self._validate_dependencies()
        self._validate_acyclic()

    @property
    def tasks(self) -> Mapping[str, Task]:
        return MappingProxyType(self._tasks)

    def ready_tasks(self, completed: Iterable[str], pending: Iterable[str]) -> list[Task]:
        completed_set = set(completed)
        pending_set = set(pending)
        ready = [
            task
            for task_id, task in self._tasks.items()
            if task_id in pending_set and set(task.dependencies).issubset(completed_set)
        ]
        return sorted(ready, key=lambda item: (item.priority, item.order))

    def blocked_tasks(self, completed: Iterable[str], pending: Iterable[str]) -> list[Task]:
        completed_set = set(completed)
        pending_set = set(pending)
        blocked = [
            task
            for task_id, task in self._tasks.items()
            if task_id in pending_set and not set(task.dependencies).issubset(completed_set)
        ]
        return sorted(blocked, key=lambda item: (item.priority, item.order))

    def to_dependency_map(self) -> dict[str, list[str]]:
        return {task_id: list(task.dependencies) for task_id, task in self._tasks.items()}

    def _validate_dependencies(self) -> None:
        task_ids = set(self._tasks)
        for task in self._tasks.values():
            unknown = set(task.dependencies) - task_ids
            if unknown:
                raise ValueError(f"Task {task.task_id} has unknown dependencies: {sorted(unknown)}")

    def _validate_acyclic(self) -> None:
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(task_id: str) -> None:
            if task_id in visited:
                return
            if task_id in visiting:
                raise ValueError("Task dependencies must form a directed acyclic graph")
            visiting.add(task_id)
            for dependency in self._tasks[task_id].dependencies:
                visit(dependency)
            visiting.remove(task_id)
            visited.add(task_id)

        for task_id in self._tasks:
            visit(task_id)


class TaskScheduler:
    """Execute tasks in parallel while respecting task dependencies."""

    def __init__(self, max_workers: int = 4) -> None:
        self.max_workers = max(1, max_workers)

    def execute(
        self,
        graph: TaskGraph,
        executor: Callable[[Task, int], object],
        retry_policy: RetryPolicy,
    ) -> SchedulerResult:
        tasks = graph.tasks
        pending = set(tasks.keys())
        completed: set[str] = set()
        failed: set[str] = set()
        states = {
            task_id: (TASK_STATUS_BLOCKED if task.dependencies else TASK_STATUS_QUEUED)
            for task_id, task in tasks.items()
        }
        attempts = {task_id: 0 for task_id in tasks}
        results: dict[str, object] = {}
        running: dict[Future[object], str] = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            while pending or running:
                for task in graph.blocked_tasks(completed=completed, pending=pending):
                    if any(dependency in failed for dependency in task.dependencies):
                        states[task.task_id] = TASK_STATUS_BLOCKED
                        pending.discard(task.task_id)
                        failed.add(task.task_id)
                    elif task.task_id in pending:
                        states[task.task_id] = TASK_STATUS_BLOCKED

                ready_tasks = [
                    task
                    for task in graph.ready_tasks(completed=completed, pending=pending)
                    if task.task_id not in running.values()
                ]
                while ready_tasks and len(running) < self.max_workers:
                    task = ready_tasks.pop(0)
                    attempts[task.task_id] += 1
                    states[task.task_id] = TASK_STATUS_RUNNING
                    future = pool.submit(executor, task, attempts[task.task_id])
                    running[future] = task.task_id

                if not running:
                    break

                completed_futures, _ = wait(running.keys(), return_when=FIRST_COMPLETED)
                for future in completed_futures:
                    task_id = running.pop(future)
                    task = tasks[task_id]
                    result = future.result()
                    results[task_id] = result
                    status = getattr(result, "status", TASK_STATUS_COMPLETED)
                    if status == TASK_STATUS_COMPLETED:
                        states[task_id] = TASK_STATUS_COMPLETED
                        pending.discard(task_id)
                        completed.add(task_id)
                        continue

                    allowed_retries = (
                        retry_policy.max_retries if task.max_retries is None else task.max_retries
                    )
                    if attempts[task_id] <= allowed_retries:
                        states[task_id] = TASK_STATUS_QUEUED
                        if retry_policy.backoff_seconds:
                            time.sleep(retry_policy.backoff_seconds)
                        continue

                    states[task_id] = TASK_STATUS_FAILED
                    pending.discard(task_id)
                    failed.add(task_id)

        for task_id in list(pending):
            states[task_id] = TASK_STATUS_BLOCKED
            failed.add(task_id)
            pending.discard(task_id)

        return SchedulerResult(results=results, states=states, attempts=attempts)
