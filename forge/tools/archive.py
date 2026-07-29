"""Archive tool for zip create/extract operations."""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Any

from ..runtime.models import ToolContext, ToolExecutionResult
from .base import RuntimeTool


class ArchiveTool(RuntimeTool):
    @property
    def name(self) -> str:
        return "archive"

    @property
    def capabilities(self) -> tuple[str, ...]:
        return ("archive.create", "archive.extract")

    def execute(self, payload: dict[str, Any], context: ToolContext) -> ToolExecutionResult:
        operation = str(payload.get("operation", "")).lower()

        if operation == "create":
            source = Path(str(payload.get("source", "")))
            destination = Path(str(payload.get("destination", "")))
            if not source.exists():
                return ToolExecutionResult(
                    success=False, error=f"Source path does not exist: {source}"
                )
            destination.parent.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                if source.is_file():
                    archive.write(source, arcname=source.name)
                else:
                    for item in source.rglob("*"):
                        if item.is_file():
                            archive.write(item, arcname=item.relative_to(source))
            return ToolExecutionResult(success=True, output=str(destination))

        if operation == "extract":
            source = Path(str(payload.get("source", "")))
            destination = Path(str(payload.get("destination", "")))
            destination.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(source, "r") as archive:
                archive.extractall(destination)
            return ToolExecutionResult(success=True, output=str(destination))

        return ToolExecutionResult(
            success=False, error=f"Unsupported archive operation: {operation}"
        )
