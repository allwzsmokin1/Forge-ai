"""Git tool for runtime-managed repository operations."""

from __future__ import annotations

import shutil
import subprocess
from typing import Any

from ..runtime.models import HealthCheckResult, ToolContext, ToolExecutionResult
from .base import RuntimeTool


class GitTool(RuntimeTool):
    @property
    def name(self) -> str:
        return "git"

    @property
    def capabilities(self) -> tuple[str, ...]:
        return ("git.status", "git.diff", "git.command")

    def execute(self, payload: dict[str, Any], context: ToolContext) -> ToolExecutionResult:
        args = payload.get("args", ["status", "--short"])
        if not isinstance(args, list) or not all(isinstance(arg, str) for arg in args):
            return ToolExecutionResult(success=False, error="args must be a list of strings")

        completed = subprocess.run(
            ["git", *args],
            check=False,
            capture_output=True,
            text=True,
            cwd=payload.get("cwd"),
            timeout=payload.get("timeout"),
        )
        return ToolExecutionResult(
            success=completed.returncode == 0,
            output={"stdout": completed.stdout, "stderr": completed.stderr},
            error=None if completed.returncode == 0 else f"git exited with {completed.returncode}",
            metadata={"returncode": completed.returncode},
        )

    def health_check(self) -> HealthCheckResult:
        return HealthCheckResult(name=self.name, healthy=shutil.which("git") is not None, details={})
