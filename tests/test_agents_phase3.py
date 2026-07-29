"""Tests for Phase 3 specialized agents."""

from forge.agents.debugger import DebugAgent
from forge.agents.documentation import DocumentationAgent
from forge.agents.git import GitAgent
from forge.agents.tester import TestAgent


def test_test_agent_returns_pytest_command_and_focus_areas() -> None:
    result = TestAgent().run("Validate orchestrator retry behavior")

    assert result.commands == ["python -m pytest -q"]
    assert "dependency and concurrency behavior" in result.focus_areas
    assert "Exercise retry exhaustion and recovery paths." in result.checks


def test_debug_agent_highlights_timeout_recovery() -> None:
    result = DebugAgent().run("task failed", error="Timeout while waiting on dependency")

    assert any("time" in cause.lower() for cause in result.suspected_causes)
    assert any("decompose" in action.lower() for action in result.recommended_actions)


def test_documentation_agent_recommends_readme() -> None:
    result = DocumentationAgent().run("Document the orchestration system")

    assert "README.md" in result.files_to_update
    assert "Architecture" in result.sections


def test_git_agent_generates_branch_and_commit_guidance() -> None:
    result = GitAgent().run("Prepare git handoff for orchestration framework")

    assert result.branch_name.startswith("forge/")
    assert "Review the final diff." in result.actions
    assert result.commit_message
