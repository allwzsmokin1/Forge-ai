"""Forge unified runtime package."""

from __future__ import annotations

from .dependency_injection import ServiceContainer
from .events import EventBus
from .lifecycle import NoOpRuntimeHook, RuntimeHook
from .metrics import RuntimeMetrics
from .models import HealthCheckResult, ToolContext, ToolExecutionRequest, ToolExecutionResult
from .permissions import PermissionPolicy
from .registry import ToolRegistry
from .runtime_manager import RuntimeHealthReport, ToolRuntimeManager

_default_runtime: ToolRuntimeManager | None = None


def _build_default_runtime() -> ToolRuntimeManager:
    from ..tools import (
        ArchiveTool,
        DockerTool,
        FilesystemTool,
        GitTool,
        PythonTool,
        SearchTool,
        TerminalTool,
        WebTool,
    )

    registry = ToolRegistry()
    for tool in (
        TerminalTool(),
        FilesystemTool(),
        GitTool(),
        PythonTool(),
        DockerTool(),
        SearchTool(),
        WebTool(),
        ArchiveTool(),
    ):
        registry.register(tool)

    runtime = ToolRuntimeManager(registry)
    runtime.startup()
    return runtime


def get_default_runtime() -> ToolRuntimeManager:
    global _default_runtime
    if _default_runtime is None:
        _default_runtime = _build_default_runtime()
    return _default_runtime


__all__ = [
    "ToolRuntimeManager",
    "ToolRegistry",
    "PermissionPolicy",
    "EventBus",
    "RuntimeHook",
    "NoOpRuntimeHook",
    "RuntimeMetrics",
    "ServiceContainer",
    "ToolExecutionRequest",
    "ToolExecutionResult",
    "ToolContext",
    "HealthCheckResult",
    "RuntimeHealthReport",
    "get_default_runtime",
]
