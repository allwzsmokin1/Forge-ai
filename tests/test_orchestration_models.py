"""Tests for the Phase 3 orchestration models."""

from __future__ import annotations

from forge.orchestration.models import (
    ExecutionSummary,
    OrchestratedTask,
    RetryPolicy,
    TaskStatus,
)

# ---------------------------------------------------------------------------
# RetryPolicy
# ---------------------------------------------------------------------------


class TestRetryPolicy:
    def test_default_values(self) -> None:
        policy = RetryPolicy()
        assert policy.max_retries == 3
        assert policy.delay_seconds == 1.0
        assert policy.backoff_factor == 2.0

    def test_compute_delay_first_attempt(self) -> None:
        policy = RetryPolicy(delay_seconds=1.0, backoff_factor=2.0)
        assert policy.compute_delay(0) == 1.0

    def test_compute_delay_second_attempt(self) -> None:
        policy = RetryPolicy(delay_seconds=1.0, backoff_factor=2.0)
        assert policy.compute_delay(1) == 2.0

    def test_compute_delay_third_attempt(self) -> None:
        policy = RetryPolicy(delay_seconds=1.0, backoff_factor=2.0)
        assert policy.compute_delay(2) == 4.0

    def test_zero_delay(self) -> None:
        policy = RetryPolicy(delay_seconds=0.0)
        assert policy.compute_delay(5) == 0.0


# ---------------------------------------------------------------------------
# OrchestratedTask
# ---------------------------------------------------------------------------


class TestOrchestratedTask:
    def test_default_status_is_queued(self) -> None:
        task = OrchestratedTask(title="T", description="Do something")
        assert task.status == TaskStatus.QUEUED

    def test_id_is_generated_automatically(self) -> None:
        t1 = OrchestratedTask(title="T1", description="A")
        t2 = OrchestratedTask(title="T2", description="B")
        assert t1.id != t2.id

    def test_is_ready_with_no_dependencies(self) -> None:
        task = OrchestratedTask(title="T", description="D")
        assert task.is_ready(set()) is True

    def test_is_ready_when_dependency_satisfied(self) -> None:
        dep = OrchestratedTask(title="Dep", description="D")
        task = OrchestratedTask(title="T", description="D", dependencies=[dep.id])
        assert task.is_ready({dep.id}) is True

    def test_is_not_ready_when_dependency_missing(self) -> None:
        dep = OrchestratedTask(title="Dep", description="D")
        task = OrchestratedTask(title="T", description="D", dependencies=[dep.id])
        assert task.is_ready(set()) is False

    def test_mark_running_sets_status(self) -> None:
        task = OrchestratedTask(title="T", description="D")
        task.mark_running()
        assert task.status == TaskStatus.RUNNING

    def test_mark_completed_stores_result(self) -> None:
        task = OrchestratedTask(title="T", description="D")
        task.mark_completed("output")
        assert task.status == TaskStatus.COMPLETED
        assert task.result == "output"

    def test_mark_failed_stores_error(self) -> None:
        task = OrchestratedTask(title="T", description="D")
        task.mark_failed("oops")
        assert task.status == TaskStatus.FAILED
        assert task.error == "oops"

    def test_mark_blocked(self) -> None:
        task = OrchestratedTask(title="T", description="D")
        task.mark_blocked()
        assert task.status == TaskStatus.BLOCKED


# ---------------------------------------------------------------------------
# ExecutionSummary
# ---------------------------------------------------------------------------


class TestExecutionSummary:
    def test_default_success_false(self) -> None:
        summary = ExecutionSummary(goal="g", total=0, completed=0, failed=0, skipped=0)
        assert summary.success is False

    def test_fields_stored_correctly(self) -> None:
        summary = ExecutionSummary(
            goal="build feature",
            total=5,
            completed=4,
            failed=1,
            skipped=0,
            success=False,
        )
        assert summary.total == 5
        assert summary.completed == 4
        assert summary.failed == 1
