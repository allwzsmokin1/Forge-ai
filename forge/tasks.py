"""Task models for dependency-aware orchestration."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import uuid4


class TaskStatus(StrEnum):
    """Lifecycle states for orchestrated tasks."""

    QUEUED = "queued"
    RUNNING = "running"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class RetryPolicy:
    """Retry settings for task execution."""

    max_attempts: int = 1


@dataclass(frozen=True)
class Task:
    """A dependency-aware unit of work produced by the planner."""

    title: str
    description: str
    priority: int
    order: int
    task_type: str = "general"
    dependencies: tuple[str, ...] = ()
    agent_hint: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    task_id: str = field(default_factory=lambda: uuid4().hex)


@dataclass
class TaskState:
    """Mutable execution state for a task."""

    task: Task
    status: TaskStatus
    attempts: int = 0
    assigned_agent: str | None = None
    result: Any = None
    error: str | None = None
    started_at: str | None = None
    completed_at: str | None = None

    @property
    def is_terminal(self) -> bool:
        """Return whether the task can no longer transition."""

        return self.status in {TaskStatus.COMPLETED, TaskStatus.FAILED}


@dataclass(frozen=True)
class TaskExecution:
    """Successful task execution payload."""

    agent_name: str
    result: Any


class TaskExecutionError(RuntimeError):
    """Execution failure tagged with the selected agent name."""

    def __init__(self, agent_name: str, message: str) -> None:
        super().__init__(message)
        self.agent_name = agent_name


class TaskGraph:
    """Directed acyclic graph describing task dependencies."""

    def __init__(self, tasks: list[Task]) -> None:
        self._tasks = sorted(tasks, key=lambda task: (task.order, task.priority, task.title))
        self._task_map = {task.task_id: task for task in self._tasks}
        if len(self._task_map) != len(self._tasks):
            raise ValueError("Task ids must be unique")

        for task in self._tasks:
            for dependency in task.dependencies:
                if dependency not in self._task_map:
                    raise ValueError(f"Task {task.task_id} depends on unknown task {dependency}")

        self._dependents: dict[str, list[str]] = {task.task_id: [] for task in self._tasks}
        for task in self._tasks:
            for dependency in task.dependencies:
                self._dependents[dependency].append(task.task_id)

        self._validate_acyclic()

    @property
    def tasks(self) -> list[Task]:
        """Return graph tasks in stable order."""

        return list(self._tasks)

    def task_ids(self) -> list[str]:
        """Return the ordered task ids."""

        return [task.task_id for task in self._tasks]

    def get(self, task_id: str) -> Task:
        """Return a task by id."""

        return self._task_map[task_id]

    def dependencies_for(self, task_id: str) -> tuple[str, ...]:
        """Return direct dependencies for a task."""

        return self._task_map[task_id].dependencies

    def dependents_for(self, task_id: str) -> tuple[str, ...]:
        """Return direct dependents for a task."""

        return tuple(self._dependents[task_id])

    def adjacency_map(self) -> dict[str, tuple[str, ...]]:
        """Return the dependency graph as an adjacency map."""

        return {task.task_id: tuple(self._dependents[task.task_id]) for task in self._tasks}

    def _validate_acyclic(self) -> None:
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(task_id: str) -> None:
            if task_id in visited:
                return
            if task_id in visiting:
                raise ValueError("Task dependencies must form a directed acyclic graph")

            visiting.add(task_id)
            for dependent in self._dependents[task_id]:
                visit(dependent)
            visiting.remove(task_id)
            visited.add(task_id)

        for task in self._tasks:
            visit(task.task_id)
