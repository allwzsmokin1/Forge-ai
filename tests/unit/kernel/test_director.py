"""Unit tests for forge.kernel.director.MissionDirector."""


from forge.kernel.director import MissionDirector
from forge.kernel.execution_provider import ExecutionProvider, ExecutionResult
from forge.kernel.mission_log import MissionLog
from forge.kernel.models import MissionStatus

# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------


class SuccessProvider(ExecutionProvider):
    """Always returns a successful result."""

    def execute(self, command: str) -> ExecutionResult:
        return ExecutionResult(
            stdout=f"ran: {command}",
            stderr="",
            exit_code=0,
            duration_ms=1.0,
        )


class FailureProvider(ExecutionProvider):
    """Always returns a non-zero exit code."""

    def execute(self, command: str) -> ExecutionResult:
        return ExecutionResult(
            stdout="",
            stderr="something went wrong",
            exit_code=1,
            duration_ms=1.0,
        )


class ExplodingProvider(ExecutionProvider):
    """Raises RuntimeError before executing anything."""

    def execute(self, command: str) -> ExecutionResult:
        raise RuntimeError("provider exploded")


class RecordingLog(MissionLog):
    """MissionLog that records calls without touching disk."""

    def __init__(self):
        self.appended: list = []

    def append(self, mission) -> None:
        self.appended.append(mission)

    def read_all(self) -> list:
        return [m.to_dict() for m in self.appended]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestMissionDirectorRun:
    def _director(self, provider=None, log=None):
        return MissionDirector(
            provider=provider or SuccessProvider(),
            log=log or RecordingLog(),
        )

    # ── Lifecycle ──────────────────────────────────────────────────────
    def test_returns_mission_object(self):
        from forge.kernel.models import Mission

        d = self._director()
        mission = d.run("echo hi")
        assert isinstance(mission, Mission)

    def test_completed_status_on_success(self):
        d = self._director()
        mission = d.run("echo hi")
        assert mission.status == MissionStatus.COMPLETED

    def test_failed_status_on_nonzero_exit(self):
        d = self._director(provider=FailureProvider())
        mission = d.run("false")
        assert mission.status == MissionStatus.FAILED

    def test_failed_status_when_provider_raises(self):
        d = self._director(provider=ExplodingProvider())
        mission = d.run("explode")
        assert mission.status == MissionStatus.FAILED

    def test_error_field_set_on_provider_exception(self):
        d = self._director(provider=ExplodingProvider())
        mission = d.run("explode")
        assert "provider exploded" in mission.error

    def test_finished_at_set_after_run(self):
        d = self._director()
        mission = d.run("echo hi")
        assert mission.finished_at is not None

    # ── Goal propagation ───────────────────────────────────────────────
    def test_goal_stored_on_mission(self):
        d = self._director()
        mission = d.run("echo hello world")
        assert mission.goal == "echo hello world"

    # ── TaskRecord ─────────────────────────────────────────────────────
    def test_task_record_populated_on_success(self):
        d = self._director()
        mission = d.run("echo hi")
        assert mission.task is not None
        assert mission.task.command == "echo hi"

    def test_task_stdout_captured(self):
        d = self._director()
        mission = d.run("echo hi")
        assert mission.task.stdout == "ran: echo hi"

    def test_task_exit_code_captured(self):
        d = self._director()
        mission = d.run("echo hi")
        assert mission.task.exit_code == 0

    def test_task_exit_code_non_zero_on_failure(self):
        d = self._director(provider=FailureProvider())
        mission = d.run("false")
        assert mission.task.exit_code == 1

    # ── Mission log ────────────────────────────────────────────────────
    def test_mission_appended_to_log_on_success(self):
        log = RecordingLog()
        d = self._director(log=log)
        d.run("echo hi")
        assert len(log.appended) == 1

    def test_mission_appended_to_log_on_failure(self):
        log = RecordingLog()
        d = self._director(provider=FailureProvider(), log=log)
        d.run("false")
        assert len(log.appended) == 1

    def test_mission_appended_even_when_provider_raises(self):
        log = RecordingLog()
        d = self._director(provider=ExplodingProvider(), log=log)
        d.run("explode")
        assert len(log.appended) == 1

    def test_multiple_runs_each_appended(self):
        log = RecordingLog()
        d = self._director(log=log)
        d.run("echo a")
        d.run("echo b")
        assert len(log.appended) == 2

    # ── Default provider/log ───────────────────────────────────────────
    def test_default_provider_is_shell(self, tmp_path):
        """MissionDirector with no args uses ShellExecutionProvider."""
        from forge.kernel.director import MissionDirector
        from forge.kernel.mission_log import MissionLog

        log = MissionLog(log_dir=tmp_path)
        d = MissionDirector(log=log)
        mission = d.run("echo integration")
        assert mission.status == MissionStatus.COMPLETED
        assert mission.task.stdout == "integration"
