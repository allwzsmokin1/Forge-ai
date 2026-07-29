"""Tests for the extended ProjectMemoryService."""

from __future__ import annotations

from pathlib import Path

from forge.memory.project_memory_service import (
    AgentDecision,
    FileMetadata,
    OrchestrationSummary,
    ProjectMemoryService,
)


def _make_service(tmp_path: Path) -> ProjectMemoryService:
    memory_path = str(tmp_path / "memory.json")
    return ProjectMemoryService(
        project_name="TestProject",
        extended_path=memory_path,
    )


class TestFileMetadata:
    def test_record_file_returns_metadata(self, tmp_path: Path) -> None:
        service = _make_service(tmp_path)
        meta = service.record_file("src/parser.py", language="python", agent_name="CoderAgent")
        assert isinstance(meta, FileMetadata)
        assert meta.path == "src/parser.py"
        assert meta.language == "python"
        assert meta.agent_name == "CoderAgent"

    def test_get_file_returns_recorded_metadata(self, tmp_path: Path) -> None:
        service = _make_service(tmp_path)
        service.record_file("src/utils.py", language="python")
        result = service.get_file("src/utils.py")
        assert result is not None
        assert result.path == "src/utils.py"

    def test_get_file_returns_none_for_unknown_path(self, tmp_path: Path) -> None:
        service = _make_service(tmp_path)
        assert service.get_file("nonexistent.py") is None

    def test_list_files_returns_all_tracked(self, tmp_path: Path) -> None:
        service = _make_service(tmp_path)
        service.record_file("a.py")
        service.record_file("b.py")
        paths = {f.path for f in service.list_files()}
        assert {"a.py", "b.py"}.issubset(paths)

    def test_record_file_updates_existing_entry(self, tmp_path: Path) -> None:
        service = _make_service(tmp_path)
        service.record_file("a.py", language="python")
        service.record_file("a.py", language="python", summary="Updated")
        assert service.get_file("a.py").summary == "Updated"
        assert len(service.list_files()) == 1


class TestAgentDecisions:
    def test_record_decision_returns_decision(self, tmp_path: Path) -> None:
        service = _make_service(tmp_path)
        decision = service.record_decision(
            "CoderAgent", "task-1", "Chose mock LLM", "No real LLM available"
        )
        assert isinstance(decision, AgentDecision)
        assert decision.decision == "Chose mock LLM"

    def test_get_decisions_for_task_filters_correctly(self, tmp_path: Path) -> None:
        service = _make_service(tmp_path)
        service.record_decision("A", "task-1", "Decision A")
        service.record_decision("B", "task-2", "Decision B")
        results = service.get_decisions_for_task("task-1")
        assert len(results) == 1
        assert results[0].decision == "Decision A"

    def test_get_decisions_for_unknown_task_returns_empty(self, tmp_path: Path) -> None:
        service = _make_service(tmp_path)
        assert service.get_decisions_for_task("no-such-task") == []


class TestOrchestrationSummaries:
    def test_record_summary_returns_summary(self, tmp_path: Path) -> None:
        service = _make_service(tmp_path)
        summary = service.record_orchestration_summary(
            goal="build parser",
            total=5,
            completed=5,
            failed=0,
            skipped=0,
            success=True,
        )
        assert isinstance(summary, OrchestrationSummary)
        assert summary.goal == "build parser"
        assert summary.success is True

    def test_get_orchestration_history_returns_all(self, tmp_path: Path) -> None:
        service = _make_service(tmp_path)
        service.record_orchestration_summary("g1", 1, 1, 0, 0, True)
        service.record_orchestration_summary("g2", 2, 2, 0, 0, True)
        history = service.get_orchestration_history()
        assert len(history) == 2


class TestContextRetrieval:
    def test_search_context_returns_matching_files(self, tmp_path: Path) -> None:
        service = _make_service(tmp_path)
        service.record_file("src/parser.py", language="python", summary="Parses CSV")
        result = service.search_context("parser")
        assert any(f.path == "src/parser.py" for f in result["files"])

    def test_search_context_returns_matching_decisions(self, tmp_path: Path) -> None:
        service = _make_service(tmp_path)
        service.record_decision("A", "t1", "Used mock LLM for parsing tasks")
        result = service.search_context("parsing")
        assert len(result["decisions"]) == 1

    def test_search_context_all_buckets_returned(self, tmp_path: Path) -> None:
        service = _make_service(tmp_path)
        result = service.search_context("anything")
        assert "memory_entries" in result
        assert "files" in result
        assert "decisions" in result

    def test_search_context_case_insensitive(self, tmp_path: Path) -> None:
        service = _make_service(tmp_path)
        service.record_file("src/CSV_Parser.py", summary="CSV parsing utilities")
        result = service.search_context("csv")
        assert len(result["files"]) >= 1


class TestPersistence:
    def test_save_and_load_roundtrip_files(self, tmp_path: Path) -> None:
        service = _make_service(tmp_path)
        service.record_file("src/app.py", language="python", summary="App entry point")
        service.save()

        service2 = _make_service(tmp_path)
        service2.load()
        assert service2.get_file("src/app.py") is not None
        assert service2.get_file("src/app.py").summary == "App entry point"

    def test_save_and_load_roundtrip_decisions(self, tmp_path: Path) -> None:
        service = _make_service(tmp_path)
        service.record_decision("Agent", "t1", "A decision", "Because it's best")
        service.save()

        service2 = _make_service(tmp_path)
        service2.load()
        assert len(service2.get_decisions_for_task("t1")) == 1

    def test_save_and_load_roundtrip_summaries(self, tmp_path: Path) -> None:
        service = _make_service(tmp_path)
        service.record_orchestration_summary("g1", 3, 3, 0, 0, True)
        service.save()

        service2 = _make_service(tmp_path)
        service2.load()
        assert len(service2.get_orchestration_history()) == 1

    def test_load_without_file_does_not_raise(self, tmp_path: Path) -> None:
        service = _make_service(tmp_path)
        # No save; just load
        service.load()  # should not raise


class TestProjectSummary:
    def test_get_project_summary_includes_extra_counts(self, tmp_path: Path) -> None:
        service = _make_service(tmp_path)
        service.record_file("f.py")
        service.record_decision("A", "t1", "D")
        summary = service.get_project_summary()
        assert "Tracked files: 1" in summary
        assert "Agent decisions: 1" in summary
