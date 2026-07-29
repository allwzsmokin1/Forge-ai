"""Plugin manager facade backed by runtime tool plugin discovery."""

from __future__ import annotations

from .runtime import get_default_runtime


class PluginManager:
    def __init__(self) -> None:
        self.plugins: list[str] = []

    def discover(self, directory: str = "plugins") -> None:
        runtime = get_default_runtime()
        self.plugins = runtime.registry.discover_plugins(directory)

    def list_plugins(self) -> list[str]:
        return list(self.plugins)


manager = PluginManager()
