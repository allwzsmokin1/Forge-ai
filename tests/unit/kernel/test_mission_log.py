"""Unit tests for forge.kernel.mission_log.MissionLog."""

import json

import pytest

from forge.kernel.mission_log import MissionLog
from forge.kernel.models import Mission, MissionStatus, TaskRecord


@pytest.fixture()
def tmp_log(tmp_path):
    """Return a MissionLog backed by a temp directory."""
    return MissionLog(log_dir=tmp_path)


def _make_completed_mission(goal: str = "echo hi") -> Mission:
    m = Mission(goal=goal)
    m.status = MissionStatus.COMPLETED
    m.task = TaskRecord(
        command=goal, stdout="hi", stderr="", exit_code=0, duration_ms=1.5
    )
    m.finished_at = "2026-01-01T00:00:00+00:00"
    return m


class TestMissionLogPath:
    def test_default_log_dir_is_dotforge(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        log = MissionLog()
        assert log.log_path == tmp_path / ".forge" / "missions.json"

    def test_custom_log_dir(self, tmp_path):
        log = MissionLog(log_dir=tmp_path / "custom")
        assert log.log_path == tmp_path / "custom" / "missions.json"


class TestMissionLogAppend:
    def test_creates_log_file_on_first_append(self, tmp_log, tmp_path):
        assert not tmp_log.log_path.exists()
        tmp_log.append(_make_completed_mission())
        assert tmp_log.log_path.exists()

    def test_appended_record_is_retrievable(self, tmp_log):
        m = _make_completed_mission("echo test")
        tmp_log.append(m)
        records = tmp_log.read_all()
        assert len(records) == 1
        assert records[0]["goal"] == "echo test"

    def test_multiple_appends_accumulate(self, tmp_log):
        for i in range(3):
            tmp_log.append(_make_completed_mission(f"echo {i}"))
        records = tmp_log.read_all()
        assert len(records) == 3

    def test_record_contains_expected_fields(self, tmp_log):
        m = _make_completed_mission()
        tmp_log.append(m)
        record = tmp_log.read_all()[0]
        assert "mission_id" in record
        assert "goal" in record
        assert "status" in record
        assert "created_at" in record
        assert "finished_at" in record
        assert "task" in record
        assert "error" in record

    def test_task_fields_persisted(self, tmp_log):
        m = _make_completed_mission("echo hi")
        tmp_log.append(m)
        task = tmp_log.read_all()[0]["task"]
        assert task["command"] == "echo hi"
        assert task["stdout"] == "hi"
        assert task["exit_code"] == 0

    def test_creates_parent_directories(self, tmp_path):
        deep_dir = tmp_path / "a" / "b" / "c"
        log = MissionLog(log_dir=deep_dir)
        log.append(_make_completed_mission())
        assert log.log_path.exists()

    def test_file_is_valid_json(self, tmp_log):
        tmp_log.append(_make_completed_mission())
        raw = tmp_log.log_path.read_text(encoding="utf-8")
        data = json.loads(raw)
        assert isinstance(data, list)
        assert len(data) == 1


class TestMissionLogReadAll:
    def test_returns_empty_list_when_no_file(self, tmp_log):
        assert tmp_log.read_all() == []

    def test_returns_empty_list_on_corrupt_file(self, tmp_path):
        log = MissionLog(log_dir=tmp_path)
        log.log_path.parent.mkdir(parents=True, exist_ok=True)
        log.log_path.write_text("NOT VALID JSON", encoding="utf-8")
        assert log.read_all() == []

    def test_order_preserved(self, tmp_log):
        goals = ["echo a", "echo b", "echo c"]
        for g in goals:
            tmp_log.append(_make_completed_mission(g))
        records = tmp_log.read_all()
        assert [r["goal"] for r in records] == goals
