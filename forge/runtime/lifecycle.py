"""Lifecycle hooks for runtime execution."""

from __future__ import annotations

from typing import Sequence

from .models import RuntimeContext, ToolExecutionRequest, ToolExecutionResult, ToolHealthStatus


class RuntimeHook:
    """Base hook for runtime lifecycle events."""

    def before_execution(self, request: ToolExecutionRequest, context: RuntimeContext) -> None:
        """Run before a tool invocation."""

    def after_execution(
        self,
        request: ToolExecutionRequest,
        result: ToolExecutionResult,
        context: RuntimeContext,
    ) -> None:
        """Run after a successful tool invocation."""

    def on_error(
        self,
        request: ToolExecutionRequest,
        error: Exception,
        attempt: int,
        context: RuntimeContext,
    ) -> None:
        """Run when a tool invocation fails."""

    def after_health_checks(
        self,
        statuses: Sequence[ToolHealthStatus],
        context: RuntimeContext,
    ) -> None:
        """Run after the runtime completes health checks."""
