"""Core data models for the Forge runtime."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ToolExecutionRequest:
    """Request payload for runtime-managed tool execution."""

    tool: str
    capability: str
    agent: str
    payload: dict[str, Any] = field(default_factory=dict)
    retries: int = 0


@dataclass(frozen=True)
class ToolExecutionResult:
    """Normalized result produced by a runtime tool."""

    success: bool
    output: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ToolContext:
    """Execution context that runtime provides to each tool."""

    request_id: str
    agent: str
    capability: str
    dependencies: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class HealthCheckResult:
    """Represents health status for a runtime component."""

    name: str
    healthy: bool
    details: dict[str, Any] = field(default_factory=dict)
