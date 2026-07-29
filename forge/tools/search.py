"""Search tool for Forge runtime."""

from __future__ import annotations

import re
from pathlib import Path

from ..runtime import RuntimeContext, ToolExecutionRequest, ToolExecutionResult
from .base import BaseTool


class SearchTool(BaseTool):
    """Search for files and file content."""

    capabilities = ("search", "filesystem")

    @property
    def name(self) -> str:
        return "search"

    @property
    def description(self) -> str:
        return "Search file paths or file content in local directories."

    def execute(
        self,
        request: ToolExecutionRequest,
        context: RuntimeContext,
    ) -> ToolExecutionResult:
        payload = request.payload
        base = Path(payload.get("path", "."))

        if request.operation == "glob":
            output = sorted(str(path) for path in base.glob(payload["pattern"]))
        elif request.operation == "grep":
            pattern = re.compile(payload["pattern"])
            matches: list[dict[str, object]] = []
            for file_path in base.rglob(payload.get("glob", "*")):
                if not file_path.is_file():
                    continue
                text = file_path.read_text(encoding=payload.get("encoding", "utf-8"))
                for line_number, line in enumerate(text.splitlines(), start=1):
                    if pattern.search(line):
                        matches.append(
                            {
                                "path": str(file_path),
                                "line_number": line_number,
                                "line": line,
                            }
                        )
            output = matches
        else:
            raise ValueError(f"Unsupported search operation: {request.operation}")

        return ToolExecutionResult(tool_name=self.name, success=True, output=output)
