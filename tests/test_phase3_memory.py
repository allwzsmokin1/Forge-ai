"""Tests for the extended project memory service."""

from __future__ import annotations

from forge.memory import MemoryManager


def test_memory_manager_persists_extended_context(tmp_path) -> None:
    memory_path = tmp_path / "memory.json"
    manager = MemoryManager(project_name="ForgeAI", memory_path=str(memory_path))

    manager.record_task_dependencies("task-1", ["task-0"])
    manager.record_task_state(
        task_id="task-1",
        title="Implement scheduler",
        description="Build dependency-aware task execution",
        agent_name="CoderAgent",
        status="completed",
        attempt=1,
        dependencies=["task-0"],
        result_summary="scheduler complete",
    )
    manager.record_file_metadata(
        path="/workspace/forge/orchestrator.py",
        summary="Main orchestration entrypoint",
        tags=["orchestration", "scheduler"],
    )
    manager.record_agent_decision(
        agent_name="OrchestratorAgent",
        task_id="task-1",
        decision="selected_agent",
        rationale="Task requires code generation.",
    )
    manager.add_summary("phase3", "autonomous multi-agent orchestration")
    manager.save()

    reloaded = MemoryManager(project_name="ForgeAI", memory_path=str(memory_path))
    reloaded.load()
    context = reloaded.get_context("scheduler")

    assert reloaded.memory.task_dependencies["task-1"] == ["task-0"]
    assert len(reloaded.memory.task_history) == 1
    assert len(reloaded.memory.file_metadata) == 1
    assert len(reloaded.memory.agent_decisions) == 1
    assert reloaded.memory.summaries["phase3"] == "autonomous multi-agent orchestration"
    assert context["tasks"][0].task_id == "task-1"
    assert context["files"][0].path == "/workspace/forge/orchestrator.py"
    assert context["summaries"][0] == "phase3: autonomous multi-agent orchestration"
