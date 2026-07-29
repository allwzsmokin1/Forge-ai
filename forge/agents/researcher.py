"""Research agent for gathering documentation and recommending best practices."""

from __future__ import annotations

from dataclasses import dataclass

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
        findings = (
            "This research summary synthesizes relevant documentation and best "
            "practices for the requested topic."
        )
        recommendations = (
            "Focus on typed interfaces, modular architecture, clear documentation, "
            "and incremental validation with tests."
        )

        if "async" in topic.lower():
            findings = (
                "Async code should use explicit task management and avoid blocking "
                "calls in event loops."
            )
            recommendations = (
                "Prefer asyncio-compatible libraries, document coroutine behavior, "
                "and use structured concurrency when possible."
            )

        return ResearchSummary(topic=topic, findings=findings, recommendations=recommendations)
