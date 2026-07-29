"""Python execution tool for Forge runtime."""

from __future__ import annotations

import sys

from ..runtime import RuntimeContext, ToolExecutionRequest, ToolExecutionResult
from .base import BaseTool


class PythonTool(BaseTool):
    """Execute Python code or modules through the runtime."""

    capabilities = ("python", "process")

    @property
    def name(self) -> str:
        return "python"

    @property
    def description(self) -> str:
        return "Run Python snippets, files, or modules."

    def execute(
        self,
        request: ToolExecutionRequest,
        context: RuntimeContext,
    ) -> ToolExecutionResult:
        if request.operation != "run":
            raise ValueError(f"Unsupported python operation: {request.operation}")

        payload = request.payload
        command = [sys.executable]
        if "code" in payload:
            command.extend(["-c", payload["code"]])
        elif "module" in payload:
            command.extend(["-m", payload["module"]])
            command.extend(payload.get("args", []))
        elif "script" in payload:
            command.append(payload["script"])
            command.extend(payload.get("args", []))
        else:
            raise ValueError("Python tool requires 'code', 'module', or 'script'")

        terminal = context.container.resolve("runtime_manager").registry.get("terminal")
        terminal_request = ToolExecutionRequest(
            tool_name="terminal",
            operation="run",
            payload={
                "command": command,
                "cwd": payload.get("cwd"),
                "env": payload.get("env"),
                "check": payload.get("check", True),
                "capture_output": payload.get("capture_output", True),
                "text": payload.get("text", True),
            },
            timeout=request.timeout,
        )
        result = terminal.execute(terminal_request, context)
        return ToolExecutionResult(tool_name=self.name, success=True, output=result.output)
