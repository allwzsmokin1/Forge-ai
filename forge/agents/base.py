"""Base classes for Forge-AI agent implementations."""

from __future__ import annotations

import abc
from typing import Any

from ..runtime import RuntimeManager, get_runtime


class BaseAgent(abc.ABC):
    """Abstract base class for Forge-AI agents.

    Every derived agent must expose a name, a description, and a run method.
    The run method should execute the agent's primary responsibility and return
    a typed result appropriate for the concrete agent.
    """

    def __init__(self, runtime_manager: RuntimeManager | None = None) -> None:
        self._runtime_manager = runtime_manager or get_runtime()

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

    @property
    def runtime_manager(self) -> RuntimeManager:
        """Return the runtime manager bound to this agent."""

        return self._runtime_manager

    def set_runtime_manager(self, runtime_manager: RuntimeManager) -> None:
        """Update the runtime manager used by the agent."""

        self._runtime_manager = runtime_manager

    def execute_tool(
        self,
        tool_name: str,
        operation: str = "run",
        payload: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Execute a runtime tool through the shared registry."""

        return self.runtime_manager.execute(
            tool_name,
            operation=operation,
            payload=payload,
            **kwargs,
        )
