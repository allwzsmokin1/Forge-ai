"""Tests for the Phase 3 dependency-aware scheduler."""

from __future__ import annotations

import threading
import time

from forge.agents.planner import Task
from forge.orchestrator import TaskResult
from forge.scheduler import (
    TASK_STATUS_COMPLETED,
    TASK_STATUS_FAILED,
    RetryPolicy,
    TaskGraph,
    TaskScheduler,
)


def build_task(
    task_id: str,
    order: int,
    dependencies: tuple[str, ...] = (),
    max_retries: int | None = None,
) -> Task:
    return Task(
        title=task_id,
        description=task_id,
        priority=1,
        order=order,
        task_id=task_id,
        task_type="code",
        dependencies=dependencies,
        max_retries=max_retries,
    )


def test_task_graph_rejects_cycles() -> None:
    task_a = build_task("task-a", 1, dependencies=("task-b",))
    task_b = build_task("task-b", 2, dependencies=("task-a",))

    try:
        TaskGraph([task_a, task_b])
    except ValueError as exc:
        assert "directed acyclic graph" in str(exc)
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("Expected cyclic task graph to be rejected")


def test_scheduler_runs_independent_tasks_in_parallel() -> None:
    scheduler = TaskScheduler(max_workers=2)
    graph = TaskGraph([build_task("task-a", 1), build_task("task-b", 2)])
    lock = threading.Lock()
    running = 0
    max_running = 0

    def execute(task: Task, attempt: int) -> TaskResult:
        nonlocal running, max_running
        with lock:
            running += 1
            max_running = max(max_running, running)
        time.sleep(0.05)
        with lock:
            running -= 1
        return TaskResult(
            task=task, agent_name="TestAgent", status=TASK_STATUS_COMPLETED, attempts=attempt
        )

    result = scheduler.execute(graph=graph, executor=execute, retry_policy=RetryPolicy())

    assert result.states["task-a"] == TASK_STATUS_COMPLETED
    assert result.states["task-b"] == TASK_STATUS_COMPLETED
    assert max_running == 2


def test_scheduler_retries_failed_tasks() -> None:
    scheduler = TaskScheduler(max_workers=1)
    graph = TaskGraph([build_task("task-a", 1, max_retries=1)])
    attempts = {"count": 0}

    def execute(task: Task, attempt: int) -> TaskResult:
        attempts["count"] += 1
        if attempts["count"] == 1:
            return TaskResult(
                task=task,
                agent_name="DebugAgent",
                status=TASK_STATUS_FAILED,
                error="transient",
                attempts=attempt,
            )
        return TaskResult(
            task=task, agent_name="DebugAgent", status=TASK_STATUS_COMPLETED, attempts=attempt
        )

    result = scheduler.execute(
        graph=graph, executor=execute, retry_policy=RetryPolicy(max_retries=0)
    )

    assert attempts["count"] == 2
    assert graph.tasks["task-a"].max_retries == 1
    assert result.attempts["task-a"] == 2
    assert result.states["task-a"] == TASK_STATUS_COMPLETED
