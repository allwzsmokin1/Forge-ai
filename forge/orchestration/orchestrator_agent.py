"""OrchestratorAgent — autonomous multi-agent coordination for complex goals.

Decomposes user goals into dependency-aware tasks, schedules them across
specialized agents, retries failures, and returns a structured summary of
the entire run.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any

from ..agents.base import BaseAgent
from .dag import TaskDAG
from .models import ExecutionSummary, OrchestratedTask, RetryPolicy, TaskStatus
from .retry import RetryManager
from .scheduler import Scheduler

logger = logging.getLogger("forge.orchestration.agent")


class OrchestratorAgent(BaseAgent):
    """Autonomous orchestrator that decomposes goals and coordinates agents.

    The OrchestratorAgent acts as a meta-agent: it accepts a high-level goal,
    decomposes it into ``OrchestratedTask`` objects with explicit dependency
    links, dispatches each task to the best-matching registered sub-agent, and
    supervises execution through the ``Scheduler`` with retry support.

    Sub-agents are registered with keyword tuples used for dispatch.  The
    longest keyword match wins; ties break in favour of later registrations.

    Example::

        orchestrator = OrchestratorAgent(max_workers=4)
        orchestrator.register_agent(CoderAgent(), keywords=("code", "implement"))
        orchestrator.register_agent(TestAgent(), keywords=("test",))
        summary = orchestrator.run("Implement and test a CSV parser")
    """

    def __init__(
        self,
        max_workers: int = 4,
        retry_policy: RetryPolicy | None = None,
        logger_instance: logging.Logger | None = None,
    ) -> None:
        self._max_workers = max_workers
        self._retry_manager = RetryManager(retry_policy or RetryPolicy())
        self._logger = logger_instance or logger
        self._agents: list[tuple[tuple[str, ...], BaseAgent]] = []

    # ------------------------------------------------------------------
    # BaseAgent interface
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        return "OrchestratorAgent"

    @property
    def description(self) -> str:
        return (
            "Decomposes complex goals into dependency-aware tasks, schedules "
            "work across specialized sub-agents, retries failures, and "
            "returns a structured execution summary."
        )

    def run(self, prompt: str, **kwargs: Any) -> ExecutionSummary:
        """Orchestrate a full multi-agent workflow for the given goal.

        Args:
            prompt: The high-level user goal.
            **kwargs: Unused; accepted for interface compatibility.

        Returns:
            An ExecutionSummary describing the outcome of every task.
        """
        goal = prompt.strip()
        self._logger.info("OrchestratorAgent starting for goal: %s", goal)

        tasks = self.decompose_goal(goal)
        dag = TaskDAG()
        for task in tasks:
            dag.add_task(task)

        scheduler = Scheduler(
            max_workers=self._max_workers,
            retry_manager=self._retry_manager,
        )
        all_tasks = scheduler.run(dag, execute_fn=self._execute_task)

        completed = sum(1 for t in all_tasks if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in all_tasks if t.status == TaskStatus.FAILED)
        skipped = sum(
            1 for t in all_tasks
            if t.status not in (TaskStatus.COMPLETED, TaskStatus.FAILED)
        )

        summary = ExecutionSummary(
            goal=goal,
            total=len(all_tasks),
            completed=completed,
            failed=failed,
            skipped=skipped,
            task_results=all_tasks,
            success=(failed == 0 and skipped == 0),
        )
        self._logger.info(
            "OrchestratorAgent finished: %d completed, %d failed, %d skipped.",
            completed,
            failed,
            skipped,
        )
        return summary

    # ------------------------------------------------------------------
    # Agent registry
    # ------------------------------------------------------------------

    def register_agent(self, agent: BaseAgent, keywords: Sequence[str]) -> None:
        """Register a sub-agent and associate it with dispatch keywords.

        Args:
            agent: The agent implementation to register.
            keywords: Lower-cased keywords used for task routing.
        """
        normalized = tuple(k.lower() for k in keywords)
        self._agents.append((normalized, agent))
        self._logger.info(
            "Registered agent '%s' with keywords %s.", agent.name, normalized
        )

    def select_agent(self, description: str) -> BaseAgent | None:
        """Pick the best-matching registered agent for a task description.

        Uses the longest keyword match; ties break in favour of later
        registrations so custom agents override built-in defaults.

        Args:
            description: Combined task title and description (lower-cased).

        Returns:
            The matched agent, or None if no agent matches.
        """
        lowered = description.lower()
        best: tuple[int, int, BaseAgent] | None = None
        for idx, (keywords, agent) in enumerate(self._agents):
            matching = [kw for kw in keywords if kw in lowered]
            if matching:
                score = max(len(kw) for kw in matching)
                if best is None or score > best[0] or (score == best[0] and idx > best[1]):
                    best = (score, idx, agent)
        return None if best is None else best[2]

    # ------------------------------------------------------------------
    # Goal decomposition
    # ------------------------------------------------------------------

    def decompose_goal(self, goal: str) -> list[OrchestratedTask]:
        """Break a goal string into a list of OrchestratedTasks.

        The decomposition heuristic splits on common separators and assigns
        ordering and priority based on keyword cues.  Dependencies are added
        when task descriptions reference earlier tasks (e.g. "then test").

        Args:
            goal: The user-facing goal string.

        Returns:
            Ordered list of OrchestratedTask objects.
        """
        if not goal:
            return []

        # Split into raw segments
        segments: list[str] = [goal]
        for sep in (";", " and then ", " then ", " and "):
            if sep in goal:
                segments = [s.strip() for s in goal.split(sep) if s.strip()]
                break

        tasks: list[OrchestratedTask] = []
        for idx, segment in enumerate(segments, start=1):
            lowered = segment.lower()
            if "urgent" in lowered or "critical" in lowered:
                priority = 1
            elif "research" in lowered or "investigate" in lowered:
                priority = 2
            else:
                priority = 3

            # Simple dependency heuristic: non-first tasks depend on the first
            deps: list[str] = []
            if tasks and any(kw in lowered for kw in ("test", "review", "document", "debug")):
                deps = [tasks[0].id]

            task = OrchestratedTask(
                title=segment[:80],
                description=segment,
                priority=priority,
                dependencies=deps,
            )
            tasks.append(task)

        return tasks

    # ------------------------------------------------------------------
    # Task execution
    # ------------------------------------------------------------------

    def _execute_task(self, task: OrchestratedTask) -> Any:
        """Dispatch a single task to the best-matching agent.

        Args:
            task: The task to execute.

        Returns:
            The result produced by the executing agent.

        Raises:
            RuntimeError: If no registered agent matches the task.
        """
        description = f"{task.title} {task.description}".strip()
        agent = self.select_agent(description)

        if agent is None:
            raise RuntimeError(
                f"No agent registered for task '{task.title}'. "
                "Register an appropriate agent before running."
            )

        task.assigned_agent = agent.name
        self._logger.info(
            "Dispatching task '%s' to agent '%s'.", task.title, agent.name
        )
        return agent.run(task.description, task=task)
