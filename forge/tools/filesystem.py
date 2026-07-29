"""Filesystem tool for Forge runtime."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..runtime import RuntimeContext, ToolExecutionRequest, ToolExecutionResult, ToolHealthStatus
from .base import BaseTool


class FilesystemTool(BaseTool):
    """Provide controlled filesystem operations."""

    capabilities = ("filesystem",)

    @property
    def name(self) -> str:
        return "filesystem"

    @property
    def description(self) -> str:
        return "Read, write, create, inspect, and list filesystem paths."

    def execute(
        self,
        request: ToolExecutionRequest,
        context: RuntimeContext,
    ) -> ToolExecutionResult:
        operation = request.operation
        payload = request.payload

        if operation == "mkdir":
            path = Path(payload["path"])
            path.mkdir(
                parents=payload.get("parents", False),
                exist_ok=payload.get("exist_ok", False),
            )
            output: Any = str(path)
        elif operation == "write_text":
            path = Path(payload["path"])
            if payload.get("create_parents", True):
                path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(payload["content"], encoding=payload.get("encoding", "utf-8"))
            output = str(path)
        elif operation == "read_text":
            path = Path(payload["path"])
            output = path.read_text(encoding=payload.get("encoding", "utf-8"))
        elif operation == "exists":
            output = Path(payload["path"]).exists()
        elif operation == "is_dir":
            output = Path(payload["path"]).is_dir()
        elif operation == "listdir":
            path = Path(payload["path"])
            output = sorted(child.name for child in path.iterdir())
        else:
            raise ValueError(f"Unsupported filesystem operation: {operation}")

        return ToolExecutionResult(tool_name=self.name, success=True, output=output)

    def health_check(self, context: RuntimeContext) -> ToolHealthStatus:
        return ToolHealthStatus(tool_name=self.name, healthy=True, details={"status": "ok"})
