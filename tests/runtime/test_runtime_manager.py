from __future__ import annotations

from dataclasses import dataclass

from forge.runtime import (
    EventBus,
    PermissionPolicy,
    RuntimeHook,
    ToolContext,
    ToolExecutionRequest,
    ToolExecutionResult,
    ToolRegistry,
    ToolRuntimeManager,
)
from forge.tools import RuntimeTool


class StaticTool(RuntimeTool):
    def __init__(self, *, fail_times: int = 0) -> None:
        self._fail_times = fail_times
        self.calls = 0

    @property
    def name(self) -> str:
        return "static"

    @property
    def capabilities(self) -> tuple[str, ...]:
        return ("test.static",)

    def execute(self, payload: dict[str, object], context: ToolContext) -> ToolExecutionResult:
        self.calls += 1
        if self.calls <= self._fail_times:
            raise RuntimeError("boom")
        return ToolExecutionResult(success=True, output={"ok": True})


@dataclass
class MockRuntimeHook(RuntimeHook):
    before: int = 0
    after: int = 0
    errors: int = 0

    def on_startup(self) -> None:
        return

    def on_shutdown(self) -> None:
        return

    def before_execute(self, request: ToolExecutionRequest) -> None:
        self.before += 1

    def after_execute(self, request: ToolExecutionRequest, result: ToolExecutionResult) -> None:
        self.after += 1

    def on_error(self, request: ToolExecutionRequest, error: Exception) -> None:
        self.errors += 1


def test_runtime_executes_tool_and_tracks_metrics() -> None:
    registry = ToolRegistry()
    tool = StaticTool()
    registry.register(tool)
    runtime = ToolRuntimeManager(registry)

    result = runtime.execute(
        ToolExecutionRequest(tool="static", capability="test.static", agent="Tester", payload={})
    )

    assert result.success is True
    snapshot = runtime.metrics.snapshot()
    assert snapshot["static"]["count"] == 1
    assert snapshot["static"]["failures"] == 0


def test_runtime_respects_permissions() -> None:
    registry = ToolRegistry()
    registry.register(StaticTool())
    permissions = PermissionPolicy(allow_by_default=False)
    runtime = ToolRuntimeManager(registry, permissions=permissions)

    result = runtime.execute(
        ToolExecutionRequest(tool="static", capability="test.static", agent="Tester", payload={})
    )

    assert result.success is False
    assert "Permission denied" in (result.error or "")


def test_runtime_retries_and_calls_hooks() -> None:
    registry = ToolRegistry()
    tool = StaticTool(fail_times=1)
    registry.register(tool)
    hook = MockRuntimeHook()
    events: list[str] = []
    bus = EventBus()
    bus.subscribe("tool.execution.succeeded", lambda event: events.append(event.name))
    runtime = ToolRuntimeManager(registry, event_bus=bus, hooks=[hook])

    result = runtime.execute(
        ToolExecutionRequest(
            tool="static",
            capability="test.static",
            agent="Tester",
            payload={},
            retries=1,
        )
    )

    assert result.success is True
    assert tool.calls == 2
    assert hook.before == 1
    assert hook.after == 1
    assert hook.errors == 1
    assert events == ["tool.execution.succeeded"]


def test_runtime_collects_health_from_tools() -> None:
    registry = ToolRegistry()
    registry.register(StaticTool())
    runtime = ToolRuntimeManager(registry)

    health = runtime.collect_health()

    assert health.healthy is True
    assert any(check.name == "registry" for check in health.checks)
    assert any(check.name == "static" for check in health.checks)
