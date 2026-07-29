"""Coder agent for generating and refactoring Python code."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .base import BaseAgent


@dataclass(frozen=True)
class CodeArtifact:
    """Represents generated or refactored code together with its explanation."""

    code: str
    explanation: str


class CoderAgent(BaseAgent):
    """Agent responsible for producing Python code and explanations."""

    @property
    def name(self) -> str:
        return "CoderAgent"

    @property
    def description(self) -> str:
        return (
            "Generate Python code, refactor existing code, and explain generated "
            "solutions in a developer-friendly way."
        )

    def run(self, prompt: str, **kwargs: Any) -> CodeArtifact:
        """Generate or refactor code in response to a prompt.

        This implementation applies simple heuristics to decide whether the user
        asked for code generation, refactoring, or explanation.
        """
        request = prompt.strip()
        if not request:
            return CodeArtifact(code="", explanation="No code request was provided.")

        lower_request = request.lower()
        if "refactor" in lower_request:
            return self._refactor_code(request)
        if "explain" in lower_request:
            return self._explain_code(request)

        return self._generate_code(request)

    def _generate_code(self, request: str) -> CodeArtifact:
        code = (
            "def hello_world() -> str:\n"
            "    \"\"\"Return a friendly greeting.\"\"\"\n"
            "    return 'Hello, world!'\n"
        )
        return CodeArtifact(
            code=code,
            explanation=(
                "Generated a simple Python function that returns a greeting. "
                "Use this as a starting point for more specific implementations."
            ),
        )

    def _refactor_code(self, request: str) -> CodeArtifact:
        code = (
            "def compute_total(prices: list[float]) -> float:\n"
            "    \"\"\"Return the sum of a list of prices.\"\"\"\n"
            "    return sum(prices)\n"
        )
        return CodeArtifact(
            code=code,
            explanation=(
                "Refactored the implementation to use Python's built-in sum function "
                "for readability and performance."
            ),
        )

    def _explain_code(self, request: str) -> CodeArtifact:
        explanation = (
            "This code example shows a well-typed Python function with a docstring, "
            "clear return type, and a simple implementation that is easy to read."
        )
        return CodeArtifact(code=request, explanation=explanation)
