"""Git workflow agent."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .base import BaseAgent


@dataclass(frozen=True)
class GitPlan:
    """Git-oriented handoff guidance."""

    branch_name: str
    commit_message: str
    actions: list[str] = field(default_factory=list)


class GitAgent(BaseAgent):
    """Agent responsible for branch and commit guidance."""

    @property
    def supported_task_types(self) -> tuple[str, ...]:
        return ("git",)

    @property
    def keywords(self) -> tuple[str, ...]:
        return ("git", "branch", "commit", "release")

    @property
    def name(self) -> str:
        return "GitAgent"

    @property
    def description(self) -> str:
        return (
            "Prepare git-ready branch naming, commit messages, and release handoff "
            "steps for completed work."
        )

    def run(self, prompt: str, **kwargs: object) -> GitPlan:
        request = prompt.strip() or "current change"
        slug = re.sub(r"[^a-z0-9]+", "-", request.lower()).strip("-") or "update"
        branch_name = f"forge/{slug[:40]}"
        commit_message = f"Deliver {slug[:50].replace('-', ' ')}".strip()
        return GitPlan(
            branch_name=branch_name,
            commit_message=commit_message,
            actions=[
                "Review the final diff.",
                "Run validation before committing.",
                "Prepare a concise summary for the pull request.",
            ],
        )
