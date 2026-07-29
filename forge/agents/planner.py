"""Planner agent for task decomposition and prioritization."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha1
from typing import Any, List

from .base import BaseAgent


@dataclass(frozen=True)
class Task:
    """Represents a planned task with routing and dependency metadata."""

    title: str
    description: str
    priority: int
    order: int
    task_id: str = ""
    task_type: str = "general"
    dependencies: tuple[str, ...] = ()
    max_retries: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class PlannerAgent(BaseAgent):
    """Agent responsible for planning work from user goals."""

    @property
    def name(self) -> str:
        return "PlannerAgent"

    @property
    def description(self) -> str:
        return (
            "Break user goals into discrete tasks, assign execution priority, "
            "and return a structured task list."
        )

    def run(self, prompt: str, **kwargs: object) -> List[Task]:
        """Convert a user goal into a task plan.

        The planner uses simple heuristics to split goals into ordered tasks and
        to assign priority, task type, and dependencies based on keyword cues.
        """
        goal = prompt.strip()
        if not goal:
            return []

        chain_tasks = " then " in goal.lower()
        separators = [";", " and ", " then "]
        raw_tasks: List[str] = [goal]
        for separator in separators:
            if separator in goal.lower():
                raw_tasks = [segment.strip() for segment in goal.split(separator) if segment.strip()]
                break

        tasks: List[Task] = []
        previous_task_id: str | None = None
        implementation_task_id: str | None = None
        for index, description in enumerate(raw_tasks, start=1):
            lowered = description.lower()
            if "urgent" in lowered or "critical" in lowered:
                priority = 1
            elif "research" in lowered or "investigate" in lowered:
                priority = 2
            else:
                priority = 3

            task_type = self._infer_task_type(lowered)
            title = description[:80]
            task_id = self._build_task_id(title=title, order=index)
            dependencies: tuple[str, ...] = ()

            if chain_tasks and previous_task_id is not None:
                dependencies = (previous_task_id,)
            elif task_type in {"review", "test", "documentation", "git", "debug"} and implementation_task_id:
                dependencies = (implementation_task_id,)

            if task_type in {"code", "debug"}:
                implementation_task_id = task_id

            tasks.append(
                Task(
                    title=title,
                    description=description,
                    priority=priority,
                    order=index,
                    task_id=task_id,
                    task_type=task_type,
                    dependencies=dependencies,
                )
            )
            previous_task_id = task_id

        return sorted(tasks, key=lambda task: (task.priority, task.order))

    def _infer_task_type(self, description: str) -> str:
        if any(keyword in description for keyword in ("plan", "task", "goal", "decompose")):
            return "plan"
        if any(keyword in description for keyword in ("review", "quality", "audit")):
            return "review"
        if any(keyword in description for keyword in ("test", "verify", "validation", "check")):
            return "test"
        if any(keyword in description for keyword in ("debug", "fix", "repair", "resolve")):
            return "debug"
        if any(keyword in description for keyword in ("document", "docs", "readme", "guide")):
            return "documentation"
        if any(keyword in description for keyword in ("commit", "branch", "git", "release", "tag")):
            return "git"
        if any(keyword in description for keyword in ("research", "investigate", "analyze")):
            return "research"
        if any(keyword in description for keyword in ("code", "implement", "build", "write", "create")):
            return "code"
        return "general"

    def _build_task_id(self, title: str, order: int) -> str:
        digest = sha1(f"{order}:{title}".encode("utf-8")).hexdigest()[:12]
        return f"task-{order:02d}-{digest}"
