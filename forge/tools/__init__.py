"""Tool registry bootstrap for Forge runtime."""

from __future__ import annotations

from .archive import ArchiveTool
from .base import BaseTool, ToolExecutionRequest, ToolExecutionResult
from .docker import DockerTool
from .filesystem import FilesystemTool
from .git import GitTool
from .python import PythonTool
from .search import SearchTool
from .terminal import TerminalTool
from .web import WebTool


def builtin_tools() -> tuple[BaseTool, ...]:
    """Return default built-in tools."""

    return (
        TerminalTool(),
        FilesystemTool(),
        GitTool(),
        PythonTool(),
        DockerTool(),
        SearchTool(),
        WebTool(),
        ArchiveTool(),
    )


__all__ = [
    "ArchiveTool",
    "BaseTool",
    "DockerTool",
    "FilesystemTool",
    "GitTool",
    "PythonTool",
    "SearchTool",
    "TerminalTool",
    "ToolExecutionRequest",
    "ToolExecutionResult",
    "WebTool",
    "builtin_tools",
]
