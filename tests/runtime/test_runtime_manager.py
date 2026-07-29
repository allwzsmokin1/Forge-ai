"""Tests for Stage 4 runtime manager behavior."""

from __future__ import annotations

from dataclasses import dataclass

from forge.runtime import RuntimeManager
from forge.tools.base import BaseTool, ToolExecutionRequest, ToolExecutionResult


@dataclass
class _State:
    calls: int = 0


class FlakyTool(BaseTool):
    name = "flaky"
    capabilities = ("flaky",)
    required_permissions = ("tool:flaky",)

    def __init__(self, state: _State) -> None:
        self._state = state

    def execute(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        del request
        self._state.calls += 1
        if self._state.calls == 1:
            return ToolExecutionResult(success=False, error="transient")
        return ToolExecutionResult(success=True, data={"ok": True})


class HealthyTool(BaseTool):
    name = "healthy"
    capabilities = ("health",)

    def execute(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        del request
        return ToolExecutionResult(success=True, data=True)


def test_runtime_manager_retries_and_records_metrics() -> None:
    runtime = RuntimeManager(default_retries=1)
    state = _State()
    runtime.registry.register(FlakyTool(state))
    runtime.permissions.grant("GitAgent", "tool:flaky")

    events: list[str] = []
    runtime.event_bus.subscribe("tool.execution.retry", lambda event, payload: events.append(event))

    outcome = runtime.execute("GitAgent", "flaky", "run")

    assert outcome.success is True
    assert outcome.attempts == 2
    assert runtime.metrics.calls_total == 2
    assert runtime.metrics.calls_success == 1
    assert runtime.metrics.calls_failed == 1
    assert events == ["tool.execution.retry"]


def test_runtime_manager_rejects_missing_permissions() -> None:
    runtime = RuntimeManager()
    runtime.registry.register(FlakyTool(_State()))

    outcome = runtime.execute("GitAgent", "flaky", "run")

    assert outcome.success is False
    assert "Missing permissions" in (outcome.error or "")


def test_runtime_health_checks_all_tools() -> None:
    runtime = RuntimeManager()
    runtime.registry.register(HealthyTool())

    health = runtime.health_check()

    assert health == {"healthy": True}
