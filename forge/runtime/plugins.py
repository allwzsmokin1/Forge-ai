"""Plugin discovery for runtime tools."""

from __future__ import annotations

import importlib
import pkgutil
from importlib.metadata import entry_points

from forge.tools.base import BaseTool


class PluginDiscovery:
    """Discover tool plugins from packages and entry points."""

    def discover_package_tools(self, package: str) -> list[BaseTool]:
        module = importlib.import_module(package)
        discovered: list[BaseTool] = []
        for module_info in pkgutil.iter_modules(module.__path__, prefix=f"{package}."):
            candidate_module = importlib.import_module(module_info.name)
            factory = getattr(candidate_module, "load_tool", None)
            if callable(factory):
                tool = factory()
                if isinstance(tool, BaseTool):
                    discovered.append(tool)
        return discovered

    def discover_entrypoint_tools(self, group: str = "forge.tools") -> list[BaseTool]:
        discovered: list[BaseTool] = []
        for ep in entry_points().select(group=group):
            loaded = ep.load()
            tool = loaded() if callable(loaded) else loaded
            if isinstance(tool, BaseTool):
                discovered.append(tool)
        return discovered
