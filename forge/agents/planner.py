"""Planner agent for task decomposition and prioritization."""

from __future__ import annotations

from dataclasses import dataclass

from .base import BaseAgent


@dataclass(frozen=True)
class Task:
    """Represents an ordered task produced by the planner."""

    title: str
    description: str
    priority: int
    order: int


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

    def run(self, prompt: str, **kwargs: object) -> list[Task]:
        """Convert a user goal into a task plan.

        The planner uses simple heuristics to split goals into ordered tasks and
        to assign priority based on keyword cues.
        """
        if kwargs.get("runtime_probe"):
            self.request_tool(
                tool="filesystem",
                capability="filesystem.list",
                payload={"operation": "list", "path": "."},
            )
        goal = prompt.strip()
        if not goal:
            return []

        separators = [";", " and ", " then "]
        raw_tasks: list[str] = [goal]
        for separator in separators:
            if separator in goal:
                raw_tasks = [
                    segment.strip() for segment in goal.split(separator) if segment.strip()
                ]
                break

        tasks: list[Task] = []
        for index, description in enumerate(raw_tasks, start=1):
            lowered = description.lower()
            if "urgent" in lowered or "critical" in lowered:
                priority = 1
            elif "research" in lowered or "investigate" in lowered:
                priority = 2
            else:
                priority = 3
            title = description[:80]
            tasks.append(Task(title=title, description=description, priority=priority, order=index))

        return sorted(tasks, key=lambda task: (task.priority, task.order))
