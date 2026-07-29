"""Debug agent for analyzing errors and suggesting fixes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .base import BaseAgent


@dataclass(frozen=True)
class DebugReport:
    """Represents the output of a debugging analysis."""

    error_message: str
    root_cause: str
    suggestions: list[str] = field(default_factory=list)
    confidence: str = "medium"


class DebugAgent(BaseAgent):
    """Agent responsible for diagnosing errors and recommending corrective actions."""

    @property
    def name(self) -> str:
        return "DebugAgent"

    @property
    def description(self) -> str:
        return (
            "Debug Python errors: analyze error messages and stack traces, identify "
            "root causes, and propose concrete fix suggestions."
        )

    def run(self, prompt: str, **kwargs: Any) -> DebugReport:
        """Analyze an error and return a structured debug report.

        Args:
            prompt: An error message, exception text, or description of a bug.
            **kwargs: Extra context such as ``task`` from the orchestrator.

        Returns:
            A DebugReport with root-cause analysis and suggested fixes.
        """
        error_text = prompt.strip()
        if not error_text:
            return DebugReport(
                error_message="",
                root_cause="No error information provided.",
                suggestions=["Supply an error message or stack trace for analysis."],
                confidence="low",
            )

        root_cause = self._identify_root_cause(error_text)
        suggestions = self._build_suggestions(error_text, root_cause)
        confidence = self._assess_confidence(root_cause)

        return DebugReport(
            error_message=error_text[:200],
            root_cause=root_cause,
            suggestions=suggestions,
            confidence=confidence,
        )

    def _identify_root_cause(self, error: str) -> str:
        lowered = error.lower()
        if "nameerror" in lowered or "name '" in lowered:
            return "Undefined variable or name referenced before assignment."
        if "typeerror" in lowered:
            return "Type mismatch — an operation received an argument of an unexpected type."
        if "attributeerror" in lowered:
            return "Attribute access on None or a wrong object type."
        if "importerror" in lowered or "modulenotfounderror" in lowered:
            return "Missing or incorrectly named module import."
        if "keyerror" in lowered:
            return "Dictionary key not found; the key may be missing or misspelled."
        if "indexerror" in lowered:
            return "List or sequence index is out of range."
        if "valueerror" in lowered:
            return "A value passed to a function is of the right type but an inappropriate value."
        if "runtimeerror" in lowered:
            return "A runtime condition prevented execution from continuing."
        if "assertion" in lowered:
            return "An assertion check failed — a precondition or invariant was violated."
        if "timeout" in lowered or "timed out" in lowered:
            return "Operation exceeded its time limit; consider increasing timeout or optimizing."
        return "Unexpected error — review the full stack trace for context."

    def _build_suggestions(self, error: str, root_cause: str) -> list[str]:
        lowered = error.lower()
        suggestions: list[str] = []

        if "undefined" in root_cause or "nameerror" in lowered:
            suggestions.append("Check that the variable is defined before use.")
            suggestions.append("Verify spelling and scope of the variable name.")
        elif "type mismatch" in root_cause:
            suggestions.append("Add explicit type conversion or validation before the operation.")
            suggestions.append("Review the function signature for expected argument types.")
        elif "attribute" in root_cause:
            suggestions.append("Add a None check before accessing the attribute.")
            suggestions.append("Ensure the object is correctly initialized.")
        elif "import" in root_cause:
            suggestions.append("Verify the package is installed and listed in dependencies.")
            suggestions.append("Check for typos in the module name.")
        elif "key" in root_cause:
            suggestions.append("Use dict.get(key, default) to handle missing keys safely.")
            suggestions.append("Validate dictionary contents before access.")
        elif "index" in root_cause:
            suggestions.append("Guard list access with a length check.")
            suggestions.append("Consider using enumerate() and checking bounds.")
        else:
            suggestions.append("Review the stack trace to pinpoint the failing line.")
            suggestions.append("Add logging around the error site to capture state.")

        suggestions.append("Write a regression test to prevent recurrence.")
        return suggestions

    def _assess_confidence(self, root_cause: str) -> str:
        known_causes = {
            "Undefined variable",
            "Type mismatch",
            "Attribute access on None",
            "Missing or incorrectly named module",
            "Dictionary key not found",
            "List or sequence index",
            "A value passed to a function",
        }
        for cause in known_causes:
            if cause.lower() in root_cause.lower():
                return "high"
        return "medium"
