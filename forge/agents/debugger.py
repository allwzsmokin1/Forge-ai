"""Debugging agent for failure analysis and remediation guidance."""

from __future__ import annotations

from dataclasses import dataclass

from .base import BaseAgent


@dataclass(frozen=True)
class DebugReport:
    """Represents a debugging recommendation."""

    issue: str
    root_cause: str
    next_step: str


class DebugAgent(BaseAgent):
    """Agent responsible for analyzing failures and suggesting remediations."""

    @property
    def name(self) -> str:
        return "DebugAgent"

    @property
    def description(self) -> str:
        return "Analyze failures, identify likely root causes, and suggest next steps."

    def run(self, prompt: str, **kwargs: object) -> DebugReport:
        issue = prompt.strip() or "Unknown failure"
        return DebugReport(
            issue=issue,
            root_cause="The task requires additional inspection of the failing inputs or dependencies.",
            next_step="Review the failing task output, validate dependencies, and retry with corrected inputs.",
        )
