"""Python tool for executing local Python snippets in a subprocess."""

from __future__ import annotations

import shutil
import subprocess
import sys
from typing import Any

from ..runtime.models import HealthCheckResult, ToolContext, ToolExecutionResult
from .base import RuntimeTool


class PythonTool(RuntimeTool):
    @property
    def name(self) -> str:
        return "python"

    @property
    def capabilities(self) -> tuple[str, ...]:
        return ("python.exec",)

    def execute(self, payload: dict[str, Any], context: ToolContext) -> ToolExecutionResult:
        code = str(payload.get("code", ""))
        if not code.strip():
            return ToolExecutionResult(success=False, error="Missing code")

        completed = subprocess.run(
            [sys.executable, "-c", code],
            check=False,
            capture_output=True,
            text=True,
            cwd=payload.get("cwd"),
            timeout=payload.get("timeout"),
        )
        return ToolExecutionResult(
            success=completed.returncode == 0,
            output={"stdout": completed.stdout, "stderr": completed.stderr},
            error=None if completed.returncode == 0 else f"python exited with {completed.returncode}",
            metadata={"returncode": completed.returncode},
        )

    def health_check(self) -> HealthCheckResult:
        return HealthCheckResult(name=self.name, healthy=shutil.which("python") is not None, details={})
