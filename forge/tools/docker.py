"""Docker tool for runtime-managed docker CLI invocations."""

from __future__ import annotations

import shutil
import subprocess
from typing import Any

from ..runtime.models import HealthCheckResult, ToolContext, ToolExecutionResult
from .base import RuntimeTool


class DockerTool(RuntimeTool):
    @property
    def name(self) -> str:
        return "docker"

    @property
    def capabilities(self) -> tuple[str, ...]:
        return ("docker.command", "docker.ps")

    def execute(self, payload: dict[str, Any], context: ToolContext) -> ToolExecutionResult:
        args = payload.get("args", ["ps"])
        if shutil.which("docker") is None:
            return ToolExecutionResult(success=False, error="docker binary not available")
        if not isinstance(args, list) or not all(isinstance(arg, str) for arg in args):
            return ToolExecutionResult(success=False, error="args must be a list of strings")

        completed = subprocess.run(
            ["docker", *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=payload.get("timeout"),
        )
        return ToolExecutionResult(
            success=completed.returncode == 0,
            output={"stdout": completed.stdout, "stderr": completed.stderr},
            error=None if completed.returncode == 0 else f"docker exited with {completed.returncode}",
            metadata={"returncode": completed.returncode},
        )

    def health_check(self) -> HealthCheckResult:
        return HealthCheckResult(
            name=self.name,
            healthy=shutil.which("docker") is not None,
            details={},
        )
