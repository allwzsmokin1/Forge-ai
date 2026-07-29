"""Orchestrator for coordinating Forge-AI agents.

The orchestration layer is intentionally registry-driven so additional agents can
be registered later without changing orchestrator control flow. The design uses
small dataclasses for structured results and dependency injection through the
agent registry.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from .agents import BaseAgent, CoderAgent, PlannerAgent, ResearchAgent, ReviewerAgent, Task
from .logger import logger
from .memory import MemoryManager
from .runtime import ToolRuntimeManager, get_default_runtime


@dataclass(frozen=True)
class TaskResult:
    """Details about a single task execution."""

    task: Task
    agent_name: str
    status: str
    result: Any = None
    error: str | None = None


@dataclass(frozen=True)
class ExecutionReport:
    """Summary of an orchestration run."""

    goal: str
    task_results: list[TaskResult] = field(default_factory=list)
    success: bool = True


class Orchestrator:
    """Coordinate multiple agents for a single user goal.

    The orchestrator accepts a goal, asks the planner to decompose it into tasks,
    and then dispatches each task to the most appropriate registered agent. The
    dispatch decision is based on keyword matching and a simple rule map that
    can be extended over time.
    """

    def __init__(
        self,
        logger_instance: logging.Logger | None = None,
        memory_manager: MemoryManager | None = None,
        runtime: ToolRuntimeManager | None = None,
        project_name: str = "ForgeAI",
        memory_path: str | None = None,
    ) -> None:
        self._logger = logger_instance or logger
        self._agents: list[tuple[tuple[str, ...], BaseAgent]] = []
        self._runtime = runtime or get_default_runtime()
        self._memory_manager = (
            memory_manager
            if memory_manager is not None
            else MemoryManager(project_name=project_name, memory_path=memory_path)
        )
        self._memory_manager.load()
        self._register_builtin_agents()

    def _register_builtin_agents(self) -> None:
        """Register the built-in agents with default keyword matching."""
        self.register_agent(
            PlannerAgent(runtime=self._runtime), keywords=("plan", "task", "goal", "feature")
        )
        self.register_agent(
            CoderAgent(runtime=self._runtime), keywords=("code", "coding", "implement", "write")
        )
        self.register_agent(
            ReviewerAgent(runtime=self._runtime), keywords=("review", "bug", "quality")
        )
        self.register_agent(
            ResearchAgent(runtime=self._runtime), keywords=("research", "docs", "documentation")
        )

    def register_agent(self, agent: BaseAgent, keywords: Sequence[str]) -> None:
        """Register an agent with one or more keywords for dispatching.

        Args:
            agent: Agent implementation to register.
            keywords: Keywords used to select this agent for a task.
        """
        normalized_keywords = tuple(keyword.lower() for keyword in keywords)
        self._agents.append((normalized_keywords, agent))
        self._logger.info("Registered agent %s with keywords %s", agent.name, normalized_keywords)

    def run(self, goal: str) -> ExecutionReport:
        """Execute the full workflow for a single user goal.

        Args:
            goal: The raw user request.

        Returns:
            An execution report containing all task results.
        """
        self._logger.info("Starting orchestration for goal: %s", goal)
        planner = self._resolve_agent_for_task("plan")
        if planner is None:
            raise RuntimeError("No planner agent registered")

        tasks = planner.run(goal)
        if not isinstance(tasks, list):
            tasks = [tasks]

        self._memory_manager.set_goal_summary(goal)
        self._memory_manager.memory.conversation.goal = goal

        task_results: list[TaskResult] = []
        try:
            for task in tasks:
                task_result = self.execute_task(task)
                task_results.append(task_result)

            success = all(result.status == "completed" for result in task_results)
            report = ExecutionReport(goal=goal, task_results=task_results, success=success)
            self._logger.info("Completed orchestration with success=%s", success)
            return report
        finally:
            self._memory_manager.save()

    def execute_task(self, task: Task) -> TaskResult:
        """Execute a single task using the best matching registered agent.

        Args:
            task: The task to execute.

        Returns:
            A TaskResult with status and optional error information.
        """
        description = f"{task.title} {task.description}".strip().lower()
        agent = self._select_agent(description)
        if agent is None:
            self._logger.warning("No agent registered for task %s", task.title)
            return TaskResult(
                task=task, agent_name="None", status="failed", error="No agent registered"
            )

        self._logger.info("Executing task %s with %s", task.title, agent.name)
        prompt = task.description if task.description else task.title
        try:
            result = agent.run(prompt, task=task)
            task_result = TaskResult(
                task=task, agent_name=agent.name, status="completed", result=result
            )
            self._memory_manager.add_entry(
                task_title=task.title,
                task_description=task.description,
                agent_name=agent.name,
                status=task_result.status,
                result=result,
                error=None,
                categories=[agent.name.lower()],
            )
            self._memory_manager.save()
            return task_result
        except Exception as exc:  # pragma: no cover - defensive branch
            self._logger.exception("Task %s failed", task.title)
            task_result = TaskResult(
                task=task, agent_name=agent.name, status="failed", error=str(exc)
            )
            self._memory_manager.add_entry(
                task_title=task.title,
                task_description=task.description,
                agent_name=agent.name,
                status=task_result.status,
                result=None,
                error=str(exc),
                categories=[agent.name.lower()],
            )
            self._memory_manager.save()
            return task_result

    def _select_agent(self, description: str) -> BaseAgent | None:
        """Choose the best-fitting agent for a task description.

        Matching is based on the longest keyword match. When multiple agents have
        the same score, a later registration wins so custom agents can override
        built-in defaults when they are explicitly registered.
        """
        lowered = description.lower()
        best_match: tuple[int, int, BaseAgent] | None = None
        for index, (keywords, agent) in enumerate(self._agents):
            if any(keyword in lowered for keyword in keywords):
                score = max(len(keyword) for keyword in keywords if keyword in lowered)
                if (
                    best_match is None
                    or score > best_match[0]
                    or (score == best_match[0] and index > best_match[1])
                ):
                    best_match = (score, index, agent)
        return None if best_match is None else best_match[2]

    def _resolve_agent_for_task(self, task_type: str) -> BaseAgent | None:
        """Resolve a specific built-in agent by task type."""
        lowered = task_type.lower()
        for keywords, agent in self._agents:
            if any(keyword == lowered for keyword in keywords):
                return agent
        return None
