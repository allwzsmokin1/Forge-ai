"""Research agent for gathering documentation and recommending best practices."""

from __future__ import annotations

from dataclasses import dataclass

from ..llm import registry
from .base import BaseAgent

FINDINGS_PREFIX = "FINDINGS:\n"
RECOMMENDATIONS_DELIMITER = "\nRECOMMENDATIONS:\n"


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
        source_url = kwargs.get("source_url")
        if isinstance(source_url, str) and source_url.strip():
            self.request_tool(
                tool="web",
                capability="web.fetch",
                payload={"url": source_url.strip(), "timeout": 5},
            )
        response = registry.get().generate(topic, task_type="research")
        findings, _, recommendations = response.text.partition(RECOMMENDATIONS_DELIMITER)
        normalized_findings = findings.removeprefix(FINDINGS_PREFIX).strip()
        return ResearchSummary(
            topic=topic,
            findings=normalized_findings,
            recommendations=recommendations.strip(),
        )
