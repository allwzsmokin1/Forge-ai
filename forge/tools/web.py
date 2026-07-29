"""Web tool for Forge runtime."""

from __future__ import annotations

import ipaddress
import socket
from urllib import parse as urllib_parse
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

        url = request.payload["url"]
        self._validate_url(url)
        with urllib_request.urlopen(url, timeout=request.timeout) as response:
            body = response.read().decode(request.payload.get("encoding", "utf-8"))
            output = {
                "status": getattr(response, "status", 200),
                "headers": dict(response.headers.items()),
                "body": body,
            }
        return ToolExecutionResult(tool_name=self.name, success=True, output=output)

    def _validate_url(self, url: str) -> None:
        parsed = urllib_parse.urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("Web tool only supports http and https URLs")
        if not parsed.hostname:
            raise ValueError("Web tool requires a hostname")

        host = parsed.hostname
        if host.lower() == "localhost":
            raise ValueError("Web tool does not allow localhost targets")

        try:
            addresses = socket.getaddrinfo(host, parsed.port or None, proto=socket.IPPROTO_TCP)
        except socket.gaierror as exc:
            raise ValueError(f"Unable to resolve host '{host}'") from exc

        for _, _, _, _, sockaddr in addresses:
            ip = ipaddress.ip_address(sockaddr[0])
            if (
                ip.is_loopback
                or ip.is_private
                or ip.is_link_local
                or ip.is_multicast
                or ip.is_reserved
                or ip.is_unspecified
            ):
                raise ValueError(f"Web tool does not allow non-public address '{ip}'")
