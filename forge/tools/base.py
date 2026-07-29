"""Base interfaces for Forge tool implementations."""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ToolExecutionRequest:
    action: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ToolExecutionResult:
    success: bool
    data: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseTool(abc.ABC):
    """Base class for runtime tools."""

    name: str = "tool"
    description: str = ""
    capabilities: tuple[str, ...] = ()
    required_permissions: tuple[str, ...] = ()

    @abc.abstractmethod
    def execute(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        """Execute a tool action and return a normalized result."""

    def health_check(self) -> ToolExecutionResult:
        return ToolExecutionResult(success=True, data={"status": "ok"})

    def _ok(self, data: Any = None, **metadata: Any) -> ToolExecutionResult:
        return ToolExecutionResult(success=True, data=data, metadata=metadata)

    def _error(self, message: str, **metadata: Any) -> ToolExecutionResult:
        return ToolExecutionResult(success=False, error=message, metadata=metadata)
