"""HTTP fetch tool."""

from __future__ import annotations

from urllib.request import Request, urlopen

from .base import BaseTool, ToolExecutionRequest, ToolExecutionResult


class WebTool(BaseTool):
    name = "web"
    description = "Fetch web content over HTTP(S)."
    capabilities = ("web", "http")
    required_permissions = ("tool:web",)

    def execute(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        if request.action != "fetch":
            return self._error(f"Unsupported web action: {request.action}")
        url = request.payload.get("url")
        if not url:
            return self._error("'url' is required")

        req = Request(url, headers={"User-Agent": "forge-runtime/0.0.1"})
        timeout = float(request.payload.get("timeout", 10.0))
        with urlopen(req, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            return self._ok(
                {
                    "status": response.status,
                    "headers": dict(response.headers.items()),
                    "body": body,
                }
            )
