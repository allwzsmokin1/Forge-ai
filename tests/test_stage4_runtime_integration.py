"""Integration tests for Stage 4 runtime + orchestrator wiring."""

from __future__ import annotations

from pathlib import Path

from forge.config import Settings
from forge.orchestrator import OrchestratorAgent


def test_orchestrator_initializes_runtime_with_builtin_tools(tmp_path: Path) -> None:
    orchestrator = OrchestratorAgent(
        memory_path=str(tmp_path / "memory.json"),
        config=Settings(max_parallel_tasks=2, default_task_retries=1),
    )

    tools = set(orchestrator.runtime.registry.list_tools())

    assert {
        "terminal",
        "filesystem",
        "git",
        "python",
        "docker",
        "search",
        "web",
        "archive",
    }.issubset(tools)


def test_git_agent_uses_runtime_capability(tmp_path: Path) -> None:
    orchestrator = OrchestratorAgent(
        memory_path=str(tmp_path / "memory.json"),
        config=Settings(max_parallel_tasks=2, default_task_retries=1),
    )

    report = orchestrator.run("implement feature and commit changes")
    git_task = next(
        (result for result in report.task_results if result.task.task_type == "git"), None
    )

    assert git_task is not None
    assert git_task.status == "completed"
    assert "Prepare repository changes" in git_task.result.summary
    assert (
        "Current git status" in git_task.result.summary
        or "Working tree is clean" in git_task.result.summary
    )
