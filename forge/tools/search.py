"""Search tool for runtime-controlled text and file searching."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..runtime.models import ToolContext, ToolExecutionResult
from .base import RuntimeTool


class SearchTool(RuntimeTool):
    @property
    def name(self) -> str:
        return "search"

    @property
    def capabilities(self) -> tuple[str, ...]:
        return ("search.text", "search.files")

    def execute(self, payload: dict[str, Any], context: ToolContext) -> ToolExecutionResult:
        root = Path(str(payload.get("root", ".")))
        pattern = str(payload.get("pattern", "")).strip()
        if not pattern:
            return ToolExecutionResult(success=False, error="Missing pattern")

        glob_pattern = str(payload.get("glob", "**/*"))
        results: list[dict[str, Any]] = []
        for file_path in root.glob(glob_pattern):
            if not file_path.is_file():
                continue
            text = file_path.read_text(encoding="utf-8", errors="ignore")
            if pattern in text:
                results.append({"path": str(file_path), "matches": text.count(pattern)})

        return ToolExecutionResult(success=True, output=results)
