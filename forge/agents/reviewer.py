"""Reviewer agent for identifying issues and recommending improvements."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .base import BaseAgent


@dataclass(frozen=True)
class ReviewFinding:
    """Represents a review finding with severity and an actionable suggestion."""

    issue: str
    severity: str
    suggestion: str


class ReviewerAgent(BaseAgent):
    """Agent responsible for reviewing Python code and surfacing potential issues."""

    @property
    def name(self) -> str:
        return "ReviewerAgent"

    @property
    def description(self) -> str:
        return (
            "Review Python code to find bugs, suggest improvements, and return "
            "severity levels for each finding."
        )

    def run(self, prompt: str, **kwargs: object) -> List[ReviewFinding]:
        """Review code and return a list of findings.

        The reviewer applies basic static heuristics to identify security risks,
        style issues, and opportunities for improvement.
        """
        if kwargs.get("runtime_probe"):
            self.request_tool(
                tool="python",
                capability="python.exec",
                payload={"code": "print('runtime_probe')"},
            )
        code = prompt.strip()
        if not code:
            return [
                ReviewFinding(
                    issue="No code provided",
                    severity="high",
                    suggestion="Supply Python code to review.",
                )
            ]

        findings: List[ReviewFinding] = []
        findings.extend(self._find_security_issues(code))
        findings.extend(self._find_style_issues(code))
        return findings

    def _find_security_issues(self, code: str) -> List[ReviewFinding]:
        findings: List[ReviewFinding] = []
        if "eval(" in code or "exec(" in code:
            findings.append(
            ReviewFinding(
                issue="Use of eval/exec",
                severity="high",
                suggestion=(
                    "Avoid eval and exec in production code. Use safe parsing or "
                    "explicit logic instead."
                ),
            )
        )
        return findings

    def _find_style_issues(self, code: str) -> List[ReviewFinding]:
        findings: List[ReviewFinding] = []
        if "TODO" in code:
            findings.append(
                ReviewFinding(
                    issue="Unresolved TODO comment",
                    severity="low",
                    suggestion="Replace TODO comments with completed implementation or a tracked issue."
                )
            )
        if "print(" in code and "if __name__" not in code:
            findings.append(
                ReviewFinding(
                    issue="Top-level print statement",
                    severity="medium",
                    suggestion=(
                        "Avoid top-level print statements in reusable modules. "
                        "Wrap example execution in a main guard."
                    ),
                )
            )
        if "def " in code and "\"\"\"" not in code:
            findings.append(
                ReviewFinding(
                    issue="Missing docstring",
                    severity="low",
                    suggestion="Add a module or function docstring to improve maintainability."
                )
            )
        return findings
