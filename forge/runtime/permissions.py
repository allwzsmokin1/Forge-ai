"""Permission controls for the Forge runtime."""

from __future__ import annotations

from typing import Iterable


class ToolPermissionError(PermissionError):
    """Raised when a tool invocation is not allowed."""


class PermissionManager:
    """Evaluate tool and capability permissions."""

    def __init__(self, default_allow: bool = True) -> None:
        self._default_allow = default_allow
        self._tool_rules: dict[str, bool] = {}
        self._capability_rules: dict[str, bool] = {}

    def allow_tool(self, tool_name: str) -> None:
        self._tool_rules[tool_name] = True

    def deny_tool(self, tool_name: str) -> None:
        self._tool_rules[tool_name] = False

    def allow_capability(self, capability: str) -> None:
        self._capability_rules[capability] = True

    def deny_capability(self, capability: str) -> None:
        self._capability_rules[capability] = False

    def is_allowed(self, tool_name: str, capabilities: Iterable[str] = ()) -> bool:
        if tool_name in self._tool_rules:
            return self._tool_rules[tool_name]

        allowed_capability = False
        for capability in capabilities:
            if self._capability_rules.get(capability) is False:
                return False
            if self._capability_rules.get(capability) is True:
                allowed_capability = True

        if allowed_capability:
            return True
        return self._default_allow

    def require(self, tool_name: str, capabilities: Iterable[str] = ()) -> None:
        if not self.is_allowed(tool_name, capabilities):
            raise ToolPermissionError(f"Tool '{tool_name}' is not permitted")
