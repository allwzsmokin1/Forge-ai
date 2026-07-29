from __future__ import annotations

from dataclasses import dataclass

import pytest

from forge.runtime import (
    PermissionManager,
    RetryPolicy,
    RuntimeHook,
    RuntimeManager,
    ToolExecutionError,
    ToolExecutionRequest,
    ToolExecutionResult,
    ToolPermissionError,
)
from forge.tools import BaseTool


class EchoTool(BaseTool):
    capabilities = ("echo",)

    @property
    def name(self) -> str:
        return "echo"

    @property
    def description(self) -> str:
        return "Echo payload values."

    def execute(self, request: ToolExecutionRequest, context) -> ToolExecutionResult:
        return ToolExecutionResult(
            tool_name=self.name,
            success=True,
            output={"payload": request.payload, "context": context.metadata},
        )


class FlakyTool(BaseTool):
    capabilities = ("flaky",)

    def __init__(self) -> None:
        self.calls = 0

    @property
    def name(self) -> str:
        return "flaky"

    @property
    def description(self) -> str:
        return "Fail once, then succeed."

    def execute(self, request: ToolExecutionRequest, context) -> ToolExecutionResult:
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("temporary failure")
        return ToolExecutionResult(tool_name=self.name, success=True, output=self.calls)


@dataclass
class HookState(RuntimeHook):
    before: int = 0
    after: int = 0
    errors: int = 0
    health: int = 0

    def before_execution(self, request, context) -> None:
        self.before += 1

    def after_execution(self, request, result, context) -> None:
        self.after += 1

    def on_error(self, request, error, attempt, context) -> None:
        self.errors += 1

    def after_health_checks(self, statuses, context) -> None:
        self.health += 1


def test_runtime_manager_executes_tool_collects_metrics_and_events() -> None:
    runtime = RuntimeManager(register_builtins=False)
    runtime.registry.register(EchoTool())
    hook = HookState()
    events = []
    runtime.add_hook(hook)
    runtime.event_bus.subscribe("tool.execution.completed", lambda event: events.append(event))

    result = runtime.execute(
        "echo",
        operation="run",
        payload={"message": "hello"},
        metadata={"scope": "test"},
    )

    assert result.success is True
    assert result.output["payload"]["message"] == "hello"
    assert result.output["context"]["scope"] == "test"
    assert hook.before == 1
    assert hook.after == 1
    assert events[0].name == "tool.execution.completed"
    assert runtime.metrics.snapshot()["echo"]["executions"] == 1
    assert runtime.check_health()[0].healthy is True
    assert hook.health == 1


def test_runtime_manager_retries_failures() -> None:
    runtime = RuntimeManager(
        register_builtins=False,
        retry_policy=RetryPolicy(max_attempts=2, backoff_seconds=0.0),
    )
    flaky = FlakyTool()
    runtime.registry.register(flaky)
    hook = HookState()
    runtime.add_hook(hook)

    result = runtime.execute("flaky")

    assert result.success is True
    assert result.output == 2
    assert flaky.calls == 2
    assert hook.errors == 1
    assert runtime.metrics.snapshot()["flaky"]["retries"] == 1


def test_runtime_manager_raises_when_retries_exhausted() -> None:
    runtime = RuntimeManager(
        register_builtins=False,
        retry_policy=RetryPolicy(max_attempts=1, backoff_seconds=0.0),
    )
    runtime.registry.register(FlakyTool())

    with pytest.raises(ToolExecutionError):
        runtime.execute("flaky")


def test_permission_manager_blocks_denied_tools() -> None:
    permissions = PermissionManager(default_allow=False)
    runtime = RuntimeManager(register_builtins=False, permission_manager=permissions)
    runtime.registry.register(EchoTool())

    with pytest.raises(ToolPermissionError):
        runtime.execute("echo")
