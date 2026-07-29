"""Documentation agent for update planning."""

from __future__ import annotations

from dataclasses import dataclass, field

from .base import BaseAgent


@dataclass(frozen=True)
class DocumentationArtifact:
    """Documentation guidance for a task."""

    summary: str
    sections: list[str] = field(default_factory=list)
    files_to_update: list[str] = field(default_factory=list)


class DocumentationAgent(BaseAgent):
    """Agent responsible for documentation planning."""

    @property
    def supported_task_types(self) -> tuple[str, ...]:
        return ("documentation",)

    @property
    def keywords(self) -> tuple[str, ...]:
        return ("document", "docs", "readme", "guide")

    @property
    def name(self) -> str:
        return "DocumentationAgent"

    @property
    def description(self) -> str:
        return (
            "Summarize user-facing changes, identify documentation sections, and "
            "suggest files to update."
        )

    def run(self, prompt: str, **kwargs: object) -> DocumentationArtifact:
        request = prompt.strip() or "current change"
        files_to_update = ["README.md"]
        task = kwargs.get("task")
        if task is not None and "files" in getattr(task, "metadata", {}):
            files_to_update.extend(str(path) for path in task.metadata["files"])

        return DocumentationArtifact(
            summary=f"Document the delivered behavior for {request}.",
            sections=["Architecture", "Execution Flow", "Validation"],
            files_to_update=list(dict.fromkeys(files_to_update)),
        )
