"""Planner agent for task decomposition and prioritization."""

from __future__ import annotations

import re

from ..config import settings
from ..tasks import RetryPolicy, Task
from .base import BaseAgent


class PlannerAgent(BaseAgent):
    """Agent responsible for planning work from user goals."""

    @property
    def supported_task_types(self) -> tuple[str, ...]:
        return ("planner",)

    @property
    def keywords(self) -> tuple[str, ...]:
        return ("plan", "task", "goal", "feature", "phase", "orchestrate")

    @property
    def name(self) -> str:
        return "PlannerAgent"

    @property
    def description(self) -> str:
        return (
            "Break user goals into discrete tasks, assign execution priority, "
            "and return a structured task list."
        )

    def run(self, prompt: str, **kwargs: object) -> list[Task]:
        """Convert a user goal into a task plan.

        The planner produces dependency-aware tasks so the scheduler can run
        independent work in parallel while preserving required ordering.
        """
        goal = prompt.strip()
        if not goal:
            return []

        goal = re.sub(r"\s+", " ", goal).strip()
        split_tasks = self._split_goal(goal)
        if len(split_tasks) > 1:
            sequential = " then " in goal.lower()
            planned_tasks: list[Task] = []
            previous_task_id: str | None = None
            for index, description in enumerate(split_tasks, start=1):
                task_type = self._infer_task_type(description)
                task = Task(
                    title=self._build_title(description, task_type),
                    description=description,
                    priority=self._infer_priority(description),
                    order=index,
                    task_type=task_type,
                    dependencies=((previous_task_id,) if sequential and previous_task_id else ()),
                    agent_hint=self._default_agent_hint(task_type),
                    retry_policy=self._retry_policy(task_type),
                )
                planned_tasks.append(task)
                previous_task_id = task.task_id
            return planned_tasks

        if self._is_complex_goal(goal):
            return self._build_delivery_pipeline(goal)

        task_type = self._infer_task_type(goal)
        return [
            Task(
                title=self._build_title(goal, task_type),
                description=goal,
                priority=self._infer_priority(goal),
                order=1,
                task_type=task_type,
                agent_hint=self._default_agent_hint(task_type),
                retry_policy=self._retry_policy(task_type),
            )
        ]

    def _split_goal(self, goal: str) -> list[str]:
        separators = [r";", r"\n+", r"\bthen\b"]
        for separator in separators:
            fragments = [
                segment.strip(" .") for segment in re.split(separator, goal, flags=re.IGNORECASE)
            ]
            filtered_fragments = [fragment for fragment in fragments if fragment]
            if len(filtered_fragments) > 1:
                return filtered_fragments
        return [goal]

    def _is_complex_goal(self, goal: str) -> bool:
        lowered = goal.lower()
        complexity_markers = (
            "build",
            "implement",
            "create",
            "feature",
            "framework",
            "orchestr",
            "phase",
            "system",
        )
        return len(goal.split()) >= 10 or any(marker in lowered for marker in complexity_markers)

    def _build_delivery_pipeline(self, goal: str) -> list[Task]:
        tasks: list[Task] = []
        order = 1

        research_task: Task | None = None
        if any(keyword in goal.lower() for keyword in ("research", "investigate", "analyze")):
            research_task = Task(
                title="Research implementation context",
                description=f"Gather context and best practices for: {goal}",
                priority=1,
                order=order,
                task_type="research",
                agent_hint="ResearchAgent",
            )
            tasks.append(research_task)
            order += 1

        implementation_dependencies = (research_task.task_id,) if research_task is not None else ()
        implementation_task = Task(
            title="Implement requested change",
            description=goal,
            priority=1,
            order=order,
            task_type="code",
            dependencies=implementation_dependencies,
            agent_hint="CoderAgent",
            retry_policy=self._retry_policy("code"),
        )
        tasks.append(implementation_task)
        order += 1

        review_task = Task(
            title="Review implementation",
            description=f"Review the implementation for: {goal}",
            priority=2,
            order=order,
            task_type="review",
            dependencies=(implementation_task.task_id,),
            agent_hint="ReviewerAgent",
        )
        tasks.append(review_task)
        order += 1

        test_task = Task(
            title="Validate implementation",
            description=f"Validate behavior and test coverage for: {goal}",
            priority=2,
            order=order,
            task_type="test",
            dependencies=(implementation_task.task_id,),
            agent_hint="TestAgent",
            retry_policy=self._retry_policy("test"),
        )
        tasks.append(test_task)
        order += 1

        documentation_task = Task(
            title="Document implementation",
            description=f"Document the delivered change for: {goal}",
            priority=3,
            order=order,
            task_type="documentation",
            dependencies=(implementation_task.task_id,),
            agent_hint="DocumentationAgent",
        )
        tasks.append(documentation_task)
        order += 1

        git_task = Task(
            title="Prepare git handoff",
            description=f"Prepare branch and commit guidance for: {goal}",
            priority=3,
            order=order,
            task_type="git",
            dependencies=(
                review_task.task_id,
                test_task.task_id,
                documentation_task.task_id,
            ),
            agent_hint="GitAgent",
        )
        tasks.append(git_task)
        return tasks

    def _infer_task_type(self, description: str) -> str:
        lowered = description.lower()
        mapping = {
            "review": ("review", "audit", "quality"),
            "test": ("test", "validate", "verify", "coverage"),
            "documentation": ("document", "docs", "readme"),
            "git": ("commit", "branch", "release", "git"),
            "research": ("research", "investigate", "analyze"),
            "code": ("code", "implement", "build", "create", "fix"),
        }
        for task_type, keywords in mapping.items():
            if any(keyword in lowered for keyword in keywords):
                return task_type
        return "code"

    def _infer_priority(self, description: str) -> int:
        lowered = description.lower()
        if "urgent" in lowered or "critical" in lowered:
            return 1
        if any(keyword in lowered for keyword in ("review", "test", "validate")):
            return 2
        return 3

    def _build_title(self, description: str, task_type: str) -> str:
        prefix = {
            "code": "Implement",
            "review": "Review",
            "test": "Validate",
            "documentation": "Document",
            "git": "Prepare git plan for",
            "research": "Research",
        }.get(task_type, "Handle")
        subject = description.strip().rstrip(".")
        return f"{prefix} {subject}"[:80]

    def _default_agent_hint(self, task_type: str) -> str | None:
        return {
            "code": "CoderAgent",
            "review": "ReviewerAgent",
            "test": "TestAgent",
            "documentation": "DocumentationAgent",
            "git": "GitAgent",
            "research": "ResearchAgent",
            "planner": "PlannerAgent",
        }.get(task_type)

    def _retry_policy(self, task_type: str) -> RetryPolicy:
        if task_type in {"code", "test"}:
            return RetryPolicy(max_attempts=settings.scheduler.default_retry_attempts)
        return RetryPolicy(max_attempts=1)
