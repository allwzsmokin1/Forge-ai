from pathlib import Path


class PluginManager:
    def __init__(self):
        self.plugins = []

    def discover(self, directory: str = "plugins"):
        path = Path(directory)

        if not path.exists():
            return

        for plugin in path.iterdir():
            if plugin.is_dir():
                self.plugins.append(plugin.name)

    def list_plugins(self):
        return self.plugins


manager = PluginManager()
