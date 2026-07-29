from __future__ import annotations

import json
from pathlib import Path

from forge.agents.base import BaseAgent
from forge.cli import initialize_project
from forge.memory import JSONStorage
from forge.memory.models import ConversationMemory, ProjectMemory
from forge.orchestrator import Orchestrator
from forge.plugins import PluginManager
from forge.runtime import RuntimeManager


def test_initialize_project_uses_runtime_filesystem_tool(tmp_path: Path) -> None:
    runtime = RuntimeManager(register_builtins=True)

    project_root = initialize_project(str(tmp_path / "sample-project"), runtime_manager=runtime)

    assert project_root.exists()
    assert (project_root / "src").is_dir()
    assert (project_root / "README.md").read_text(encoding="utf-8") == "# sample-project\n"


def test_json_storage_round_trips_through_runtime(tmp_path: Path) -> None:
    runtime = RuntimeManager(register_builtins=True)
    storage = JSONStorage(str(tmp_path / ".forge" / "memory.json"), runtime_manager=runtime)
    memory = ProjectMemory(
        name="ForgeAI",
        created_at="2026-01-01T00:00:00+00:00",
        goal_summary="summary",
        conversation=ConversationMemory(goal="goal"),
    )

    storage.save(memory)
    loaded = storage.load()

    assert loaded.name == "ForgeAI"
    assert loaded.goal_summary == "summary"
    assert loaded.conversation.goal == "goal"
    assert json.loads((tmp_path / ".forge" / "memory.json").read_text(encoding="utf-8"))["name"] == "ForgeAI"


def test_plugin_manager_discovers_runtime_tool_plugins(tmp_path: Path) -> None:
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    (plugin_dir / "sample_plugin.py").write_text(
        "\n".join(
            [
                "from forge.runtime import ToolExecutionRequest, ToolExecutionResult",
                "from forge.tools import BaseTool",
                "",
                "class SampleTool(BaseTool):",
                "    @property",
                "    def name(self):",
                "        return 'sample'",
                "",
                "    @property",
                "    def description(self):",
                "        return 'sample tool'",
                "",
                "    def execute(self, request: ToolExecutionRequest, context):",
                "        return ToolExecutionResult(tool_name=self.name, success=True, output='ok')",
                "",
                "def register_tools(registry):",
                "    registry.register(SampleTool())",
            ]
        ),
        encoding="utf-8",
    )
    runtime = RuntimeManager(register_builtins=True)
    manager = PluginManager(runtime_manager=runtime)

    discovered = manager.discover(str(plugin_dir))

    assert discovered == ["sample_plugin"]
    assert "sample" in runtime.registry.list_tools()
    assert runtime.execute("sample").output == "ok"


class RuntimeAwareAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "RuntimeAwareAgent"

    @property
    def description(self) -> str:
        return "Verifies runtime injection."

    def run(self, prompt: str, **kwargs):
        return self.runtime_manager.registry.list_tools()


def test_orchestrator_injects_shared_runtime_into_agents() -> None:
    runtime = RuntimeManager(register_builtins=True)
    orchestrator = Orchestrator(runtime_manager=runtime)
    agent = RuntimeAwareAgent()

    orchestrator.register_agent(agent, keywords=("runtime-aware",))

    assert agent.runtime_manager is runtime
    assert "filesystem" in agent.run("test")
