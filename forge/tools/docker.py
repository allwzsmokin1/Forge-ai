"""Docker tool for Forge runtime."""

from __future__ import annotations

from ..runtime import RuntimeContext, ToolExecutionRequest, ToolExecutionResult
from .base import BaseTool


class DockerTool(BaseTool):
    """Run docker commands through the runtime."""

    capabilities = ("docker", "process")

    @property
    def name(self) -> str:
        return "docker"

    @property
    def description(self) -> str:
        return "Run docker commands and return structured command output."

    def execute(
        self,
        request: ToolExecutionRequest,
        context: RuntimeContext,
    ) -> ToolExecutionResult:
        if request.operation != "run":
            raise ValueError(f"Unsupported docker operation: {request.operation}")

        terminal = context.container.resolve("runtime_manager").registry.get("terminal")
        terminal_request = ToolExecutionRequest(
            tool_name="terminal",
            operation="run",
            payload={
                "command": ["docker", *request.payload.get("args", [])],
                "cwd": request.payload.get("cwd"),
                "env": request.payload.get("env"),
                "check": request.payload.get("check", True),
                "capture_output": request.payload.get("capture_output", True),
                "text": request.payload.get("text", True),
            },
            timeout=request.timeout,
        )
        result = terminal.execute(terminal_request, context)
        return ToolExecutionResult(tool_name=self.name, success=True, output=result.output)
