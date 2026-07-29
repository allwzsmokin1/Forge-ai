"""Runtime data models for Forge-AI tool execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class ToolExecutionRequest:
    """Normalized request payload for a tool invocation."""

    tool_name: str
    operation: str = "run"
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timeout: Optional[float] = None
    retries: Optional[int] = None
    correlation_id: Optional[str] = None


@dataclass(frozen=True)
class ToolExecutionResult:
    """Normalized result returned from a tool invocation."""

    tool_name: str
    success: bool
    output: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    attempts: int = 1


@dataclass(frozen=True)
class ToolHealthStatus:
    """Health status returned by a tool health check."""

    tool_name: str
    healthy: bool
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RuntimeContext:
    """Execution context injected into tool invocations."""

    container: Any
    event_bus: Any
    logger: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
