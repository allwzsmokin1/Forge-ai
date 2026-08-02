"""Domain models for the OrchestrAI MVP kernel."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


class MissionStatus(str, Enum):
    """Lifecycle states of a Mission."""

    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TaskRecord:
    """Record of a single shell command execution within a Mission.

    Attributes:
        command:     The shell command that was executed.
        stdout:      Captured standard output (stripped).
        stderr:      Captured standard error (stripped).
        exit_code:   Process exit code; 0 indicates success.
        duration_ms: Wall-clock execution time in milliseconds.
    """

    command: str
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: float

    @property
    def succeeded(self) -> bool:
        """Return True when the command exited with code 0."""
        return self.exit_code == 0

    def to_dict(self) -> dict:
        return {
            "command": self.command,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "duration_ms": self.duration_ms,
        }


@dataclass
class Mission:
    """Top-level unit of work submitted to the Mission Director.

    Attributes:
        goal:       The raw string goal submitted by the developer.
        mission_id: Stable UUID that identifies this mission across sessions.
        status:     Current lifecycle state.
        created_at: ISO-8601 timestamp of creation in UTC.
        finished_at: ISO-8601 timestamp of completion or failure in UTC.
        task:       The single ``TaskRecord`` produced during execution.
        error:      Human-readable error message when status is FAILED.
    """

    goal: str
    mission_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: MissionStatus = MissionStatus.CREATED
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    finished_at: str | None = None
    task: TaskRecord | None = None
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "mission_id": self.mission_id,
            "goal": self.goal,
            "status": self.status.value,
            "created_at": self.created_at,
            "finished_at": self.finished_at,
            "task": self.task.to_dict() if self.task else None,
            "error": self.error,
        }
