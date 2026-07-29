"""Directed Acyclic Graph (DAG) for task dependency management.

Tracks which tasks can run concurrently, which are blocked by unfinished
predecessors, and detects cycles that would make execution impossible.
"""

from __future__ import annotations

import logging

from .models import OrchestratedTask, TaskStatus

logger = logging.getLogger("forge.orchestration.dag")


class CycleError(ValueError):
    """Raised when the dependency graph contains a cycle."""


class TaskDAG:
    """Directed Acyclic Graph that manages task execution order.

    Each task is a node; a directed edge from A → B means "B depends on A"
    (B cannot run until A is complete).

    Example::

        dag = TaskDAG()
        dag.add_task(task_a)
        dag.add_task(task_b)
        dag.add_dependency(task_b.id, depends_on_id=task_a.id)
        dag.validate()  # raises CycleError if a cycle exists
        ready = dag.get_ready_tasks()  # returns [task_a]
    """

    def __init__(self) -> None:
        self._tasks: dict[str, OrchestratedTask] = {}
        # adjacency list: task_id → set of task IDs that depend on it
        self._dependents: dict[str, set[str]] = {}
        self._logger = logger

    # ------------------------------------------------------------------
    # Mutation helpers
    # ------------------------------------------------------------------

    def add_task(self, task: OrchestratedTask) -> None:
        """Register a task in the DAG.

        Args:
            task: The task to add.

        Raises:
            ValueError: If a task with the same ID is already registered.
        """
        if task.id in self._tasks:
            raise ValueError(f"Task '{task.id}' is already registered in the DAG.")
        self._tasks[task.id] = task
        self._dependents.setdefault(task.id, set())
        for dep_id in task.dependencies:
            self._dependents.setdefault(dep_id, set()).add(task.id)
        self._logger.debug("Added task '%s' (%s) to DAG.", task.title, task.id)

    def add_dependency(self, task_id: str, depends_on_id: str) -> None:
        """Record that *task_id* depends on *depends_on_id*.

        Args:
            task_id: ID of the task that has a dependency.
            depends_on_id: ID of the task that must finish first.

        Raises:
            KeyError: If either task ID is not registered.
        """
        if task_id not in self._tasks:
            raise KeyError(f"Task '{task_id}' not found in DAG.")
        if depends_on_id not in self._tasks:
            raise KeyError(f"Dependency task '{depends_on_id}' not found in DAG.")
        task = self._tasks[task_id]
        if depends_on_id not in task.dependencies:
            task.dependencies.append(depends_on_id)
        self._dependents.setdefault(depends_on_id, set()).add(task_id)
        self._logger.debug("Added dependency %s → %s.", depends_on_id, task_id)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_task(self, task_id: str) -> OrchestratedTask | None:
        """Return the task with the given ID, or None if not found."""
        return self._tasks.get(task_id)

    def all_tasks(self) -> list[OrchestratedTask]:
        """Return all registered tasks sorted by priority then insertion order."""
        return sorted(self._tasks.values(), key=lambda t: (t.priority, t.title))

    def get_ready_tasks(self) -> list[OrchestratedTask]:
        """Return tasks whose dependencies are all completed and that are QUEUED.

        Returns:
            Ordered list of tasks ready for immediate execution.
        """
        completed_ids: set[str] = {
            tid for tid, t in self._tasks.items() if t.status == TaskStatus.COMPLETED
        }
        ready = [
            task
            for task in self._tasks.values()
            if task.status == TaskStatus.QUEUED and task.is_ready(completed_ids)
        ]
        return sorted(ready, key=lambda t: (t.priority, t.title))

    def get_blocked_tasks(self) -> list[OrchestratedTask]:
        """Return tasks that are waiting for one or more dependencies."""
        completed_ids: set[str] = {
            tid for tid, t in self._tasks.items() if t.status == TaskStatus.COMPLETED
        }
        return [
            task
            for task in self._tasks.values()
            if task.status in (TaskStatus.QUEUED, TaskStatus.BLOCKED)
            and not task.is_ready(completed_ids)
        ]

    def is_complete(self) -> bool:
        """Return True when every task has reached a terminal state."""
        return all(
            t.status in (TaskStatus.COMPLETED, TaskStatus.FAILED)
            for t in self._tasks.values()
        )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self) -> None:
        """Check the graph for dependency cycles.

        Raises:
            CycleError: If the graph contains a cycle.
        """
        visited: set[str] = set()
        in_stack: set[str] = set()

        def dfs(node: str) -> None:
            visited.add(node)
            in_stack.add(node)
            for dependent in self._dependents.get(node, set()):
                if dependent not in visited:
                    dfs(dependent)
                elif dependent in in_stack:
                    raise CycleError(
                        f"Cycle detected involving tasks '{node}' and '{dependent}'."
                    )
            in_stack.discard(node)

        for task_id in self._tasks:
            if task_id not in visited:
                dfs(task_id)

        self._logger.debug("DAG validation passed — no cycles detected.")

    # ------------------------------------------------------------------
    # Topological sort
    # ------------------------------------------------------------------

    def topological_sort(self) -> list[OrchestratedTask]:
        """Return tasks in a valid topological execution order.

        Returns:
            Tasks ordered so that every dependency appears before its dependent.

        Raises:
            CycleError: If the graph contains a cycle.
        """
        self.validate()

        in_degree: dict[str, int] = {tid: len(t.dependencies) for tid, t in self._tasks.items()}
        queue: list[OrchestratedTask] = sorted(
            [t for t in self._tasks.values() if in_degree[t.id] == 0],
            key=lambda t: (t.priority, t.title),
        )
        result: list[OrchestratedTask] = []

        while queue:
            task = queue.pop(0)
            result.append(task)
            for dependent_id in sorted(self._dependents.get(task.id, set())):
                in_degree[dependent_id] -= 1
                if in_degree[dependent_id] == 0:
                    dep_task = self._tasks[dependent_id]
                    # Insert while preserving priority ordering
                    inserted = False
                    for i, q_task in enumerate(queue):
                        if (dep_task.priority, dep_task.title) < (q_task.priority, q_task.title):
                            queue.insert(i, dep_task)
                            inserted = True
                            break
                    if not inserted:
                        queue.append(dep_task)

        return result
