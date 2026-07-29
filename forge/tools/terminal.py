"""Terminal command execution tool."""

from __future__ import annotations

import subprocess

from .base import BaseTool, ToolExecutionRequest, ToolExecutionResult


class TerminalTool(BaseTool):
    name = "terminal"
    description = "Execute shell commands with captured output."
    capabilities = ("terminal", "command-execution")
    required_permissions = ("tool:terminal",)

    def execute(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        if request.action != "run":
            return self._error(f"Unsupported terminal action: {request.action}")

        payload = request.payload
        command = payload.get("command")
        if not command:
            return self._error("'command' is required")

        shell = bool(payload.get("shell", isinstance(command, str)))
        cwd = payload.get("cwd")
        timeout = payload.get("timeout")

        completed = subprocess.run(
            command,
            shell=shell,
            cwd=cwd,
            timeout=timeout,
            capture_output=True,
            text=True,
            check=False,
        )
        success = completed.returncode == 0
        return ToolExecutionResult(
            success=success,
            data={
                "command": command,
                "returncode": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            },
            error=None if success else f"Command failed with exit code {completed.returncode}",
        )
