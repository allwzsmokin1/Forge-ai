"""Documentation agent for generating concise project guidance."""

from __future__ import annotations

from dataclasses import dataclass

from .base import BaseAgent


@dataclass(frozen=True)
class DocumentationArtifact:
    """Represents documentation guidance for a task."""

    title: str
    summary: str
    sections: tuple[str, ...]


class DocumentationAgent(BaseAgent):
    """Agent responsible for preparing documentation-oriented outputs."""

    @property
    def name(self) -> str:
        return "DocumentationAgent"

    @property
    def description(self) -> str:
        return "Summarize implementation changes and outline documentation updates."

    def run(self, prompt: str, **kwargs: object) -> DocumentationArtifact:
        request = prompt.strip() or "general change"
        return DocumentationArtifact(
            title=request[:80],
            summary=f"Document the purpose, behavior, and validation steps for: {request}",
            sections=("Overview", "Architecture", "Validation"),
        )
