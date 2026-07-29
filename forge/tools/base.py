"""Base abstractions for Forge runtime tools."""

from __future__ import annotations

import abc
from typing import Any

from ..runtime import RuntimeContext, ToolExecutionRequest, ToolExecutionResult, ToolHealthStatus


class BaseTool(abc.ABC):
    """Base class for all runtime tools."""

    capabilities: tuple[str, ...] = ()

    @property
    @abc.abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def description(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def execute(
        self,
        request: ToolExecutionRequest,
        context: RuntimeContext,
    ) -> ToolExecutionResult | Any:
        raise NotImplementedError

    def health_check(self, context: RuntimeContext) -> ToolHealthStatus:
        return ToolHealthStatus(tool_name=self.name, healthy=True, details={"status": "ok"})
