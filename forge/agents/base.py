"""Base classes for Forge-AI agent implementations."""

from __future__ import annotations

import abc
from typing import Any

from ..runtime import (
    ToolExecutionRequest,
    ToolExecutionResult,
    ToolRuntimeManager,
    get_default_runtime,
)


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

    def request_tool(
        self,
        *,
        tool: str,
        capability: str,
        payload: dict[str, Any] | None = None,
        retries: int = 0,
    ) -> ToolExecutionResult:
        """Request a runtime-managed tool capability."""
        request = ToolExecutionRequest(
            tool=tool,
            capability=capability,
            agent=self.name,
            payload=payload or {},
            retries=retries,
        )
        return self.runtime.execute(request)

    def __init__(self, runtime: ToolRuntimeManager | None = None) -> None:
        self.runtime = runtime or get_default_runtime()
