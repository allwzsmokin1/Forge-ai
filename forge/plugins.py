from pathlib import Path

from .runtime import RuntimeManager, get_runtime


class PluginManager:
    def __init__(self, runtime_manager: RuntimeManager | None = None):
        self.plugins = []
        self._runtime_manager = runtime_manager or get_runtime()

    def discover(self, directory: str = "plugins"):
        path = Path(directory)
        discovered = self._runtime_manager.registry.discover_plugins(str(path))
        self.plugins = discovered
        return discovered

    def list_plugins(self):
        return self.plugins


manager = PluginManager()
