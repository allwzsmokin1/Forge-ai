"""Git workflow agent for summarizing repository actions."""

from __future__ import annotations

from dataclasses import dataclass

from .base import BaseAgent


@dataclass(frozen=True)
class GitAction:
    """Represents a suggested git-oriented action."""

    summary: str
    recommended_branch_action: str
    ready_to_commit: bool


class GitAgent(BaseAgent):
    """Agent responsible for summarizing git workflow follow-up actions."""

    @property
    def name(self) -> str:
        return "GitAgent"

    @property
    def description(self) -> str:
        return "Summarize commit readiness and recommended git workflow actions."

    def run(self, prompt: str, **kwargs: object) -> GitAction:
        request = prompt.strip() or "repository update"
        runtime_summary = ""
        tool_result = self.request_tool(
            capability="git",
            action="status",
            payload={"cwd": kwargs.get("cwd")},
        )
        if tool_result and tool_result.success and isinstance(tool_result.data, dict):
            stdout = str(tool_result.data.get("stdout", "")).strip()
            runtime_summary = (
                f" Current git status:\n{stdout}" if stdout else " Working tree is clean."
            )
        elif tool_result and tool_result.error:
            runtime_summary = f" Runtime git check unavailable ({tool_result.error})."

        return GitAction(
            summary=f"Prepare repository changes for: {request}.{runtime_summary}",
            recommended_branch_action="Review the diff and create a focused commit once validation passes.",
            ready_to_commit=True,
        )
