"""Git operations tool."""

from __future__ import annotations

import subprocess

from .base import BaseTool, ToolExecutionRequest, ToolExecutionResult


class GitTool(BaseTool):
    name = "git"
    description = "Run scoped git commands."
    capabilities = ("git", "version-control")
    required_permissions = ("tool:git",)

    def execute(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        payload = request.payload
        cwd = payload.get("cwd")
        action = request.action

        command_map = {
            "status": ["git", "status", "--short"],
            "branch": ["git", "branch", "--show-current"],
            "log": ["git", "log", "--oneline", "-n", str(payload.get("limit", 10))],
            "diff": ["git", "diff"],
            "run": ["git", *payload.get("args", [])],
        }
        command = command_map.get(action)
        if command is None:
            return self._error(f"Unsupported git action: {action}")

        completed = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
        success = completed.returncode == 0
        return ToolExecutionResult(
            success=success,
            data={"stdout": completed.stdout, "stderr": completed.stderr, "command": command},
            error=None if success else f"Git command failed with exit code {completed.returncode}",
        )
