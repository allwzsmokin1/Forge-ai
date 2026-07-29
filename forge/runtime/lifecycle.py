"""Lifecycle hooks for runtime startup/shutdown and tool execution."""

from __future__ import annotations

from typing import Protocol

from .models import ToolExecutionRequest, ToolExecutionResult


class RuntimeHook(Protocol):
    """Interface for observing runtime lifecycle events."""

    def on_startup(self) -> None: ...

    def on_shutdown(self) -> None: ...

    def before_execute(self, request: ToolExecutionRequest) -> None: ...

    def after_execute(self, request: ToolExecutionRequest, result: ToolExecutionResult) -> None: ...

    def on_error(self, request: ToolExecutionRequest, error: Exception) -> None: ...


class NoOpRuntimeHook:
    """Default hook implementation."""

    def on_startup(self) -> None:
        return

    def on_shutdown(self) -> None:
        return

    def before_execute(self, request: ToolExecutionRequest) -> None:
        return

    def after_execute(self, request: ToolExecutionRequest, result: ToolExecutionResult) -> None:
        return

    def on_error(self, request: ToolExecutionRequest, error: Exception) -> None:
        return
