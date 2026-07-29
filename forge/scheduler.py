"""Parallel task scheduler for Forge-AI orchestration."""

from __future__ import annotations

import logging
from collections.abc import Callable
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import dataclass, replace
from datetime import UTC, datetime

from .logger import log_structured, logger
from .tasks import Task, TaskExecution, TaskExecutionError, TaskGraph, TaskState, TaskStatus

StateChangeCallback = Callable[[TaskState], None]
TaskExecutor = Callable[[Task, int], TaskExecution]


@dataclass(frozen=True)
class SchedulerReport:
    """Final scheduler output."""

    task_states: list[TaskState]
    task_graph: dict[str, tuple[str, ...]]
    max_parallelism: int

    @property
    def success(self) -> bool:
        """Return whether every task completed successfully."""

        return all(state.status == TaskStatus.COMPLETED for state in self.task_states)


class Scheduler:
    """Execute dependency-aware tasks in parallel."""

    def __init__(
        self,
        max_workers: int = 4,
        logger_instance: logging.Logger | None = None,
    ) -> None:
        self.max_workers = max_workers
        self._logger = logger_instance or logger

    def run(
        self,
        tasks: list[Task],
        executor: TaskExecutor,
        on_state_change: StateChangeCallback | None = None,
    ) -> SchedulerReport:
        """Run tasks while respecting dependency order and retry policy."""

        graph = TaskGraph(tasks)
        states = {
            task.task_id: TaskState(
                task=task,
                status=TaskStatus.QUEUED if not task.dependencies else TaskStatus.BLOCKED,
            )
            for task in graph.tasks
        }
        for state in states.values():
            self._emit_state_change(state, on_state_change)

        in_flight: dict[Future[TaskExecution], str] = {}
        max_parallelism = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            while True:
                self._refresh_ready_states(states, graph, on_state_change)

                ready_states = [
                    state
                    for state in states.values()
                    if state.status == TaskStatus.QUEUED
                    and state.task.task_id not in in_flight.values()
                ]
                for state in ready_states:
                    state.status = TaskStatus.RUNNING
                    state.attempts += 1
                    state.started_at = self._now_iso()
                    state.error = None
                    self._emit_state_change(state, on_state_change)
                    future = pool.submit(executor, state.task, state.attempts)
                    in_flight[future] = state.task.task_id
                    max_parallelism = max(max_parallelism, len(in_flight))

                if not in_flight:
                    unresolved = [state for state in states.values() if not state.is_terminal]
                    if not unresolved or not any(
                        state.status == TaskStatus.QUEUED for state in unresolved
                    ):
                        break

                if not in_flight:
                    continue

                completed, _ = wait(set(in_flight), return_when=FIRST_COMPLETED)
                for future in completed:
                    task_id = in_flight.pop(future)
                    state = states[task_id]
                    try:
                        outcome = future.result()
                        state.assigned_agent = outcome.agent_name
                        state.result = outcome.result
                        state.error = None
                        state.status = TaskStatus.COMPLETED
                        state.completed_at = self._now_iso()
                        self._emit_state_change(state, on_state_change)
                        log_structured(
                            self._logger,
                            logging.INFO,
                            "task_completed",
                            task_id=task_id,
                            agent_name=outcome.agent_name,
                            attempts=state.attempts,
                        )
                    except TaskExecutionError as exc:
                        state.assigned_agent = exc.agent_name
                        state.result = None
                        state.error = str(exc)
                        if state.attempts < state.task.retry_policy.max_attempts:
                            state.status = TaskStatus.QUEUED
                            state.completed_at = None
                        else:
                            state.status = TaskStatus.FAILED
                            state.completed_at = self._now_iso()
                        self._emit_state_change(state, on_state_change)
                        log_structured(
                            self._logger,
                            logging.WARNING,
                            "task_failed",
                            task_id=task_id,
                            agent_name=exc.agent_name,
                            attempts=state.attempts,
                            error=str(exc),
                            will_retry=state.status == TaskStatus.QUEUED,
                        )
        self._refresh_ready_states(states, graph, on_state_change)
        ordered_states = [states[task.task_id] for task in graph.tasks]
        return SchedulerReport(
            task_states=ordered_states,
            task_graph=graph.adjacency_map(),
            max_parallelism=max_parallelism,
        )

    def _refresh_ready_states(
        self,
        states: dict[str, TaskState],
        graph: TaskGraph,
        on_state_change: StateChangeCallback | None,
    ) -> None:
        for task in graph.tasks:
            state = states[task.task_id]
            if state.is_terminal or state.status == TaskStatus.RUNNING:
                continue

            dependency_states = [states[dependency] for dependency in task.dependencies]
            if dependency_states and any(
                dependency_state.status == TaskStatus.FAILED
                for dependency_state in dependency_states
            ):
                blocked_by = [
                    dependency_state.task.task_id
                    for dependency_state in dependency_states
                    if dependency_state.status == TaskStatus.FAILED
                ]
                if (
                    state.status != TaskStatus.BLOCKED
                    or state.error != f"Blocked by failed dependencies: {', '.join(blocked_by)}"
                ):
                    state.status = TaskStatus.BLOCKED
                    state.error = f"Blocked by failed dependencies: {', '.join(blocked_by)}"
                    self._emit_state_change(state, on_state_change)
                continue

            if dependency_states and not all(
                dependency_state.status == TaskStatus.COMPLETED
                for dependency_state in dependency_states
            ):
                if state.status != TaskStatus.BLOCKED:
                    state.status = TaskStatus.BLOCKED
                    self._emit_state_change(state, on_state_change)
                continue

            if state.status != TaskStatus.QUEUED:
                state.status = TaskStatus.QUEUED
                state.error = None
                self._emit_state_change(state, on_state_change)

    def _emit_state_change(
        self,
        state: TaskState,
        on_state_change: StateChangeCallback | None,
    ) -> None:
        if on_state_change is not None:
            on_state_change(replace(state))

    def _now_iso(self) -> str:
        return datetime.now(tz=UTC).isoformat()
