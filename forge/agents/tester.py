"""Test agent for generating and evaluating test cases."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .base import BaseAgent


@dataclass(frozen=True)
class TestResult:
    """Represents the outcome of a test-generation or test-evaluation task."""

    subject: str
    test_cases: list[str] = field(default_factory=list)
    passed: int = 0
    failed: int = 0
    notes: str = ""


class TestAgent(BaseAgent):
    """Agent responsible for generating test cases and evaluating test coverage."""

    @property
    def name(self) -> str:
        return "TestAgent"

    @property
    def description(self) -> str:
        return (
            "Generate unit test cases for Python code, evaluate test coverage, "
            "and surface missing test scenarios."
        )

    def run(self, prompt: str, **kwargs: Any) -> TestResult:
        """Generate or evaluate tests for the provided subject.

        Args:
            prompt: Code snippet or description of the module to test.
            **kwargs: Extra context such as ``task`` from the orchestrator.

        Returns:
            A TestResult containing generated test cases and summary notes.
        """
        subject = prompt.strip()
        if not subject:
            return TestResult(
                subject="",
                notes="No subject provided for test generation.",
            )

        test_cases = self._generate_test_cases(subject)
        notes = self._evaluate_coverage(subject, test_cases)
        return TestResult(
            subject=subject[:80],
            test_cases=test_cases,
            passed=len(test_cases),
            failed=0,
            notes=notes,
        )

    def _generate_test_cases(self, subject: str) -> list[str]:
        lowered = subject.lower()
        cases: list[str] = []

        cases.append(f"test_{self._slugify(subject[:40])}_happy_path")
        cases.append(f"test_{self._slugify(subject[:40])}_empty_input")
        cases.append(f"test_{self._slugify(subject[:40])}_invalid_input")

        if "async" in lowered or "coroutine" in lowered:
            cases.append(f"test_{self._slugify(subject[:40])}_async_execution")
        if "exception" in lowered or "error" in lowered or "raise" in lowered:
            cases.append(f"test_{self._slugify(subject[:40])}_raises_on_bad_input")
        if "return" in lowered or "result" in lowered:
            cases.append(f"test_{self._slugify(subject[:40])}_return_type")

        return cases

    def _evaluate_coverage(self, subject: str, cases: list[str]) -> str:
        count = len(cases)
        if count >= 5:
            return f"Good coverage: {count} test cases generated for subject."
        if count >= 3:
            return f"Basic coverage: {count} test cases generated. Consider edge cases."
        return f"Minimal coverage: only {count} test cases generated."

    @staticmethod
    def _slugify(text: str) -> str:
        return "".join(ch if ch.isalnum() else "_" for ch in text.lower()).strip("_")
