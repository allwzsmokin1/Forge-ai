"""Terminal tool for running subprocess commands via runtime."""

from __future__ import annotations

import shutil
import subprocess
from typing import Any

from ..runtime.models import HealthCheckResult, ToolContext, ToolExecutionResult
from .base import RuntimeTool


class TerminalTool(RuntimeTool):
    @property
    def name(self) -> str:
        return "terminal"

    @property
    def capabilities(self) -> tuple[str, ...]:
        return ("terminal.execute",)

    def execute(self, payload: dict[str, Any], context: ToolContext) -> ToolExecutionResult:
        command = str(payload.get("command", "")).strip()
        if not command:
            return ToolExecutionResult(success=False, error="Missing command")

        completed = subprocess.run(
            command,
            shell=True,
            check=False,
            text=True,
            capture_output=True,
            cwd=payload.get("cwd"),
            timeout=payload.get("timeout"),
        )
        return ToolExecutionResult(
            success=completed.returncode == 0,
            output={"stdout": completed.stdout, "stderr": completed.stderr},
            error=(
                None if completed.returncode == 0 else f"Command failed with {completed.returncode}"
            ),
            metadata={"returncode": completed.returncode, "agent": context.agent},
        )

    def health_check(self) -> HealthCheckResult:
        return HealthCheckResult(name=self.name, healthy=shutil.which("sh") is not None, details={})
