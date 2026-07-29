"""Research agent for gathering documentation and recommending best practices."""

from __future__ import annotations

from dataclasses import dataclass

from ..llm import registry
from .base import BaseAgent


@dataclass(frozen=True)
class ResearchSummary:
    """Represents a research summary with findings and recommendations."""

    topic: str
    findings: str
    recommendations: str


class ResearchAgent(BaseAgent):
    """Agent responsible for gathering documentation and summarizing best practices."""

    @property
    def name(self) -> str:
        return "ResearchAgent"

    @property
    def description(self) -> str:
        return (
            "Gather documentation, summarize findings, and recommend best practices "
            "for software engineering tasks."
        )

    def run(self, prompt: str, **kwargs: object) -> ResearchSummary:
        """Summarize the research topic and recommend best practices."""
        topic = prompt.strip() or "general software engineering"
        response = registry.get().generate(topic, task_type="research")
        findings, _, recommendations = response.text.partition("\nRECOMMENDATIONS:\n")
        return ResearchSummary(topic=topic, findings=findings, recommendations=recommendations)
