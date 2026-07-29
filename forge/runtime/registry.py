"""Tool registry for runtime dispatch and capability lookup."""

from __future__ import annotations

from collections import defaultdict

from forge.tools.base import BaseTool


class ToolRegistry:
    """Stores tools and capability mappings."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}
        self._capabilities: dict[str, set[str]] = defaultdict(set)

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool
        for capability in tool.capabilities:
            self._capabilities[capability].add(tool.name)

    def get(self, name: str) -> BaseTool:
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        return self._tools[name]

    def list_tools(self) -> tuple[str, ...]:
        return tuple(sorted(self._tools))

    def resolve_capability(self, capability: str) -> BaseTool:
        names = sorted(self._capabilities.get(capability, ()))
        if not names:
            raise KeyError(f"No tool registered for capability: {capability}")
        return self._tools[names[0]]

    def all_tools(self) -> list[BaseTool]:
        return list(self._tools.values())
