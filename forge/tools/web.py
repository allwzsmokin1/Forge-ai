"""Web tool for Forge runtime."""

from __future__ import annotations

from urllib import request as urllib_request

from ..runtime import RuntimeContext, ToolExecutionRequest, ToolExecutionResult
from .base import BaseTool


class WebTool(BaseTool):
    """Fetch web content through a common runtime interface."""

    capabilities = ("web", "network")

    @property
    def name(self) -> str:
        return "web"

    @property
    def description(self) -> str:
        return "Fetch remote resources via HTTP GET."

    def execute(
        self,
        request: ToolExecutionRequest,
        context: RuntimeContext,
    ) -> ToolExecutionResult:
        if request.operation != "fetch":
            raise ValueError(f"Unsupported web operation: {request.operation}")

        with urllib_request.urlopen(request.payload["url"], timeout=request.timeout) as response:
            body = response.read().decode(request.payload.get("encoding", "utf-8"))
            output = {
                "status": getattr(response, "status", 200),
                "headers": dict(response.headers.items()),
                "body": body,
            }
        return ToolExecutionResult(tool_name=self.name, success=True, output=output)
