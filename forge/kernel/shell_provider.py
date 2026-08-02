"""ShellExecutionProvider — runs shell commands via subprocess.

This is the only ExecutionProvider shipped with the MVP. It wraps any shell
command in a subprocess, captures stdout/stderr, and returns a structured
ExecutionResult. No AI provider, routing, or plugin logic lives here.
"""

from __future__ import annotations

import shlex
import subprocess
import time

from .execution_provider import ExecutionProvider, ExecutionResult

# Commands that could cause irreversible system-level damage are blocked.
# This list is intentionally conservative; it is not a security boundary —
# it is a safety net against obvious accidental misuse.
_BLOCKED_PREFIXES: tuple[str, ...] = (
    "rm ",
    "rm\t",
    "sudo ",
    "sudo\t",
    "mkfs",
    "dd ",
    "dd\t",
    "> /dev/",
    ":(){ :|:& };:",  # fork bomb
)


def _is_safe(command: str) -> bool:
    """Return False if *command* starts with a blocked prefix."""
    stripped = command.strip()
    for prefix in _BLOCKED_PREFIXES:
        if stripped.startswith(prefix):
            return False
    return True


class ShellExecutionProvider(ExecutionProvider):
    """Execute a shell command as a subprocess and return structured output.

    Args:
        timeout: Maximum seconds to wait for the command to complete.
            Defaults to 30. Commands that exceed this limit are killed and
            the result carries exit_code=-1.
        shell: When True (default) the command string is passed directly to
            the shell. When False the command is split with ``shlex.split``
            and executed without a shell, which is safer for trusted input.
    """

    def __init__(self, timeout: float = 30.0, shell: bool = True) -> None:
        self._timeout = timeout
        self._shell = shell

    def execute(self, command: str) -> ExecutionResult:
        """Run *command* in a subprocess and return the result.

        Args:
            command: Shell command string to execute.

        Returns:
            An :class:`ExecutionResult` with captured stdout/stderr and timing.

        Raises:
            ValueError: If the command matches a blocked prefix.
        """
        if not _is_safe(command):
            raise ValueError(f"Command blocked for safety: {command!r}")

        args: str | list[str] = command if self._shell else shlex.split(command)
        start = time.perf_counter()
        try:
            proc = subprocess.run(
                args,
                shell=self._shell,
                capture_output=True,
                text=True,
                timeout=self._timeout,
                check=False,
            )
            duration_ms = (time.perf_counter() - start) * 1000
            return ExecutionResult(
                stdout=proc.stdout.strip(),
                stderr=proc.stderr.strip(),
                exit_code=proc.returncode,
                duration_ms=round(duration_ms, 2),
            )
        except subprocess.TimeoutExpired:
            duration_ms = (time.perf_counter() - start) * 1000
            return ExecutionResult(
                stdout="",
                stderr=f"Command timed out after {self._timeout}s",
                exit_code=-1,
                duration_ms=round(duration_ms, 2),
            )
