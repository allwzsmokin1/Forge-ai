from __future__ import annotations

from forge.runtime import ToolContext, ToolExecutionResult, ToolRegistry
from forge.tools import RuntimeTool


class DummyTool(RuntimeTool):
    @property
    def name(self) -> str:
        return "dummy"

    @property
    def capabilities(self) -> tuple[str, ...]:
        return ("dummy.run",)

    def execute(self, payload, context: ToolContext) -> ToolExecutionResult:
        return ToolExecutionResult(success=True, output={"dummy": True})


def test_registry_discovers_plugin_tools(tmp_path) -> None:
    plugin_file = tmp_path / "sample_plugin.py"
    plugin_file.write_text(
        """from forge.tools import RuntimeTool
from forge.runtime import ToolContext, ToolExecutionResult


class PluginTool(RuntimeTool):
    @property
    def name(self):
        return 'plugin_tool'

    @property
    def capabilities(self):
        return ('plugin.capability',)

    def execute(self, payload, context: ToolContext):
        return ToolExecutionResult(success=True, output={'from': 'plugin'})


def register_tools(registry):
    registry.register(PluginTool())
""",
        encoding="utf-8",
    )

    registry = ToolRegistry()
    discovered = registry.discover_plugins(str(tmp_path))

    assert discovered == ["sample_plugin"]
    assert "plugin_tool" in registry.list_tools()
    resolved = registry.resolve_for_capability("plugin.capability")
    assert resolved.name == "plugin_tool"
