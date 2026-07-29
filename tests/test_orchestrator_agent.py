"""Tests for the OrchestratorAgent."""

from __future__ import annotations

from typing import Any

from forge.agents.base import BaseAgent
from forge.orchestration.models import ExecutionSummary, RetryPolicy, TaskStatus
from forge.orchestration.orchestrator_agent import OrchestratorAgent


class EchoAgent(BaseAgent):
    """Simple stub agent that echoes the prompt."""

    @property
    def name(self) -> str:
        return "EchoAgent"

    @property
    def description(self) -> str:
        return "Echoes the prompt."

    def run(self, prompt: str, **kwargs: Any) -> str:
        return f"echo:{prompt}"


class FailAgent(BaseAgent):
    """Agent that always raises."""

    @property
    def name(self) -> str:
        return "FailAgent"

    @property
    def description(self) -> str:
        return "Always fails."

    def run(self, prompt: str, **kwargs: Any) -> str:
        raise RuntimeError("Intentional failure")


# ---------------------------------------------------------------------------
# Interface and registration
# ---------------------------------------------------------------------------


class TestOrchestratorAgentInterface:
    def test_name(self) -> None:
        assert OrchestratorAgent().name == "OrchestratorAgent"

    def test_description_not_empty(self) -> None:
        assert OrchestratorAgent().description

    def test_register_and_select_agent(self) -> None:
        orch = OrchestratorAgent()
        agent = EchoAgent()
        orch.register_agent(agent, keywords=["echo", "print"])
        selected = orch.select_agent("please echo this text")
        assert selected is agent

    def test_select_agent_returns_none_for_no_match(self) -> None:
        orch = OrchestratorAgent()
        orch.register_agent(EchoAgent(), keywords=["echo"])
        assert orch.select_agent("completely unrelated task") is None

    def test_later_registration_wins_on_tie(self) -> None:
        orch = OrchestratorAgent()
        a1 = EchoAgent()
        a2 = EchoAgent()
        orch.register_agent(a1, keywords=["test"])
        orch.register_agent(a2, keywords=["test"])
        # Both have the same keyword length; later registration should win
        selected = orch.select_agent("run a test now")
        assert selected is a2

    def test_longest_keyword_match_wins(self) -> None:
        orch = OrchestratorAgent()

        class ShortAgent(BaseAgent):
            @property
            def name(self) -> str:
                return "Short"

            @property
            def description(self) -> str:
                return ""

            def run(self, prompt: str, **kwargs: Any) -> str:
                return ""

        class LongAgent(BaseAgent):
            @property
            def name(self) -> str:
                return "Long"

            @property
            def description(self) -> str:
                return ""

            def run(self, prompt: str, **kwargs: Any) -> str:
                return ""

        orch.register_agent(ShortAgent(), keywords=["run"])
        orch.register_agent(LongAgent(), keywords=["run tests"])
        selected = orch.select_agent("please run tests for all modules")
        assert selected.name == "Long"


# ---------------------------------------------------------------------------
# Goal decomposition
# ---------------------------------------------------------------------------


class TestOrchestratorDecomposition:
    def test_empty_goal_returns_no_tasks(self) -> None:
        orch = OrchestratorAgent()
        assert orch.decompose_goal("") == []

    def test_single_segment_returns_one_task(self) -> None:
        orch = OrchestratorAgent()
        tasks = orch.decompose_goal("implement a parser")
        assert len(tasks) == 1
        assert tasks[0].title == "implement a parser"

    def test_semicolon_splits_into_multiple_tasks(self) -> None:
        orch = OrchestratorAgent()
        tasks = orch.decompose_goal("implement parser; test parser")
        assert len(tasks) == 2

    def test_and_then_splits_into_multiple_tasks(self) -> None:
        orch = OrchestratorAgent()
        tasks = orch.decompose_goal("write code and then review code")
        assert len(tasks) == 2

    def test_urgent_keyword_sets_priority_one(self) -> None:
        orch = OrchestratorAgent()
        tasks = orch.decompose_goal("urgent: fix production crash")
        assert tasks[0].priority == 1

    def test_research_keyword_sets_priority_two(self) -> None:
        orch = OrchestratorAgent()
        tasks = orch.decompose_goal("research best practices for caching")
        assert tasks[0].priority == 2

    def test_test_task_depends_on_first_task(self) -> None:
        orch = OrchestratorAgent()
        tasks = orch.decompose_goal("implement feature; test feature")
        test_task = next(t for t in tasks if "test" in t.title.lower())
        impl_task = next(t for t in tasks if "implement" in t.title.lower())
        assert impl_task.id in test_task.dependencies


# ---------------------------------------------------------------------------
# Full run
# ---------------------------------------------------------------------------


class TestOrchestratorAgentRun:
    def _orch_with_echo(self) -> OrchestratorAgent:
        orch = OrchestratorAgent(
            max_workers=2,
            retry_policy=RetryPolicy(max_retries=0, delay_seconds=0.0),
        )
        orch.register_agent(EchoAgent(), keywords=["implement", "write", "test", "review"])
        return orch

    def test_run_returns_execution_summary(self) -> None:
        orch = self._orch_with_echo()
        result = orch.run("implement a feature")
        assert isinstance(result, ExecutionSummary)

    def test_run_single_task_succeeds(self) -> None:
        orch = self._orch_with_echo()
        result = orch.run("implement a feature")
        assert result.completed == 1
        assert result.failed == 0
        assert result.success is True

    def test_run_two_tasks_both_complete(self) -> None:
        orch = self._orch_with_echo()
        result = orch.run("implement feature; test feature")
        assert result.completed == 2
        assert result.success is True

    def test_run_empty_goal_returns_zero_tasks(self) -> None:
        orch = self._orch_with_echo()
        result = orch.run("")
        assert result.total == 0
        assert result.success is True

    def test_run_no_agent_causes_task_failure(self) -> None:
        orch = OrchestratorAgent(
            max_workers=1,
            retry_policy=RetryPolicy(max_retries=0, delay_seconds=0.0),
        )
        # No agents registered → task should fail
        result = orch.run("implement a feature")
        assert result.failed == 1
        assert result.success is False

    def test_run_assigns_agent_name_to_task(self) -> None:
        orch = self._orch_with_echo()
        result = orch.run("implement a feature")
        completed = [t for t in result.task_results if t.status == TaskStatus.COMPLETED]
        assert all(t.assigned_agent == "EchoAgent" for t in completed)

    def test_run_stores_task_result(self) -> None:
        orch = self._orch_with_echo()
        result = orch.run("implement a feature")
        completed = [t for t in result.task_results if t.status == TaskStatus.COMPLETED]
        assert completed[0].result.startswith("echo:")

    def test_run_with_failing_agent_marks_failed(self) -> None:
        orch = OrchestratorAgent(
            max_workers=1,
            retry_policy=RetryPolicy(max_retries=0, delay_seconds=0.0),
        )
        orch.register_agent(FailAgent(), keywords=["implement"])
        result = orch.run("implement something")
        assert result.failed == 1
        assert result.success is False
