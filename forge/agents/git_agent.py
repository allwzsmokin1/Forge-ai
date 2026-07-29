"""Git agent for composing commit messages, changelogs, and branch advice."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .base import BaseAgent


@dataclass(frozen=True)
class GitArtifact:
    """Represents the output of a git-related task."""

    action: str
    commit_message: str = ""
    branch_name: str = ""
    changelog_entry: str = ""
    advice: list[str] = field(default_factory=list)


class GitAgent(BaseAgent):
    """Agent responsible for git-related tasks such as commit messages and changelogs."""

    @property
    def name(self) -> str:
        return "GitAgent"

    @property
    def description(self) -> str:
        return (
            "Compose semantic commit messages, suggest branch names, generate "
            "changelog entries, and provide git workflow advice."
        )

    def run(self, prompt: str, **kwargs: Any) -> GitArtifact:
        """Handle a git-related request.

        Args:
            prompt: Description of the change or git workflow question.
            **kwargs: Extra context such as ``task`` from the orchestrator.

        Returns:
            A GitArtifact with structured git guidance.
        """
        request = prompt.strip()
        if not request:
            return GitArtifact(
                action="none",
                advice=["No request provided. Supply a change description."],
            )

        lowered = request.lower()
        action = self._classify_action(lowered)

        return GitArtifact(
            action=action,
            commit_message=self._compose_commit_message(action, request),
            branch_name=self._suggest_branch(action, request),
            changelog_entry=self._compose_changelog(action, request),
            advice=self._build_advice(action, lowered),
        )

    def _classify_action(self, lowered: str) -> str:
        if "fix" in lowered or "bug" in lowered or "patch" in lowered:
            return "fix"
        if "refactor" in lowered:
            return "refactor"
        if "doc" in lowered or "readme" in lowered or "comment" in lowered:
            return "docs"
        if "test" in lowered:
            return "test"
        if "chore" in lowered or "ci" in lowered or "config" in lowered:
            return "chore"
        if "feat" in lowered or "feature" in lowered or "add" in lowered:
            return "feat"
        return "feat"

    def _compose_commit_message(self, action: str, request: str) -> str:
        summary = request[:72].strip().rstrip(".")
        first_line = summary.split("\n")[0]
        return f"{action}: {first_line.lower()}"

    def _suggest_branch(self, action: str, request: str) -> str:
        slug = "".join(
            ch if ch.isalnum() else "-" for ch in request[:40].lower()
        ).strip("-")
        slug = "-".join(part for part in slug.split("-") if part)
        return f"{action}/{slug}"

    def _compose_changelog(self, action: str, request: str) -> str:
        summary = request[:100].strip().rstrip(".")
        tag_map = {
            "feat": "Added",
            "fix": "Fixed",
            "refactor": "Changed",
            "docs": "Documentation",
            "test": "Tests",
            "chore": "Chore",
        }
        tag = tag_map.get(action, "Changed")
        return f"- **{tag}**: {summary}"

    def _build_advice(self, action: str, lowered: str) -> list[str]:
        advice: list[str] = [
            "Keep commit messages concise (≤72 chars for the subject line).",
            "Use the imperative mood: 'fix bug' not 'fixed bug'.",
        ]
        if action == "feat":
            advice.append("Consider opening a feature branch from the default branch.")
        if action == "fix":
            advice.append("Reference the issue number in the commit body when available.")
        if "merge" in lowered:
            advice.append("Prefer rebase over merge for a cleaner linear history.")
        return advice
