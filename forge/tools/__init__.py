"""Built-in Forge runtime tools."""

from .archive import ArchiveTool
from .base import BaseTool
from .docker import DockerTool
from .filesystem import FilesystemTool
from .git import GitTool
from .python import PythonTool
from .search import SearchTool
from .terminal import TerminalTool
from .web import WebTool


def register_builtin_tools(registry: object) -> None:
    """Register the built-in runtime tools."""

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


__all__ = [
    "ArchiveTool",
    "BaseTool",
    "DockerTool",
    "FilesystemTool",
    "GitTool",
    "PythonTool",
    "SearchTool",
    "TerminalTool",
    "WebTool",
    "register_builtin_tools",
]
