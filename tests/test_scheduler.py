"""Tests for the parallel Scheduler."""

from __future__ import annotations

from typing import Any

from forge.orchestration.dag import TaskDAG
from forge.orchestration.models import OrchestratedTask, RetryPolicy, TaskStatus
from forge.orchestration.retry import RetryManager
from forge.orchestration.scheduler import Scheduler


def _make_task(title: str, priority: int = 3) -> OrchestratedTask:
    return OrchestratedTask(title=title, description=title, priority=priority)


def _success_fn(task: OrchestratedTask) -> str:
    return f"done:{task.title}"


def _failing_fn(task: OrchestratedTask) -> Any:
    raise RuntimeError(f"Simulated failure for {task.title}")


class TestSchedulerBasic:
    def test_single_task_completes(self) -> None:
        dag = TaskDAG()
        t = _make_task("T1")
        dag.add_task(t)
        scheduler = Scheduler(max_workers=2)
        results = scheduler.run(dag, _success_fn)
        assert any(r.status == TaskStatus.COMPLETED for r in results)

    def test_single_task_result_stored(self) -> None:
        dag = TaskDAG()
        t = _make_task("T1")
        dag.add_task(t)
        scheduler = Scheduler(max_workers=2)
        scheduler.run(dag, _success_fn)
        assert t.result == "done:T1"

    def test_independent_tasks_all_complete(self) -> None:
        dag = TaskDAG()
        tasks = [_make_task(f"T{i}") for i in range(4)]
        for task in tasks:
            dag.add_task(task)
        scheduler = Scheduler(max_workers=4)
        scheduler.run(dag, _success_fn)
        for task in tasks:
            assert task.status == TaskStatus.COMPLETED

    def test_dependency_respected_order(self) -> None:
        """t2 must run after t1."""
        execution_order: list[str] = []

        def ordered_fn(task: OrchestratedTask) -> str:
            execution_order.append(task.title)
            return task.title

        dag = TaskDAG()
        t1 = _make_task("first")
        t2 = OrchestratedTask(title="second", description="second", dependencies=[t1.id])
        dag.add_task(t1)
        dag.add_task(t2)
        Scheduler(max_workers=2).run(dag, ordered_fn)
        assert execution_order.index("first") < execution_order.index("second")

    def test_empty_dag_returns_empty_list(self) -> None:
        dag = TaskDAG()
        results = Scheduler().run(dag, _success_fn)
        assert results == []


class TestSchedulerRetry:
    def test_failed_task_retried_up_to_policy_limit(self) -> None:
        attempt_counts: dict[str, int] = {}

        def flaky_fn(task: OrchestratedTask) -> str:
            attempt_counts[task.title] = attempt_counts.get(task.title, 0) + 1
            if attempt_counts[task.title] < 3:
                raise RuntimeError("transient")
            return "ok"

        policy = RetryPolicy(max_retries=3, delay_seconds=0.0)
        manager = RetryManager(policy)
        dag = TaskDAG()
        t = _make_task("flaky")
        dag.add_task(t)
        Scheduler(max_workers=1, retry_manager=manager).run(dag, flaky_fn)
        assert t.status == TaskStatus.COMPLETED
        assert attempt_counts["flaky"] == 3

    def test_task_permanently_fails_when_budget_exhausted(self) -> None:
        policy = RetryPolicy(max_retries=2, delay_seconds=0.0)
        manager = RetryManager(policy)
        dag = TaskDAG()
        t = _make_task("always-fail")
        dag.add_task(t)
        Scheduler(max_workers=1, retry_manager=manager).run(dag, _failing_fn)
        assert t.status == TaskStatus.FAILED
        assert t.retry_count == 2

    def test_no_retry_policy_leaves_task_failed(self) -> None:
        policy = RetryPolicy(max_retries=0, delay_seconds=0.0)
        manager = RetryManager(policy)
        dag = TaskDAG()
        t = _make_task("fail-once")
        dag.add_task(t)
        Scheduler(max_workers=1, retry_manager=manager).run(dag, _failing_fn)
        assert t.status == TaskStatus.FAILED
        assert t.retry_count == 0


class TestSchedulerConcurrency:
    def test_scheduler_handles_max_workers_one(self) -> None:
        """Verify the scheduler still works when limited to one worker."""
        dag = TaskDAG()
        tasks = [_make_task(f"T{i}") for i in range(3)]
        for task in tasks:
            dag.add_task(task)
        Scheduler(max_workers=1).run(dag, _success_fn)
        for task in tasks:
            assert task.status == TaskStatus.COMPLETED

    def test_chain_of_five_tasks_completes_in_order(self) -> None:
        execution_order: list[str] = []

        def record_fn(task: OrchestratedTask) -> str:
            execution_order.append(task.title)
            return task.title

        dag = TaskDAG()
        prev = _make_task("T0")
        dag.add_task(prev)
        for i in range(1, 5):
            curr = OrchestratedTask(
                title=f"T{i}", description=f"T{i}", dependencies=[prev.id]
            )
            dag.add_task(curr)
            prev = curr

        Scheduler(max_workers=2).run(dag, record_fn)
        for i in range(len(execution_order) - 1):
            a, b = execution_order[i], execution_order[i + 1]
            assert int(a[1:]) < int(b[1:])
