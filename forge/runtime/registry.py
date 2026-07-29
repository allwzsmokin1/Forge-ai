"""Registry and plugin discovery for Forge runtime tools."""

from __future__ import annotations

import importlib.util
from importlib import metadata
from pathlib import Path
from types import ModuleType


class ToolRegistry:
    """Manage runtime tool registration and plugin discovery."""

    def __init__(self) -> None:
        self._tools: dict[str, object] = {}
        self._plugins: list[str] = []

    def register(self, tool: object) -> None:
        name = getattr(tool, "name", None)
        if not name:
            raise ValueError("Registered tools must define a name")
        self._tools[name] = tool

    def get(self, name: str) -> object:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise KeyError(f"Unknown tool: {name}") from exc

    def list_tools(self) -> tuple[str, ...]:
        return tuple(sorted(self._tools.keys()))

    def list_plugins(self) -> tuple[str, ...]:
        return tuple(self._plugins)

    def discover_plugins(self, directory: str = "plugins") -> list[str]:
        discovered = list(self._discover_entry_points())
        discovered.extend(self._discover_directory(directory))
        self._plugins.extend(
            plugin_name for plugin_name in discovered if plugin_name not in self._plugins
        )
        return discovered

    def _discover_entry_points(self) -> list[str]:
        discovered: list[str] = []
        entry_points = metadata.entry_points()
        selected = (
            entry_points.select(group="forge.tools")
            if hasattr(entry_points, "select")
            else entry_points.get("forge.tools", [])
        )
        for entry_point in selected:
            loaded = entry_point.load()
            self._register_plugin_payload(loaded)
            discovered.append(entry_point.name)
        return discovered

    def _discover_directory(self, directory: str) -> list[str]:
        path = Path(directory)
        if not path.exists():
            return []

        discovered: list[str] = []
        for plugin_path in sorted(path.iterdir()):
            module = self._load_plugin_module(plugin_path)
            if module is None:
                continue
            self._register_plugin_payload(module)
            discovered.append(plugin_path.stem)
        return discovered

    def _load_plugin_module(self, plugin_path: Path) -> ModuleType | None:
        if plugin_path.is_file() and plugin_path.suffix == ".py":
            module_name = f"forge_runtime_plugin_{plugin_path.stem}"
            spec = importlib.util.spec_from_file_location(module_name, plugin_path)
        elif plugin_path.is_dir() and (plugin_path / "__init__.py").exists():
            module_name = f"forge_runtime_plugin_{plugin_path.name}"
            spec = importlib.util.spec_from_file_location(
                module_name,
                plugin_path / "__init__.py",
                submodule_search_locations=[str(plugin_path)],
            )
        else:
            return None

        if spec is None or spec.loader is None:
            return None

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _register_plugin_payload(self, payload: object) -> None:
        if hasattr(payload, "register_tools"):
            payload.register_tools(self)
            return
        if callable(payload):
            payload(self)
            return
        if isinstance(payload, ModuleType) and hasattr(payload, "register_tools"):
            payload.register_tools(self)
            return
        if hasattr(payload, "name"):
            self.register(payload)
