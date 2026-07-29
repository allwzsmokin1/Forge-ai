"""Terminal tool for Forge runtime."""

from __future__ import annotations

import subprocess
from typing import Any

from ..runtime import RuntimeContext, ToolExecutionRequest, ToolExecutionResult
from .base import BaseTool


class TerminalTool(BaseTool):
    """Execute shell commands through a single runtime interface."""

    capabilities = ("terminal", "process")

    @property
    def name(self) -> str:
        return "terminal"

    @property
    def description(self) -> str:
        return "Run shell commands and capture their output."

    def execute(
        self,
        request: ToolExecutionRequest,
        context: RuntimeContext,
    ) -> ToolExecutionResult:
        if request.operation != "run":
            raise ValueError(f"Unsupported terminal operation: {request.operation}")

        payload = request.payload
        completed = subprocess.run(
            payload["command"],
            cwd=payload.get("cwd"),
            env=payload.get("env"),
            shell=payload.get("shell", False),
            capture_output=payload.get("capture_output", True),
            text=payload.get("text", True),
            timeout=request.timeout,
            check=payload.get("check", True),
        )
        output: Any = {
            "args": completed.args,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
        return ToolExecutionResult(tool_name=self.name, success=True, output=output)
