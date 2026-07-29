"""Runtime lifecycle hook interfaces."""

from __future__ import annotations

import abc

from .models import ToolCall, ToolOutcome


class RuntimeHook(abc.ABC):
    """Lifecycle callbacks around tool execution."""

    def before_execute(self, call: ToolCall) -> None:
        """Called before runtime dispatches a tool call."""

    def after_execute(self, call: ToolCall, outcome: ToolOutcome) -> None:
        """Called after runtime dispatches a tool call."""

    def on_error(self, call: ToolCall, error: Exception) -> None:
        """Called when runtime catches a tool execution exception."""
