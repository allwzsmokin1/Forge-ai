"""Docker CLI wrapper tool."""

from __future__ import annotations

import subprocess

from .base import BaseTool, ToolExecutionRequest, ToolExecutionResult


class DockerTool(BaseTool):
    name = "docker"
    description = "Run Docker CLI commands when available."
    capabilities = ("docker", "containerization")
    required_permissions = ("tool:docker",)

    def execute(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        args = request.payload.get("args", [])
        if request.action != "run":
            return self._error(f"Unsupported docker action: {request.action}")

        completed = subprocess.run(
            ["docker", *args], capture_output=True, text=True, check=False
        )
        success = completed.returncode == 0
        return ToolExecutionResult(
            success=success,
            data={"stdout": completed.stdout, "stderr": completed.stderr, "args": args},
            error=None if success else f"Docker command failed with exit code {completed.returncode}",
        )

    def health_check(self) -> ToolExecutionResult:
        completed = subprocess.run(["docker", "--version"], capture_output=True, text=True, check=False)
        return ToolExecutionResult(
            success=completed.returncode == 0,
            data={"stdout": completed.stdout.strip(), "stderr": completed.stderr.strip()},
            error=None if completed.returncode == 0 else "Docker not available",
        )
