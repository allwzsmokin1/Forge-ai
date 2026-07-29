"""Tests for the RetryManager and RetryPolicy."""

from __future__ import annotations

from forge.orchestration.models import OrchestratedTask, RetryPolicy, TaskStatus
from forge.orchestration.retry import RetryManager


def _make_task(title: str = "T") -> OrchestratedTask:
    return OrchestratedTask(title=title, description=title)


class TestRetryManager:
    def test_should_retry_returns_false_for_non_failed_task(self) -> None:
        manager = RetryManager()
        task = _make_task()
        assert manager.should_retry(task) is False

    def test_should_retry_returns_true_within_budget(self) -> None:
        manager = RetryManager(RetryPolicy(max_retries=3))
        task = _make_task()
        task.mark_failed("err")
        assert manager.should_retry(task) is True

    def test_should_retry_returns_false_when_budget_exhausted(self) -> None:
        manager = RetryManager(RetryPolicy(max_retries=1))
        task = _make_task()
        task.mark_failed("err")
        task.retry_count = 1
        assert manager.should_retry(task) is False

    def test_prepare_retry_resets_task_to_queued(self) -> None:
        manager = RetryManager()
        task = _make_task()
        task.mark_failed("err")
        manager.prepare_retry(task)
        assert task.status == TaskStatus.QUEUED

    def test_prepare_retry_increments_retry_count(self) -> None:
        manager = RetryManager()
        task = _make_task()
        task.mark_failed("err")
        manager.prepare_retry(task)
        assert task.retry_count == 1

    def test_prepare_retry_clears_error_and_result(self) -> None:
        manager = RetryManager()
        task = _make_task()
        task.mark_failed("err")
        task.result = "old"
        manager.prepare_retry(task)
        assert task.error is None
        assert task.result is None

    def test_compute_delay_increases_with_attempts(self) -> None:
        policy = RetryPolicy(delay_seconds=1.0, backoff_factor=2.0)
        manager = RetryManager(policy)
        task = _make_task()
        task.retry_count = 1
        delay1 = manager.compute_delay(task)
        task.retry_count = 2
        delay2 = manager.compute_delay(task)
        assert delay2 > delay1

    def test_wait_with_zero_delay_does_not_sleep(self) -> None:
        """Ensure wait returns quickly when delay is zero (no actual sleep)."""
        import time

        policy = RetryPolicy(delay_seconds=0.0)
        manager = RetryManager(policy)
        task = _make_task()
        start = time.monotonic()
        manager.wait(task)
        elapsed = time.monotonic() - start
        assert elapsed < 1.0

    def test_policy_property_returns_configured_policy(self) -> None:
        policy = RetryPolicy(max_retries=7)
        manager = RetryManager(policy)
        assert manager.policy is policy

    def test_default_policy_is_used_when_none_provided(self) -> None:
        manager = RetryManager()
        assert manager.policy.max_retries == 3
