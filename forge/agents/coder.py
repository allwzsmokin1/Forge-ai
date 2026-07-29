"""Coder agent for generating and refactoring Python code."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..llm import registry
from .base import BaseAgent

CODE_PREFIX = "CODE:\n"
EXPLANATION_DELIMITER = "\nEXPLANATION:\n"


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
        return self._run_provider(request)

    def _refactor_code(self, request: str) -> CodeArtifact:
        return self._run_provider(request)

    def _explain_code(self, request: str) -> CodeArtifact:
        return self._run_provider(request)

    def _run_provider(self, request: str) -> CodeArtifact:
        response = registry.get().generate(request, task_type="coder")
        code, _, explanation = response.text.partition(EXPLANATION_DELIMITER)
        normalized_code = code.removeprefix(CODE_PREFIX).strip()
        return CodeArtifact(code=normalized_code, explanation=explanation.strip())
