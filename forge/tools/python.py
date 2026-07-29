"""Python execution tool."""

from __future__ import annotations

import subprocess
import sys

from .base import BaseTool, ToolExecutionRequest, ToolExecutionResult


class PythonTool(BaseTool):
    name = "python"
    description = "Execute Python snippets in a subprocess."
    capabilities = ("python", "code-execution")
    required_permissions = ("tool:python",)

    def execute(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        payload = request.payload
        action = request.action
        if action not in {"exec", "run_module"}:
            return self._error(f"Unsupported python action: {action}")

        if action == "exec":
            code = payload.get("code", "")
            command = [sys.executable, "-c", code]
        else:
            module = payload.get("module")
            if not module:
                return self._error("'module' is required for run_module")
            command = [sys.executable, "-m", module]

        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        success = completed.returncode == 0
        return ToolExecutionResult(
            success=success,
            data={"stdout": completed.stdout, "stderr": completed.stderr, "command": command},
            error=(
                None if success else f"Python command failed with exit code {completed.returncode}"
            ),
        )
