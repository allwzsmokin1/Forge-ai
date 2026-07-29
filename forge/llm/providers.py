"""LLM provider abstractions and built-in provider implementations."""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class LLMResponse:
    """Represents a normalized response from an LLM provider."""

    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class LLMProvider(abc.ABC):
    """Abstract base class for LLM providers."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def description(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        raise NotImplementedError


class MockLLMProvider(LLMProvider):
    """A deterministic local provider for offline testing and default usage."""

    @property
    def name(self) -> str:
        return "mock"

    @property
    def description(self) -> str:
        return "Local mock provider used for tests and offline development."

    def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        if not prompt.strip():
            return LLMResponse(text="", metadata={"source": self.name})

        normalized = prompt.strip().lower()
        task_type = kwargs.get("task_type", "general")

        if task_type == "coder":
            if "refactor" in normalized:
                code = (
                    "def compute_total(prices: list[float]) -> float:\n"
                    "    \"\"\"Return the sum of a list of prices.\"\"\"\n"
                    "    return sum(prices)\n"
                )
                explanation = (
                    "Refactored the function to use Python's built-in sum for clarity "
                    "and maintainability."
                )
            elif "explain" in normalized:
                code = prompt
                explanation = (
                    "This code example is being explained by the mock provider with a "
                    "focus on readability, docstrings, and Python best practices."
                )
            else:
                code = (
                    "def hello_world() -> str:\n"
                    "    \"\"\"Return a friendly greeting.\"\"\"\n"
                    "    return 'Hello, world!'\n"
                )
                explanation = (
                    "Generated a simple Python function that returns a greeting. "
                    "Use it as a starting point for more specific implementations."
                )
            return LLMResponse(
                text=f"CODE:\n{code}\nEXPLANATION:\n{explanation}",
                metadata={"source": self.name, "task_type": task_type},
            )

        if task_type == "research":
            findings = (
                "Async code should use explicit task management and avoid blocking "
                "calls within the event loop."
            )
            recommendations = (
                "Prefer asyncio-compatible libraries, document coroutine behavior, "
                "and use structured concurrency when possible."
            )
            return LLMResponse(
                text=f"FINDINGS:\n{findings}\nRECOMMENDATIONS:\n{recommendations}",
                metadata={"source": self.name, "task_type": task_type},
            )

        if "async" in normalized:
            findings = (
                "Async code should avoid blocking calls and favor explicit async "
                "workflow management."
            )
            recommendations = (
                "Use asyncio-compatible libraries, document coroutine boundaries, "
                "and test async paths carefully."
            )
            response = f"FINDINGS:\n{findings}\nRECOMMENDATIONS:\n{recommendations}"
        else:
            response = (
                "FINDINGS:\nThis mock provider returns synthesized research output "
                "based on the request.\nRECOMMENDATIONS:\nCapture requirements, "
                "organize documentation, and validate assumptions with prototypes."
            )

        return LLMResponse(text=response, metadata={"source": self.name, "task_type": task_type})


class OpenAIProvider(LLMProvider):
    """An OpenAI provider placeholder for future remote provider integration."""

    @property
    def name(self) -> str:
        return "openai"

    @property
    def description(self) -> str:
        return "OpenAI provider placeholder that is not yet implemented in this project."

    def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        raise NotImplementedError("OpenAI provider is not available in this environment.")


class HuggingFaceProvider(LLMProvider):
    """A HuggingFace provider placeholder for future remote provider integration."""

    @property
    def name(self) -> str:
        return "huggingface"

    @property
    def description(self) -> str:
        return "HuggingFace provider placeholder that is not yet implemented in this project."

    def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        raise NotImplementedError("HuggingFace provider is not available in this environment.")
