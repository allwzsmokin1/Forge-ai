"""Documentation agent for generating module and API documentation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .base import BaseAgent


@dataclass(frozen=True)
class DocumentationArtifact:
    """Represents generated documentation for a module, class, or function."""

    subject: str
    summary: str
    sections: list[str] = field(default_factory=list)
    format: str = "markdown"


class DocumentationAgent(BaseAgent):
    """Agent responsible for producing documentation from code or descriptions."""

    @property
    def name(self) -> str:
        return "DocumentationAgent"

    @property
    def description(self) -> str:
        return (
            "Generate module-level, class-level, and function-level documentation "
            "from Python source code or plain descriptions."
        )

    def run(self, prompt: str, **kwargs: Any) -> DocumentationArtifact:
        """Produce documentation for the supplied code or description.

        Args:
            prompt: Python code or a textual description of the component.
            **kwargs: Extra context such as ``task`` from the orchestrator.

        Returns:
            A DocumentationArtifact with structured documentation sections.
        """
        subject = prompt.strip()
        if not subject:
            return DocumentationArtifact(
                subject="",
                summary="No subject provided for documentation.",
                sections=[],
            )

        summary = self._generate_summary(subject)
        sections = self._generate_sections(subject)
        return DocumentationArtifact(
            subject=subject[:80],
            summary=summary,
            sections=sections,
            format="markdown",
        )

    def _generate_summary(self, subject: str) -> str:
        lowered = subject.lower()
        if "class " in lowered:
            return "This class provides structured functionality for the described purpose."
        if "def " in lowered or "async def" in lowered:
            return "This function implements the described behavior with typed inputs and outputs."
        if "module" in lowered or "package" in lowered:
            return "This module exposes utilities and abstractions for its described domain."
        return f"Documentation for: {subject[:60]}"

    def _generate_sections(self, subject: str) -> list[str]:
        lowered = subject.lower()
        sections: list[str] = []

        sections.append("## Overview\n\nDescribes the purpose and responsibility of this component.")

        if "def " in lowered or "async def" in lowered:
            sections.append(
                "## Parameters\n\n"
                "| Name | Type | Description |\n"
                "|------|------|-------------|\n"
                "| prompt | str | Input text or code snippet |"
            )
            sections.append(
                "## Returns\n\nReturns a structured result appropriate for the component type."
            )
            sections.append(
                "## Raises\n\n- `ValueError` — if required inputs are missing or malformed."
            )

        if "class " in lowered:
            sections.append(
                "## Attributes\n\nLists the public attributes and their types."
            )
            sections.append(
                "## Methods\n\nDescribes the public interface methods."
            )

        sections.append(
            "## Example\n\n```python\n# Example usage\n# result = component.run(prompt)\n```"
        )

        if "async" in lowered or "await" in lowered:
            sections.append(
                "## Async Notes\n\n"
                "This component contains async code. Ensure callers use `await` "
                "and run within an active event loop."
            )

        return sections
