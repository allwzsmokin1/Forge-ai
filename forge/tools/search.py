"""Code and file search tool."""

from __future__ import annotations

import re
from pathlib import Path

from .base import BaseTool, ToolExecutionRequest, ToolExecutionResult


class SearchTool(BaseTool):
    name = "search"
    description = "Search files by glob or content pattern."
    capabilities = ("search", "discovery")
    required_permissions = ("tool:search",)

    def execute(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        payload = request.payload
        root = Path(payload.get("root", "."))

        if request.action == "glob":
            pattern = payload.get("pattern")
            if not pattern:
                return self._error("'pattern' is required")
            matches = sorted(str(path) for path in root.glob(pattern))
            return self._ok(matches)

        if request.action == "grep":
            pattern = payload.get("pattern")
            if not pattern:
                return self._error("'pattern' is required")
            compiled = re.compile(pattern)
            include = payload.get("include", "**/*")
            results: list[dict[str, object]] = []
            for file_path in root.glob(include):
                if not file_path.is_file():
                    continue
                try:
                    lines = file_path.read_text(encoding="utf-8").splitlines()
                except UnicodeDecodeError:
                    continue
                for line_no, line in enumerate(lines, start=1):
                    if compiled.search(line):
                        results.append(
                            {"path": str(file_path), "line": line_no, "text": line.strip()}
                        )
            return self._ok(results)

        return self._error(f"Unsupported search action: {request.action}")
