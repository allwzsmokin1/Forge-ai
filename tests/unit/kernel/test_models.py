"""Unit tests for forge.kernel.models."""


from forge.kernel.models import Mission, MissionStatus, TaskRecord


class TestMissionStatus:
    def test_values(self):
        assert MissionStatus.CREATED.value == "created"
        assert MissionStatus.RUNNING.value == "running"
        assert MissionStatus.COMPLETED.value == "completed"
        assert MissionStatus.FAILED.value == "failed"

    def test_is_str_subclass(self):
        # MissionStatus inherits str so it serialises naturally
        assert isinstance(MissionStatus.COMPLETED, str)


class TestTaskRecord:
    def test_succeeded_true_on_zero_exit(self):
        t = TaskRecord(command="echo hi", stdout="hi", stderr="", exit_code=0, duration_ms=1.5)
        assert t.succeeded is True

    def test_succeeded_false_on_nonzero_exit(self):
        t = TaskRecord(command="false", stdout="", stderr="err", exit_code=1, duration_ms=2.0)
        assert t.succeeded is False

    def test_to_dict_keys(self):
        t = TaskRecord(command="ls", stdout="a\nb", stderr="", exit_code=0, duration_ms=3.0)
        d = t.to_dict()
        assert set(d) == {"command", "stdout", "stderr", "exit_code", "duration_ms"}

    def test_to_dict_values(self):
        t = TaskRecord(command="ls", stdout="a", stderr="e", exit_code=2, duration_ms=5.5)
        d = t.to_dict()
        assert d["command"] == "ls"
        assert d["stdout"] == "a"
        assert d["stderr"] == "e"
        assert d["exit_code"] == 2
        assert d["duration_ms"] == 5.5


class TestMission:
    def test_default_status_is_created(self):
        m = Mission(goal="echo hi")
        assert m.status == MissionStatus.CREATED

    def test_mission_id_is_assigned(self):
        m = Mission(goal="echo hi")
        assert m.mission_id
        assert len(m.mission_id) == 36  # UUID4 string length

    def test_two_missions_have_different_ids(self):
        m1 = Mission(goal="echo 1")
        m2 = Mission(goal="echo 2")
        assert m1.mission_id != m2.mission_id

    def test_created_at_is_set(self):
        m = Mission(goal="echo hi")
        assert m.created_at  # non-empty ISO timestamp

    def test_to_dict_structure(self):
        m = Mission(goal="echo hi")
        d = m.to_dict()
        assert set(d) == {
            "mission_id",
            "goal",
            "status",
            "created_at",
            "finished_at",
            "task",
            "error",
        }

    def test_to_dict_includes_task_when_present(self):
        m = Mission(goal="ls")
        m.task = TaskRecord(command="ls", stdout="a", stderr="", exit_code=0, duration_ms=1.0)
        d = m.to_dict()
        assert d["task"] is not None
        assert d["task"]["command"] == "ls"

    def test_to_dict_task_is_none_when_absent(self):
        m = Mission(goal="ls")
        assert m.to_dict()["task"] is None

    def test_status_is_mutable(self):
        m = Mission(goal="echo hi")
        m.status = MissionStatus.RUNNING
        assert m.status == MissionStatus.RUNNING
