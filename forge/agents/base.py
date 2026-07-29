"""Base classes for Forge-AI agent implementations."""

from __future__ import annotations

import abc
from typing import Any

from forge.runtime import RuntimeManager, ToolOutcome


class BaseAgent(abc.ABC):
    """Abstract base class for Forge-AI agents.

    Every derived agent must expose a name, a description, and a run method.
    The run method should execute the agent's primary responsibility and return
    a typed result appropriate for the concrete agent.
    """

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

    def __init__(self, runtime: RuntimeManager | None = None) -> None:
        self._runtime = runtime

    @property
    def runtime(self) -> RuntimeManager | None:
        """Runtime manager used to resolve tool capabilities."""
        return getattr(self, "_runtime", None)

    def set_runtime(self, runtime: RuntimeManager) -> None:
        """Attach a runtime manager to the agent."""
        self._runtime = runtime

    def request_tool(
        self,
        capability: str,
        action: str,
        payload: dict[str, Any] | None = None,
        retries: int | None = None,
    ) -> ToolOutcome | None:
        """Request execution through the shared runtime registry."""
        runtime = self.runtime
        if runtime is None:
            return None
        try:
            return runtime.execute_capability(
                agent_name=self.name,
                capability=capability,
                action=action,
                payload=payload,
                retries=retries,
            )
        except KeyError:
            return None
