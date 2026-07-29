"""Dependency-aware orchestration for coordinating Forge-AI agents."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field, is_dataclass
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
from .config import Settings, settings
from .logger import logger
from .memory import MemoryManager
from .scheduler import (
    TASK_STATUS_COMPLETED,
    TASK_STATUS_FAILED,
    RetryPolicy,
    SchedulerResult,
    TaskGraph,
    TaskScheduler,
)


@dataclass(frozen=True)
class TaskResult:
    """Details about a single task execution."""

    task: Task
    agent_name: str
    status: str
    result: Any = None
    error: str | None = None
    attempts: int = 1


@dataclass(frozen=True)
class ExecutionReport:
    """Summary of an orchestration run."""

    goal: str
    task_results: list[TaskResult] = field(default_factory=list)
    success: bool = True
    task_states: dict[str, str] = field(default_factory=dict)
    dependency_map: dict[str, list[str]] = field(default_factory=dict)


class OrchestratorAgent(BaseAgent):
    """Coordinate specialized agents against a dependency-aware task graph."""

    def __init__(
        self,
        logger_instance: logging.Logger | None = None,
        memory_manager: MemoryManager | None = None,
        project_name: str = "ForgeAI",
        memory_path: str | None = None,
        config: Settings | None = None,
        scheduler: TaskScheduler | None = None,
    ) -> None:
        self._settings = config or settings
        self._logger = logger_instance or logger
        self._agents: list[tuple[tuple[str, ...], tuple[str, ...], BaseAgent]] = []
        self._memory_manager = (
            memory_manager
            if memory_manager is not None
            else MemoryManager(
                project_name=project_name,
                memory_path=memory_path or self._settings.memory_path,
            )
        )
        self._memory_manager.load()
        self._retry_policy = RetryPolicy(
            max_retries=self._settings.default_task_retries,
            backoff_seconds=self._settings.retry_backoff_seconds,
        )
        self._scheduler = scheduler or TaskScheduler(max_workers=self._settings.max_parallel_tasks)
        self._register_builtin_agents()

    @property
    def name(self) -> str:
        return "OrchestratorAgent"

    @property
    def description(self) -> str:
        return (
            "Decompose goals into a task graph, schedule dependency-aware work, "
            "coordinate specialized agents, and persist project memory."
        )

    def _register_builtin_agents(self) -> None:
        self.register_agent(
            PlannerAgent(),
            keywords=("plan", "task", "goal", "feature"),
            task_types=("plan",),
        )
        self.register_agent(
            CoderAgent(),
            keywords=("code", "coding", "implement", "write", "build", "create"),
            task_types=("code", "general"),
        )
        self.register_agent(
            ReviewerAgent(),
            keywords=("review", "bug", "quality", "audit"),
            task_types=("review",),
        )
        self.register_agent(
            ResearchAgent(),
            keywords=("research", "docs", "documentation", "analyze"),
            task_types=("research",),
        )
        self.register_agent(
            TestAgent(),
            keywords=("test", "verify", "validation", "check"),
            task_types=("test",),
        )
        self.register_agent(
            DebugAgent(),
            keywords=("debug", "fix", "repair", "resolve"),
            task_types=("debug",),
        )
        self.register_agent(
            DocumentationAgent(),
            keywords=("document", "docs", "readme", "guide"),
            task_types=("documentation",),
        )
        self.register_agent(
            GitAgent(),
            keywords=("git", "commit", "branch", "release", "tag"),
            task_types=("git",),
        )

    def register_agent(
        self,
        agent: BaseAgent,
        keywords: Sequence[str],
        task_types: Sequence[str] | None = None,
    ) -> None:
        """Register an agent with one or more keywords and task types for dispatching."""

        normalized_keywords = tuple(keyword.lower() for keyword in keywords)
        normalized_task_types = tuple(task_type.lower() for task_type in (task_types or ()))
        self._agents.append((normalized_keywords, normalized_task_types, agent))
        self._logger.info(
            "event=agent_registered agent=%s keywords=%s task_types=%s",
            agent.name,
            normalized_keywords,
            normalized_task_types,
        )

    def run(self, prompt: str, **kwargs: Any) -> ExecutionReport:
        """Execute the full orchestration workflow for a single user goal."""

        goal = prompt.strip()
        self._logger.info("event=orchestration_started goal=%s", goal)
        planner = self._resolve_agent_for_task("plan")
        if planner is None:
            raise RuntimeError("No planner agent registered")

        tasks = planner.run(goal, **kwargs)
        if not isinstance(tasks, list):
            tasks = [tasks]

        graph = TaskGraph(tasks)
        self._memory_manager.set_goal_summary(goal)
        self._memory_manager.memory.conversation.goal = goal
        self._memory_manager.add_summary("latest_goal", goal)
        for task in tasks:
            self._memory_manager.record_task_dependencies(task.task_id, list(task.dependencies))
            self._memory_manager.record_agent_decision(
                agent_name=self.name,
                task_id=task.task_id,
                decision="planned",
                rationale=f"Task '{task.title}' assigned type '{task.task_type}'.",
            )

        try:
            scheduled = self._scheduler.execute(
                graph=graph,
                executor=self.execute_task,
                retry_policy=self._retry_policy,
            )
            report = self._build_execution_report(goal=goal, tasks=tasks, scheduled=scheduled)
            self._memory_manager.add_summary("latest_execution_success", str(report.success))
            self._logger.info("event=orchestration_finished success=%s", report.success)
            return report
        finally:
            self._memory_manager.save()

    def execute_task(self, task: Task, attempt: int = 1) -> TaskResult:
        """Execute a single task using the best matching registered agent."""

        agent = self._select_agent(task)
        if agent is None:
            self._memory_manager.record_task_state(
                task_id=task.task_id,
                title=task.title,
                description=task.description,
                agent_name="None",
                status=TASK_STATUS_FAILED,
                attempt=attempt,
                dependencies=list(task.dependencies),
                error="No agent registered",
            )
            return TaskResult(
                task=task,
                agent_name="None",
                status=TASK_STATUS_FAILED,
                error="No agent registered",
                attempts=attempt,
            )

        self._memory_manager.record_agent_decision(
            agent_name=self.name,
            task_id=task.task_id,
            decision="selected_agent",
            rationale=f"Selected {agent.name} for task type '{task.task_type}'.",
        )
        self._memory_manager.record_task_state(
            task_id=task.task_id,
            title=task.title,
            description=task.description,
            agent_name=agent.name,
            status="running",
            attempt=attempt,
            dependencies=list(task.dependencies),
        )

        prompt = self._task_query(task)
        try:
            result = agent.run(
                prompt,
                task=task,
                context=self._memory_manager.get_context(prompt),
                memory=self._memory_manager,
            )
            summary = self._summarize_result(result)
            task_result = TaskResult(
                task=task,
                agent_name=agent.name,
                status=TASK_STATUS_COMPLETED,
                result=result,
                attempts=attempt,
            )
            self._memory_manager.record_task_state(
                task_id=task.task_id,
                title=task.title,
                description=task.description,
                agent_name=agent.name,
                status=task_result.status,
                attempt=attempt,
                dependencies=list(task.dependencies),
                result_summary=summary,
            )
            self._memory_manager.add_entry(
                task_title=task.title,
                task_description=task.description,
                agent_name=agent.name,
                status=task_result.status,
                result=summary,
                error=None,
                categories=[agent.name.lower(), task.task_type],
            )
            self._memory_manager.add_summary(f"task:{task.task_id}", summary)
            self._logger.info(
                "event=task_completed task_id=%s agent=%s attempt=%d",
                task.task_id,
                agent.name,
                attempt,
            )
            return task_result
        except Exception as exc:  # pragma: no cover - defensive branch
            error = str(exc)
            self._logger.exception(
                "event=task_failed task_id=%s agent=%s attempt=%d error=%s",
                task.task_id,
                agent.name,
                attempt,
                error,
            )
            self._memory_manager.record_task_state(
                task_id=task.task_id,
                title=task.title,
                description=task.description,
                agent_name=agent.name,
                status=TASK_STATUS_FAILED,
                attempt=attempt,
                dependencies=list(task.dependencies),
                error=error,
            )
            self._memory_manager.add_entry(
                task_title=task.title,
                task_description=task.description,
                agent_name=agent.name,
                status=TASK_STATUS_FAILED,
                result=None,
                error=error,
                categories=[agent.name.lower(), task.task_type],
            )
            return TaskResult(
                task=task,
                agent_name=agent.name,
                status=TASK_STATUS_FAILED,
                error=error,
                attempts=attempt,
            )

    def _build_execution_report(
        self,
        goal: str,
        tasks: Sequence[Task],
        scheduled: SchedulerResult,
    ) -> ExecutionReport:
        task_results: list[TaskResult] = []
        for task in sorted(tasks, key=lambda item: item.order):
            result = scheduled.results.get(task.task_id)
            if isinstance(result, TaskResult):
                task_results.append(
                    TaskResult(
                        task=task,
                        agent_name=result.agent_name,
                        status=scheduled.states.get(task.task_id, result.status),
                        result=result.result,
                        error=result.error,
                        attempts=scheduled.attempts.get(task.task_id, result.attempts),
                    )
                )
                continue

            task_results.append(
                TaskResult(
                    task=task,
                    agent_name="None",
                    status=scheduled.states.get(task.task_id, TASK_STATUS_FAILED),
                    result=None,
                    error="Task was blocked by unmet dependencies.",
                    attempts=scheduled.attempts.get(task.task_id, 0),
                )
            )

        success = all(result.status == TASK_STATUS_COMPLETED for result in task_results)
        return ExecutionReport(
            goal=goal,
            task_results=task_results,
            success=success,
            task_states=scheduled.states,
            dependency_map={task.task_id: list(task.dependencies) for task in tasks},
        )

    def _select_agent(self, task: Task) -> BaseAgent | None:
        task_type = task.task_type.lower()
        for _, task_types, agent in self._agents:
            if task_type in task_types:
                return agent

        description = self._task_query(task).lower()
        best_match: tuple[int, int, BaseAgent] | None = None
        for index, (keywords, _, agent) in enumerate(self._agents):
            if any(keyword in description for keyword in keywords):
                score = max(len(keyword) for keyword in keywords if keyword in description)
                if (
                    best_match is None
                    or score > best_match[0]
                    or (score == best_match[0] and index > best_match[1])
                ):
                    best_match = (score, index, agent)
        return None if best_match is None else best_match[2]

    def _resolve_agent_for_task(self, task_type: str) -> BaseAgent | None:
        lowered = task_type.lower()
        for _, task_types, agent in self._agents:
            if lowered in task_types:
                return agent
        for keywords, _, agent in self._agents:
            if any(keyword == lowered for keyword in keywords):
                return agent
        return None

    def _summarize_result(self, result: Any) -> str:
        if result is None:
            return ""
        if isinstance(result, str):
            return result
        if is_dataclass(result):
            serialized = asdict(result)
            return "; ".join(f"{key}={value}" for key, value in serialized.items())
        if isinstance(result, dict):
            return "; ".join(f"{key}={value}" for key, value in result.items())
        if isinstance(result, list):
            return ", ".join(self._summarize_result(item) for item in result)
        return str(result)

    def _task_query(self, task: Task) -> str:
        return task.description if task.description else task.title


class Orchestrator(OrchestratorAgent):
    """Backward-compatible orchestrator alias for prior integrations."""
