"""Common interface for all Forge runtime tools."""

from __future__ import annotations

import abc
from typing import Any

from ..runtime.models import HealthCheckResult, ToolContext, ToolExecutionResult


class RuntimeTool(abc.ABC):
    """Base interface for runtime-managed tools."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def capabilities(self) -> tuple[str, ...]:
        raise NotImplementedError

    @abc.abstractmethod
    def execute(self, payload: dict[str, Any], context: ToolContext) -> ToolExecutionResult:
        raise NotImplementedError

    def health_check(self) -> HealthCheckResult:
        return HealthCheckResult(name=self.name, healthy=True, details={})
