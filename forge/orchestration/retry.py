"""Retry policy management for the orchestration framework.

Provides configurable retry logic with exponential backoff so the scheduler
can automatically re-queue failed tasks up to a defined limit.
"""

from __future__ import annotations

import logging
import time

from .models import OrchestratedTask, RetryPolicy, TaskStatus

logger = logging.getLogger("forge.orchestration.retry")


class RetryManager:
    """Applies a RetryPolicy to orchestrated tasks.

    Example::

        policy = RetryPolicy(max_retries=3, delay_seconds=0.5, backoff_factor=2.0)
        manager = RetryManager(policy)

        if manager.should_retry(task):
            manager.prepare_retry(task)   # resets state, increments counter
            manager.wait(task)            # sleeps for the computed backoff delay
    """

    def __init__(self, policy: RetryPolicy | None = None) -> None:
        self._policy = policy or RetryPolicy()
        self._logger = logger

    @property
    def policy(self) -> RetryPolicy:
        """The active retry policy."""
        return self._policy

    def should_retry(self, task: OrchestratedTask) -> bool:
        """Return True when the task is eligible for another attempt.

        A task is eligible when it has failed and has not yet exhausted its
        configured retry budget.

        Args:
            task: The task to evaluate.
        """
        if task.status != TaskStatus.FAILED:
            return False
        eligible = task.retry_count < self._policy.max_retries
        self._logger.debug(
            "Task '%s' retry eligibility: %s (attempt %d / %d)",
            task.title,
            eligible,
            task.retry_count,
            self._policy.max_retries,
        )
        return eligible

    def prepare_retry(self, task: OrchestratedTask) -> None:
        """Reset task state for re-execution and increment the retry counter.

        Args:
            task: The task to prepare for retry.
        """
        task.retry_count += 1
        task.error = None
        task.result = None
        task.status = TaskStatus.QUEUED
        self._logger.info(
            "Prepared task '%s' for retry attempt %d.", task.title, task.retry_count
        )

    def compute_delay(self, task: OrchestratedTask) -> float:
        """Return the wait time in seconds before the next retry for this task.

        Args:
            task: The task about to be retried.
        """
        attempt = max(0, task.retry_count - 1)
        delay = self._policy.compute_delay(attempt)
        self._logger.debug(
            "Computed retry delay for '%s': %.2f seconds (attempt %d).",
            task.title,
            delay,
            task.retry_count,
        )
        return delay

    def wait(self, task: OrchestratedTask) -> None:
        """Block the current thread for the appropriate backoff delay.

        This is intentionally synchronous; the scheduler calls it inside
        a worker thread so it does not block the main thread.

        Args:
            task: The task about to be retried.
        """
        delay = self.compute_delay(task)
        if delay > 0:
            self._logger.debug("Sleeping %.2f s before retrying '%s'.", delay, task.title)
            time.sleep(delay)
