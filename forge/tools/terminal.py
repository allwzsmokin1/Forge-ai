"""Terminal tool for Forge runtime."""

from __future__ import annotations

import subprocess
from typing import Any

from ..runtime import RuntimeContext, ToolExecutionRequest, ToolExecutionResult
from .base import BaseTool

SENSITIVE_COMMANDS = {
    "chmod",
    "chown",
    "dd",
    "mkfs",
    "poweroff",
    "reboot",
    "rm",
    "shutdown",
    "sudo",
}


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
        command = payload["command"]
        self._validate_command(command, payload)
        completed = subprocess.run(
            command,
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

    def _validate_command(self, command: Any, payload: dict[str, Any]) -> None:
        shell = payload.get("shell", False)
        if shell:
            raise PermissionError("Shell execution is disabled for the terminal tool")

        if isinstance(command, str):
            raise TypeError("Terminal commands must be tokenized sequences, not raw strings")

        if not command:
            raise ValueError("Terminal command payload cannot be empty")

        base_command = str(command[0]).strip()
        if not base_command:
            raise ValueError("Terminal command payload cannot start with an empty executable")

        if base_command in SENSITIVE_COMMANDS and not payload.get("allow_sensitive", False):
            raise PermissionError(
                f"Command '{base_command}' requires explicit allow_sensitive=True"
            )
