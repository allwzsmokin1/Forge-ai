"""Data models for the Phase 3 orchestration framework.

Defines task state, dependency-aware tasks, and retry policy configuration
used by the OrchestratorAgent, DAG, and Scheduler components.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskStatus(str, Enum):
    """Lifecycle states for an orchestrated task."""

    QUEUED = "queued"
    RUNNING = "running"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class RetryPolicy:
    """Configuration for retrying failed tasks.

    Attributes:
        max_retries: Maximum number of retry attempts (0 = no retries).
        delay_seconds: Base delay in seconds before the first retry.
        backoff_factor: Multiplier applied to the delay for each subsequent retry.
    """

    max_retries: int = 3
    delay_seconds: float = 1.0
    backoff_factor: float = 2.0

    def compute_delay(self, attempt: int) -> float:
        """Return the wait time in seconds before the given retry attempt.

        Args:
            attempt: Zero-based retry attempt index.

        Returns:
            The computed delay in seconds.
        """
        return self.delay_seconds * (self.backoff_factor ** attempt)


@dataclass
class OrchestratedTask:
    """A task that participates in a dependency-aware execution graph.

    Attributes:
        id: Unique identifier for the task.
        title: Short human-readable label.
        description: Full description of the work to perform.
        priority: Scheduling priority (lower numbers run first).
        dependencies: IDs of tasks that must complete before this task starts.
        status: Current lifecycle state.
        retry_count: Number of times the task has been retried.
        result: Output produced by the executing agent, if available.
        error: Error message from the most recent failure, if any.
        assigned_agent: Name of the agent selected to run the task.
        metadata: Arbitrary additional context for the task.
    """

    title: str
    description: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    priority: int = 3
    dependencies: list[str] = field(default_factory=list)
    status: TaskStatus = field(default=TaskStatus.QUEUED)
    retry_count: int = 0
    result: Any | None = None
    error: str | None = None
    assigned_agent: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_ready(self, completed_ids: set[str]) -> bool:
        """Return True when all dependencies are satisfied.

        Args:
            completed_ids: Set of task IDs that have completed successfully.
        """
        return all(dep in completed_ids for dep in self.dependencies)

    def mark_running(self) -> None:
        """Transition the task to the RUNNING state."""
        self.status = TaskStatus.RUNNING

    def mark_completed(self, result: Any = None) -> None:
        """Transition the task to the COMPLETED state and store the result."""
        self.status = TaskStatus.COMPLETED
        self.result = result

    def mark_failed(self, error: str) -> None:
        """Transition the task to the FAILED state and record the error."""
        self.status = TaskStatus.FAILED
        self.error = error

    def mark_blocked(self) -> None:
        """Transition the task to the BLOCKED state (waiting for dependencies)."""
        self.status = TaskStatus.BLOCKED


@dataclass
class ExecutionSummary:
    """Summary produced at the end of an orchestrated run.

    Attributes:
        goal: The original user goal.
        total: Total number of tasks.
        completed: Number of successfully completed tasks.
        failed: Number of tasks that ultimately failed.
        skipped: Number of tasks that were never run.
        task_results: Full list of all orchestrated tasks after execution.
        success: True when every task completed without error.
    """

    goal: str
    total: int
    completed: int
    failed: int
    skipped: int
    task_results: list[OrchestratedTask] = field(default_factory=list)
    success: bool = False
