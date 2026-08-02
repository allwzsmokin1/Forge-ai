"""MissionDirector — the single kernel component in the MVP.

Responsibilities
----------------
1. **Create** a Mission from a developer-supplied goal string.
2. **Run** the mission by delegating execution to the injected
   :class:`~forge.kernel.execution_provider.ExecutionProvider`.
3. **Complete or fail** the mission and persist a record via
   :class:`~forge.kernel.mission_log.MissionLog`.

The Mission Director contains no AI, routing, context management, or memory
logic. Those are Version 2+ concerns (see ``ARCHITECTURE.md``).
"""

from __future__ import annotations

from datetime import UTC, datetime

from .execution_provider import ExecutionProvider
from .mission_log import MissionLog
from .models import Mission, MissionStatus, TaskRecord
from .shell_provider import ShellExecutionProvider


class MissionDirector:
    """Orchestrate a single mission from creation through completion.

    Args:
        provider:  The :class:`ExecutionProvider` to use for execution.
            Defaults to :class:`~forge.kernel.shell_provider.ShellExecutionProvider`.
        log:       The :class:`MissionLog` to persist finished missions.
            Defaults to ``MissionLog()`` (writes to ``.forge/missions.json``).
    """

    def __init__(
        self,
        provider: ExecutionProvider | None = None,
        log: MissionLog | None = None,
    ) -> None:
        self._provider: ExecutionProvider = provider or ShellExecutionProvider()
        self._log: MissionLog = log or MissionLog()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, goal: str) -> Mission:
        """Create, execute, and record a mission for *goal*.

        The mission lifecycle is:
        ``CREATED → RUNNING → COMPLETED | FAILED``

        The finished mission is appended to the mission log regardless of
        whether execution succeeded or failed.

        Args:
            goal: The shell command (or goal string) submitted by the developer.

        Returns:
            The completed or failed :class:`Mission`.
        """
        mission = self._create(goal)
        mission = self._execute(mission)
        self._log.append(mission)
        return mission

    # ------------------------------------------------------------------
    # Internal lifecycle steps
    # ------------------------------------------------------------------

    def _create(self, goal: str) -> Mission:
        """Instantiate a new Mission in CREATED state."""
        return Mission(goal=goal, status=MissionStatus.CREATED)

    def _execute(self, mission: Mission) -> Mission:
        """Advance *mission* from CREATED → RUNNING → COMPLETED | FAILED."""
        mission.status = MissionStatus.RUNNING

        try:
            result = self._provider.execute(mission.goal)
        except Exception as exc:  # noqa: BLE001 — provider may raise any exception type
            mission.status = MissionStatus.FAILED
            mission.error = str(exc)
            mission.finished_at = datetime.now(UTC).isoformat()
            return mission

        task = TaskRecord(
            command=mission.goal,
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.exit_code,
            duration_ms=result.duration_ms,
        )
        mission.task = task

        if result.succeeded:
            mission.status = MissionStatus.COMPLETED
        else:
            mission.status = MissionStatus.FAILED
            mission.error = result.stderr or f"Command exited with code {result.exit_code}"

        mission.finished_at = datetime.now(UTC).isoformat()
        return mission
