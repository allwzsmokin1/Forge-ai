"""Testing agent for validating implementation readiness."""

from __future__ import annotations

from dataclasses import dataclass

from .base import BaseAgent


@dataclass(frozen=True)
class TestReport:
    """Represents a lightweight validation outcome."""

    passed: bool
    summary: str
    recommended_checks: tuple[str, ...]


class TestAgent(BaseAgent):
    """Agent responsible for validating that work is ready for verification."""

    @property
    def name(self) -> str:
        return "TestAgent"

    @property
    def description(self) -> str:
        return "Validate work items, suggest checks, and summarize testing readiness."

    def run(self, prompt: str, **kwargs: object) -> TestReport:
        request = prompt.strip()
        if not request:
            return TestReport(
                passed=False,
                summary="No test target was provided.",
                recommended_checks=("python -m pytest -q",),
            )

        recommended_checks = ("python -m pytest -q",)
        if "integration" in request.lower():
            recommended_checks = ("python -m pytest -q", "Run integration workflow coverage.")

        return TestReport(
            passed=True,
            summary=f"Prepared validation guidance for: {request}",
            recommended_checks=recommended_checks,
        )
