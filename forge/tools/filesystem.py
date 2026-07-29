"""Filesystem tool for runtime-controlled file operations."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from ..runtime.models import ToolContext, ToolExecutionResult
from .base import RuntimeTool


class FilesystemTool(RuntimeTool):
    @property
    def name(self) -> str:
        return "filesystem"

    @property
    def capabilities(self) -> tuple[str, ...]:
        return ("filesystem.read", "filesystem.write", "filesystem.list", "filesystem.delete")

    def execute(self, payload: dict[str, Any], context: ToolContext) -> ToolExecutionResult:
        operation = str(payload.get("operation", "")).lower()
        path = Path(str(payload.get("path", "")))

        if operation == "read":
            if not path.exists():
                return ToolExecutionResult(success=False, error=f"Path does not exist: {path}")
            return ToolExecutionResult(success=True, output=path.read_text(encoding="utf-8"))

        if operation == "write":
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(str(payload.get("content", "")), encoding="utf-8")
            return ToolExecutionResult(success=True, output=str(path))

        if operation == "list":
            if not path.exists() or not path.is_dir():
                return ToolExecutionResult(success=False, error=f"Directory does not exist: {path}")
            entries = sorted(item.name for item in path.iterdir())
            return ToolExecutionResult(success=True, output=entries)

        if operation == "delete":
            if path.is_dir():
                shutil.rmtree(path)
            elif path.exists():
                path.unlink()
            return ToolExecutionResult(success=True, output=str(path))

        return ToolExecutionResult(
            success=False, error=f"Unsupported filesystem operation: {operation}"
        )
