"""Tests for extended project memory."""

from forge.memory import MemoryManager
from forge.tasks import Task, TaskState, TaskStatus


def test_memory_persists_context_artifacts(tmp_path) -> None:
    memory_path = tmp_path / "memory.json"
    manager = MemoryManager(project_name="ForgeAI", memory_path=str(memory_path))
    task = Task(
        title="Implement orchestration",
        description="Build orchestrator",
        priority=1,
        order=1,
        task_type="code",
        task_id="task-1",
    )
    state = TaskState(
        task=task,
        status=TaskStatus.COMPLETED,
        attempts=1,
        assigned_agent="CoderAgent",
        result="done",
    )

    manager.record_task_state(state)
    manager.add_file_metadata("README.md", "Updated orchestration docs", tags=["documentation"])
    manager.add_agent_decision(
        agent_name="ReviewerAgent",
        task_id="task-1",
        decision="Approved implementation.",
        rationale="Dependency graph looked correct.",
    )
    manager.add_summary("Execution", "Orchestrator completed successfully.", categories=["run"])
    manager.save()

    reloaded = MemoryManager(project_name="ForgeAI", memory_path=str(memory_path))
    reloaded.load()
    context = reloaded.retrieve_context("orchestrat")

    assert reloaded.memory.file_metadata["README.md"].summary == "Updated orchestration docs"
    assert reloaded.memory.agent_decisions[0].decision == "Approved implementation."
    assert reloaded.memory.summaries[0].title == "Execution"
    assert context["tasks"][0].task_id == "task-1"
    assert context["summaries"][0].title == "Execution"
