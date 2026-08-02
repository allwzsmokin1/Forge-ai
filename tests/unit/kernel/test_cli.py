"""Unit tests for the `orchestrai run` CLI command."""

import json

from typer.testing import CliRunner

from forge.cli import app

runner = CliRunner()


class TestRunCommand:
    def test_run_echo_exits_zero(self, tmp_path):
        result = runner.invoke(app, ["run", "echo hello", "--log-dir", str(tmp_path)])
        assert result.exit_code == 0, result.output

    def test_run_echo_output_contains_completed(self, tmp_path):
        result = runner.invoke(app, ["run", "echo hello", "--log-dir", str(tmp_path)])
        assert "COMPLETED" in result.output

    def test_run_echo_output_shows_stdout(self, tmp_path):
        result = runner.invoke(app, ["run", "echo hello", "--log-dir", str(tmp_path)])
        assert "hello" in result.output

    def test_run_creates_json_log(self, tmp_path):
        runner.invoke(app, ["run", "echo hello", "--log-dir", str(tmp_path)])
        log_file = tmp_path / "missions.json"
        assert log_file.exists()

    def test_json_log_has_one_record(self, tmp_path):
        runner.invoke(app, ["run", "echo hello", "--log-dir", str(tmp_path)])
        records = json.loads((tmp_path / "missions.json").read_text())
        assert len(records) == 1

    def test_json_log_record_goal(self, tmp_path):
        runner.invoke(app, ["run", "echo hello", "--log-dir", str(tmp_path)])
        record = json.loads((tmp_path / "missions.json").read_text())[0]
        assert record["goal"] == "echo hello"

    def test_json_log_record_status_completed(self, tmp_path):
        runner.invoke(app, ["run", "echo hello", "--log-dir", str(tmp_path)])
        record = json.loads((tmp_path / "missions.json").read_text())[0]
        assert record["status"] == "completed"

    def test_json_log_record_has_task(self, tmp_path):
        runner.invoke(app, ["run", "echo hello", "--log-dir", str(tmp_path)])
        record = json.loads((tmp_path / "missions.json").read_text())[0]
        assert record["task"] is not None
        assert record["task"]["exit_code"] == 0

    def test_run_failing_command_exits_nonzero(self, tmp_path):
        result = runner.invoke(app, ["run", "false", "--log-dir", str(tmp_path)])
        assert result.exit_code != 0

    def test_run_failing_command_shows_failed(self, tmp_path):
        result = runner.invoke(app, ["run", "false", "--log-dir", str(tmp_path)])
        assert "FAILED" in result.output

    def test_second_run_appends_to_log(self, tmp_path):
        runner.invoke(app, ["run", "echo first", "--log-dir", str(tmp_path)])
        runner.invoke(app, ["run", "echo second", "--log-dir", str(tmp_path)])
        records = json.loads((tmp_path / "missions.json").read_text())
        assert len(records) == 2

    def test_run_shows_mission_id(self, tmp_path):
        result = runner.invoke(app, ["run", "echo hi", "--log-dir", str(tmp_path)])
        assert "Mission ID" in result.output

    def test_run_shows_log_path(self, tmp_path):
        result = runner.invoke(app, ["run", "echo hi", "--log-dir", str(tmp_path)])
        assert "missions.json" in result.output


class TestHistoryCommand:
    def test_history_empty_when_no_log(self, tmp_path):
        result = runner.invoke(app, ["history", "--log-dir", str(tmp_path)])
        assert result.exit_code == 0
        assert "No missions" in result.output

    def test_history_shows_completed_goal(self, tmp_path):
        runner.invoke(app, ["run", "echo history_test", "--log-dir", str(tmp_path)])
        result = runner.invoke(app, ["history", "--log-dir", str(tmp_path)])
        assert "echo history_test" in result.output
