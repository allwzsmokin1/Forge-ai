"""Tool registry and plugin discovery for the Forge runtime."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from ..tools.base import RuntimeTool


class ToolRegistry:
    """Registry mapping names and capabilities to tool instances."""

    def __init__(self) -> None:
        self._tools_by_name: dict[str, RuntimeTool] = {}
        self._tool_names_by_capability: dict[str, set[str]] = {}
        self._plugin_names: list[str] = []

    def register(self, tool: RuntimeTool) -> None:
        self._tools_by_name[tool.name] = tool
        for capability in tool.capabilities:
            self._tool_names_by_capability.setdefault(capability, set()).add(tool.name)

    def get(self, name: str) -> RuntimeTool:
        try:
            return self._tools_by_name[name]
        except KeyError as exc:
            raise KeyError(f"Unknown tool: {name}") from exc

    def resolve_for_capability(self, capability: str) -> RuntimeTool:
        names = sorted(self._tool_names_by_capability.get(capability, set()))
        if not names:
            raise KeyError(f"No tool registered for capability: {capability}")
        return self._tools_by_name[names[0]]

    def list_tools(self) -> list[str]:
        return sorted(self._tools_by_name.keys())

    def list_plugins(self) -> list[str]:
        return list(self._plugin_names)

    def discover_plugins(self, directory: str = "plugins") -> list[str]:
        path = Path(directory)
        if not path.exists() or not path.is_dir():
            self._plugin_names = []
            return []

        discovered: list[str] = []
        for plugin_file in sorted(path.glob("*.py")):
            spec = importlib.util.spec_from_file_location(f"forge_plugin_{plugin_file.stem}", plugin_file)
            if spec is None or spec.loader is None:
                continue
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            register_tools = getattr(module, "register_tools", None)
            if callable(register_tools):
                register_tools(self)
                discovered.append(plugin_file.stem)

        self._plugin_names = discovered
        return discovered
