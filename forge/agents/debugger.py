"""Debugging agent for failed task analysis."""

from __future__ import annotations

from dataclasses import dataclass, field

from .base import BaseAgent


@dataclass(frozen=True)
class DebugReport:
    """Diagnosis for a failed task."""

    issue: str
    suspected_causes: list[str] = field(default_factory=list)
    recommended_actions: list[str] = field(default_factory=list)


class DebugAgent(BaseAgent):
    """Agent responsible for retry guidance after task failures."""

    @property
    def supported_task_types(self) -> tuple[str, ...]:
        return ("debug",)

    @property
    def keywords(self) -> tuple[str, ...]:
        return ("debug", "failure", "error", "retry")

    @property
    def name(self) -> str:
        return "DebugAgent"

    @property
    def description(self) -> str:
        return (
            "Diagnose failed tasks, propose likely causes, and recommend targeted " "retry actions."
        )

    def run(self, prompt: str, **kwargs: object) -> DebugReport:
        issue = kwargs.get("error")
        issue_text = str(issue or prompt or "Unknown failure").strip()
        lowered = issue_text.lower()

        suspected_causes = ["Inspect task inputs and intermediate state."]
        recommended_actions = ["Retry after addressing the most likely root cause."]

        if "timeout" in lowered:
            suspected_causes.append("The task may require more time or smaller work units.")
            recommended_actions.append("Increase timeout or decompose the task further.")
        if "dependency" in lowered or "blocked" in lowered:
            suspected_causes.append("A prerequisite task likely failed or never completed.")
            recommended_actions.append("Repair upstream tasks before retrying this task.")
        if "assert" in lowered or "test" in lowered:
            suspected_causes.append("Behavior diverged from expectations under test.")
            recommended_actions.append("Compare expected and actual outputs before rerunning.")

        return DebugReport(
            issue=issue_text,
            suspected_causes=suspected_causes,
            recommended_actions=recommended_actions,
        )
