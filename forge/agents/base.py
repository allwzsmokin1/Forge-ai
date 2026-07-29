"""Base classes for Forge-AI agent implementations."""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..tasks import Task


class BaseAgent(abc.ABC):
    """Abstract base class for Forge-AI agents.

    Every derived agent must expose a name, a description, and a run method.
    The run method should execute the agent's primary responsibility and return
    a typed result appropriate for the concrete agent.
    """

    @property
    def supported_task_types(self) -> tuple[str, ...]:
        """Task types the agent can execute directly."""

        return ()

    @property
    def keywords(self) -> tuple[str, ...]:
        """Keywords that describe the agent's capabilities."""

        return ()

    def can_handle(self, task: Task) -> bool:
        """Return whether the agent can handle a planned task."""

        if task.agent_hint and task.agent_hint.lower() == self.name.lower():
            return True
        if task.task_type.lower() in {task_type.lower() for task_type in self.supported_task_types}:
            return True
        lowered = f"{task.title} {task.description}".lower()
        return any(keyword.lower() in lowered for keyword in self.keywords)

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """The human-readable name of the agent."""

    @property
    @abc.abstractmethod
    def description(self) -> str:
        """A short description of the agent's purpose."""

    @abc.abstractmethod
    def run(self, prompt: str, **kwargs: Any) -> Any:
        """Execute the agent on the provided prompt.

        Args:
            prompt: The user-facing request or goal.
            **kwargs: Extra context values for agent execution.

        Returns:
            A structured result value from the agent.
        """
        raise NotImplementedError
