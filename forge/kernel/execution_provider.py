"""ExecutionProvider — the single adapter interface for the MVP kernel.

The Mission Director depends only on this ABC; the concrete implementation
(ShellExecutionProvider) is injected at construction time, keeping the kernel
testable without real subprocess calls.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Result value-object
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExecutionResult:
    """Structured result returned by every ExecutionProvider.

    Attributes:
        stdout:      Captured standard output (stripped).
        stderr:      Captured standard error (stripped).
        exit_code:   Process exit code; 0 indicates success.
        duration_ms: Wall-clock execution time in milliseconds.
    """

    stdout: str
    stderr: str
    exit_code: int
    duration_ms: float

    @property
    def succeeded(self) -> bool:
        return self.exit_code == 0


# ---------------------------------------------------------------------------
# Abstract base class
# ---------------------------------------------------------------------------


class ExecutionProvider(ABC):
    """Interface that every execution back-end must implement.

    The MVP ships with :class:`~forge.kernel.shell_provider.ShellExecutionProvider`.
    Future providers (Claude Code, OpenHands, …) implement this same interface
    and can be injected without touching the kernel.
    """

    @abstractmethod
    def execute(self, command: str) -> ExecutionResult:
        """Execute *command* and return a structured result.

        Args:
            command: The command string to execute.

        Returns:
            An :class:`ExecutionResult` with stdout, stderr, exit_code, and
            duration_ms populated.

        Raises:
            RuntimeError: If the provider encounters an unrecoverable error
                before the command can run.
        """

