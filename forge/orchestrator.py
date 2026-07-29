"""Orchestrator for coordinating Forge-AI agents."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from .agents import (
    BaseAgent,
    CoderAgent,
    DebugAgent,
    DocumentationAgent,
    GitAgent,
    PlannerAgent,
    ResearchAgent,
    ReviewerAgent,
    Task,
    TestAgent,
)
from .config import settings
from .logger import log_structured, logger
from .memory import MemoryManager
from .scheduler import Scheduler
from .tasks import TaskExecution, TaskExecutionError, TaskState


@dataclass(frozen=True)
class TaskResult:
    """Details about a single task execution."""

    task: Task
    agent_name: str
    status: str
    attempts: int = 0
    result: Any = None
    error: str | None = None


@dataclass(frozen=True)
class ExecutionReport:
    """Summary of an orchestration run."""

    goal: str
    task_results: list[TaskResult] = field(default_factory=list)
    task_graph: dict[str, tuple[str, ...]] = field(default_factory=dict)
    max_parallelism: int = 0
    success: bool = True


class OrchestratorAgent:
    """Coordinate multi-agent execution for a user goal."""

    def __init__(
        self,
        logger_instance: logging.Logger | None = None,
        memory_manager: MemoryManager | None = None,
        project_name: str = settings.app_name,
        memory_path: str | None = None,
        max_parallel_tasks: int | None = None,
    ) -> None:
        self._logger = logger_instance or logger
        self._agents: list[tuple[tuple[str, ...], BaseAgent]] = []
        self._memory_manager = (
            memory_manager
            if memory_manager is not None
            else MemoryManager(
                project_name=project_name,
                memory_path=memory_path or settings.memory.path,
            )
        )
        self._scheduler = Scheduler(
            max_workers=max_parallel_tasks or settings.scheduler.max_parallel_tasks,
            logger_instance=self._logger,
        )
        self._memory_manager.load()
        self._register_builtin_agents()

    def _register_builtin_agents(self) -> None:
        self.register_agent(PlannerAgent(), keywords=("plan", "task", "goal", "feature"))
        self.register_agent(CoderAgent(), keywords=("code", "coding", "implement", "write"))
        self.register_agent(ReviewerAgent(), keywords=("review", "bug", "quality"))
        self.register_agent(ResearchAgent(), keywords=("research", "docs", "documentation"))
        self.register_agent(TestAgent(), keywords=("test", "validate", "verify"))
        self.register_agent(DebugAgent(), keywords=("debug", "retry", "failure"))
        self.register_agent(DocumentationAgent(), keywords=("document", "readme", "guide"))
        self.register_agent(GitAgent(), keywords=("git", "branch", "commit", "release"))

    def register_agent(self, agent: BaseAgent, keywords: Sequence[str]) -> None:
        """Register an agent with one or more keywords for dispatching."""

        normalized_keywords = tuple(keyword.lower() for keyword in keywords)
        self._agents.append((normalized_keywords, agent))
        self._logger.info("Registered agent %s with keywords %s", agent.name, normalized_keywords)

    def run(self, goal: str) -> ExecutionReport:
        """Execute the full workflow for a single user goal."""

        self._logger.info("Starting orchestration for goal: %s", goal)
        planner = self._resolve_agent_by_task_type("planner")
        if planner is None:
            raise RuntimeError("No planner agent registered")

        tasks = planner.run(goal)
        if not isinstance(tasks, list):
            tasks = [tasks]

        self._memory_manager.set_goal_summary(goal)
        self._memory_manager.add_project_goal(goal)
        self._memory_manager.memory.conversation.goal = goal
        self._memory_manager.add_summary(
            title="Goal",
            content=goal,
            categories=["goal"],
            metadata={"task_count": len(tasks)},
        )
        log_structured(self._logger, logging.INFO, "orchestration_started", goal=goal)

        try:
            scheduler_report = self._scheduler.run(
                tasks,
                self.execute_task,
                on_state_change=self._record_task_state,
            )
            task_results = [
                TaskResult(
                    task=state.task,
                    agent_name=state.assigned_agent or state.task.agent_hint or "Unassigned",
                    status=state.status.value,
                    attempts=state.attempts,
                    result=state.result,
                    error=state.error,
                )
                for state in scheduler_report.task_states
            ]
            report = ExecutionReport(
                goal=goal,
                task_results=task_results,
                task_graph=scheduler_report.task_graph,
                max_parallelism=scheduler_report.max_parallelism,
                success=scheduler_report.success,
            )
            self._memory_manager.add_summary(
                title="Execution result",
                content=f"Goal completed with success={report.success}.",
                categories=["execution"],
                metadata={
                    "success": report.success,
                    "max_parallelism": report.max_parallelism,
                },
            )
            self._logger.info("Completed orchestration with success=%s", report.success)
            return report
        finally:
            self._memory_manager.save()

    def execute_task(self, task: Task, attempt: int) -> TaskExecution:
        """Execute a single task using the best matching registered agent."""

        agent = self._select_agent(task)
        if agent is None:
            raise TaskExecutionError("Unassigned", "No agent registered")

        self._memory_manager.add_agent_decision(
            agent_name=agent.name,
            task_id=task.task_id,
            decision=f"Selected {agent.name} for {task.task_type} task.",
            rationale="Matched agent capabilities to planned task type.",
            related_tasks=list(task.dependencies),
            metadata={"attempt": attempt},
        )
        prompt = task.description or task.title
        try:
            result = agent.run(prompt, task=task, attempt=attempt, memory=self._memory_manager)
            self._capture_result_context(task, agent.name, result)
            self._memory_manager.save()
            return TaskExecution(agent_name=agent.name, result=result)
        except Exception as exc:
            self._logger.exception("Task %s failed", task.title)
            self._record_debug_context(task, attempt, agent.name, str(exc))
            self._memory_manager.save()
            raise TaskExecutionError(agent.name, str(exc)) from exc

    def _select_agent(self, task: Task) -> BaseAgent | None:
        lowered = f"{task.title} {task.description}".lower()
        best_match: tuple[int, int, BaseAgent] | None = None
        for index, (keywords, agent) in enumerate(self._agents):
            if task.agent_hint and task.agent_hint.lower() == agent.name.lower():
                return agent

            keyword_matches = [keyword for keyword in keywords if keyword in lowered]
            if not agent.can_handle(task) and not keyword_matches:
                continue

            score = max((len(keyword) for keyword in keyword_matches), default=0)
            if task.task_type.lower() in {
                task_type.lower() for task_type in agent.supported_task_types
            }:
                score = max(score, len(task.task_type))

            if (
                best_match is None
                or score > best_match[0]
                or (score == best_match[0] and index > best_match[1])
            ):
                best_match = (score, index, agent)

        return None if best_match is None else best_match[2]

    def _resolve_agent_by_task_type(self, task_type: str) -> BaseAgent | None:
        lowered = task_type.lower()
        for _, agent in self._agents:
            if lowered in {name.lower() for name in agent.supported_task_types}:
                return agent
        return None

    def _record_task_state(self, state: TaskState) -> None:
        self._memory_manager.record_task_state(state)
        self._memory_manager.save()
        log_structured(
            self._logger,
            logging.INFO,
            "task_state_changed",
            task_id=state.task.task_id,
            status=state.status.value,
            attempts=state.attempts,
            agent=state.assigned_agent or state.task.agent_hint,
            dependencies=list(state.task.dependencies),
        )

    def _record_debug_context(
        self,
        task: Task,
        attempt: int,
        agent_name: str,
        error: str,
    ) -> None:
        debug_agent = self._resolve_agent_by_task_type("debug")
        if debug_agent is None or debug_agent.name == agent_name:
            return

        try:
            diagnosis = debug_agent.run(
                f"Task {task.title} failed with error: {error}",
                task=task,
                attempt=attempt,
                error=error,
            )
            self._memory_manager.add_agent_decision(
                agent_name=debug_agent.name,
                task_id=task.task_id,
                decision="Generated retry guidance.",
                rationale=self._summarize_result(diagnosis),
                related_tasks=[task.task_id],
                metadata={"attempt": attempt, "source_agent": agent_name},
            )
        except Exception:  # pragma: no cover - defensive branch
            self._logger.exception("Debug agent failed while diagnosing task %s", task.task_id)

    def _capture_result_context(self, task: Task, agent_name: str, result: Any) -> None:
        self._memory_manager.add_summary(
            title=task.title,
            content=self._summarize_result(result),
            categories=[task.task_type, agent_name.lower()],
            metadata={"task_id": task.task_id},
        )

        for file_path in getattr(result, "files_to_update", []):
            self._memory_manager.add_file_metadata(
                file_path=file_path,
                summary=f"{agent_name} recommended updates during {task.title}.",
                tags=[task.task_type, agent_name.lower()],
                metadata={"task_id": task.task_id},
            )

    def _summarize_result(self, result: Any) -> str:
        if hasattr(result, "__dict__"):
            return ", ".join(
                f"{key}={value}" for key, value in vars(result).items() if not key.startswith("_")
            )
        return str(result)


Orchestrator = OrchestratorAgent
