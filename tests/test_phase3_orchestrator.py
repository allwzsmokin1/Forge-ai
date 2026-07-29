"""Tests for the Phase 3 orchestrator workflow."""

from __future__ import annotations

from forge.config import Settings
from forge.orchestrator import OrchestratorAgent


def test_orchestrator_runs_dependency_aware_goal(tmp_path) -> None:
    orchestrator = OrchestratorAgent(
        memory_path=str(tmp_path / "memory.json"),
        config=Settings(max_parallel_tasks=2, default_task_retries=1),
    )

    report = orchestrator.run("implement scheduler and review scheduler and test scheduler and document scheduler")

    assert report.success is True
    assert len(report.task_results) == 4
    statuses = {result.task.task_type: result.status for result in report.task_results}
    assert statuses["code"] == "completed"
    assert statuses["review"] == "completed"
    assert statuses["test"] == "completed"
    assert statuses["documentation"] == "completed"
    review_task = next(result.task for result in report.task_results if result.task.task_type == "review")
    assert report.dependency_map[review_task.task_id]


def test_orchestrator_persists_task_history(tmp_path) -> None:
    memory_path = tmp_path / "memory.json"
    orchestrator = OrchestratorAgent(
        memory_path=str(memory_path),
        config=Settings(max_parallel_tasks=2, default_task_retries=1),
    )

    orchestrator.run("implement planner and commit planner")

    reloaded = OrchestratorAgent(
        memory_path=str(memory_path),
        config=Settings(max_parallel_tasks=2, default_task_retries=1),
    )
    context = reloaded._memory_manager.get_context("planner")

    assert len(reloaded._memory_manager.memory.task_history) >= 2
    assert any(record.status == "completed" for record in context["tasks"])
