"""Web tool for fetching HTTP content."""

from __future__ import annotations

from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

from ..runtime.models import ToolContext, ToolExecutionResult
from .base import RuntimeTool


class WebTool(RuntimeTool):
    @property
    def name(self) -> str:
        return "web"

    @property
    def capabilities(self) -> tuple[str, ...]:
        return ("web.fetch",)

    def execute(self, payload: dict[str, Any], context: ToolContext) -> ToolExecutionResult:
        url = str(payload.get("url", "")).strip()
        if not url:
            return ToolExecutionResult(success=False, error="Missing url")

        timeout = payload.get("timeout", 10)
        try:
            with urlopen(url, timeout=timeout) as response:
                body = response.read().decode("utf-8", errors="replace")
                return ToolExecutionResult(
                    success=True,
                    output={"status": response.status, "body": body},
                )
        except URLError as exc:
            return ToolExecutionResult(success=False, error=str(exc))
