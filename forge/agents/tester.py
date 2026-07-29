"""Testing agent for validation planning and execution guidance."""

from __future__ import annotations

from dataclasses import dataclass, field

from .base import BaseAgent


@dataclass(frozen=True)
class TestReport:
    """Suggested validation plan for a task."""

    summary: str
    commands: list[str] = field(default_factory=list)
    checks: list[str] = field(default_factory=list)
    focus_areas: list[str] = field(default_factory=list)


class TestAgent(BaseAgent):
    """Agent responsible for test and validation guidance."""

    @property
    def supported_task_types(self) -> tuple[str, ...]:
        return ("test",)

    @property
    def keywords(self) -> tuple[str, ...]:
        return ("test", "validate", "verify", "coverage")

    @property
    def name(self) -> str:
        return "TestAgent"

    @property
    def description(self) -> str:
        return (
            "Plan validation, recommend test commands, and identify behavioral "
            "checks for a requested change."
        )

    def run(self, prompt: str, **kwargs: object) -> TestReport:
        request = prompt.strip() or "current change"
        lowered = request.lower()
        focus_areas = ["unit coverage", "regression safety"]
        if "memory" in lowered:
            focus_areas.append("persistence behavior")
        if "orchestr" in lowered or "scheduler" in lowered:
            focus_areas.append("dependency and concurrency behavior")
        if "git" in lowered:
            focus_areas.append("workflow metadata")

        checks = [
            "Verify success and failure paths.",
            "Confirm dependency ordering is preserved.",
        ]
        if "retry" in lowered:
            checks.append("Exercise retry exhaustion and recovery paths.")

        return TestReport(
            summary=f"Validation plan for {request}.",
            commands=["python -m pytest -q"],
            checks=checks,
            focus_areas=focus_areas,
        )
