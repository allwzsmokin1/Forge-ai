"""Core runtime data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ToolCall:
    """A normalized tool execution request."""

    agent_name: str
    tool_name: str
    action: str
    payload: dict[str, Any] = field(default_factory=dict)
    retries: int = 0


@dataclass(frozen=True)
class ToolOutcome:
    """A normalized tool execution result."""

    success: bool
    data: Any = None
    error: str | None = None
    attempts: int = 1
    duration_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
