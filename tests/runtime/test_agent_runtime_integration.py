from __future__ import annotations

from forge.agents import CoderAgent, PlannerAgent, ResearchAgent, ReviewerAgent
from forge.orchestrator import Orchestrator
from forge.runtime import ToolContext, ToolExecutionResult, ToolRegistry, ToolRuntimeManager
from forge.tools import RuntimeTool


class RecordingTool(RuntimeTool):
    def __init__(self, name: str, capabilities: tuple[str, ...]) -> None:
        self._name = name
        self._capabilities = capabilities
        self.calls: list[dict[str, object]] = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def capabilities(self) -> tuple[str, ...]:
        return self._capabilities

    def execute(self, payload, context: ToolContext) -> ToolExecutionResult:
        self.calls.append(payload)
        return ToolExecutionResult(success=True, output={"ok": True})


def _runtime_with_probe_tools() -> tuple[ToolRuntimeManager, dict[str, RecordingTool]]:
    registry = ToolRegistry()
    tools = {
        "search": RecordingTool("search", ("search.text", "search.files")),
        "web": RecordingTool("web", ("web.fetch",)),
        "filesystem": RecordingTool(
            "filesystem",
            ("filesystem.read", "filesystem.write", "filesystem.list", "filesystem.delete"),
        ),
        "python": RecordingTool("python", ("python.exec",)),
    }
    for tool in tools.values():
        registry.register(tool)
    return ToolRuntimeManager(registry), tools


def test_agents_use_runtime_capability_requests() -> None:
    runtime, tools = _runtime_with_probe_tools()

    CoderAgent(runtime=runtime).run("Write code", runtime_probe="Forge")
    ResearchAgent(runtime=runtime).run("Topic", source_url="https://example.com")
    PlannerAgent(runtime=runtime).run("Plan task", runtime_probe=True)
    ReviewerAgent(runtime=runtime).run("print('x')", runtime_probe=True)

    assert tools["search"].calls
    assert tools["web"].calls
    assert tools["filesystem"].calls
    assert tools["python"].calls


def test_orchestrator_injects_shared_runtime() -> None:
    runtime, _ = _runtime_with_probe_tools()
    orchestrator = Orchestrator(runtime=runtime)

    agent_runtimes = {agent.runtime for _, agent in orchestrator._agents}

    assert runtime in agent_runtimes
    assert len(agent_runtimes) == 1
