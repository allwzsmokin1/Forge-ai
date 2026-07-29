"""Runtime manager coordinating tool execution, retries, metrics, and hooks."""

from __future__ import annotations

import json
import logging
import subprocess
import time
import uuid
from collections.abc import Iterable
from dataclasses import dataclass

from .dependency_injection import ServiceContainer
from .events import EventBus
from .lifecycle import NoOpRuntimeHook, RuntimeHook
from .metrics import RuntimeMetrics
from .models import HealthCheckResult, ToolContext, ToolExecutionRequest, ToolExecutionResult
from .permissions import PermissionPolicy
from .registry import ToolRegistry


@dataclass(frozen=True)
class RuntimeHealthReport:
    """Health report for runtime and registered tools."""

    healthy: bool
    checks: list[HealthCheckResult]


class ToolRuntimeManager:
    """Unified execution runtime for all agent tool access."""

    def __init__(
        self,
        registry: ToolRegistry,
        *,
        permissions: PermissionPolicy | None = None,
        event_bus: EventBus | None = None,
        hooks: Iterable[RuntimeHook] | None = None,
        container: ServiceContainer | None = None,
        metrics: RuntimeMetrics | None = None,
        logger_instance: logging.Logger | None = None,
    ) -> None:
        self.registry = registry
        self.permissions = permissions or PermissionPolicy()
        self.event_bus = event_bus or EventBus()
        self.hooks = list(hooks or [NoOpRuntimeHook()])
        self.container = container or ServiceContainer()
        self.metrics = metrics or RuntimeMetrics()
        self._logger = logger_instance or logging.getLogger("forge.runtime")

    def startup(self) -> None:
        for hook in self.hooks:
            hook.on_startup()
        self.event_bus.publish("runtime.startup")

    def shutdown(self) -> None:
        for hook in self.hooks:
            hook.on_shutdown()
        self.event_bus.publish("runtime.shutdown")

    def execute(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        if not self.permissions.is_allowed(request.agent, request.capability):
            return ToolExecutionResult(
                success=False,
                error=f"Permission denied for agent '{request.agent}' and capability '{request.capability}'",
            )

        for hook in self.hooks:
            hook.before_execute(request)

        self.event_bus.publish(
            "tool.execution.started",
            {"agent": request.agent, "capability": request.capability, "tool": request.tool},
        )

        attempts = max(request.retries, 0) + 1
        last_error: Exception | None = None
        start = time.perf_counter()

        for attempt in range(1, attempts + 1):
            try:
                tool = self._resolve_tool(request)
                context = ToolContext(
                    request_id=str(uuid.uuid4()),
                    agent=request.agent,
                    capability=request.capability,
                    dependencies=self.container.snapshot(),
                )
                result = tool.execute(request.payload, context)
                elapsed = time.perf_counter() - start
                if result.success:
                    self.metrics.record_success(tool.name, elapsed)
                    self._emit_success(request, result, elapsed)
                    return result

                self.metrics.record_failure(tool.name, elapsed)
                last_error = RuntimeError(result.error or "Tool execution failed")
            except (KeyError, OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
                elapsed = time.perf_counter() - start
                self.metrics.record_failure(request.tool, elapsed)
                last_error = exc
                for hook in self.hooks:
                    hook.on_error(request, exc)
                self._logger.warning(
                    "runtime.execution.retry",
                    extra={
                        "runtime_event": {
                            "attempt": attempt,
                            "max_attempts": attempts,
                            "error": str(exc),
                            "tool": request.tool,
                        }
                    },
                )

            if attempt < attempts:
                continue

        error = str(last_error) if last_error else "Unknown runtime execution failure"
        result = ToolExecutionResult(success=False, error=error)
        for hook in self.hooks:
            hook.after_execute(request, result)
        self.event_bus.publish(
            "tool.execution.failed",
            {
                "agent": request.agent,
                "capability": request.capability,
                "tool": request.tool,
                "error": result.error,
            },
        )
        return result

    def collect_health(self) -> RuntimeHealthReport:
        checks: list[HealthCheckResult] = [
            HealthCheckResult(
                name="registry",
                healthy=True,
                details={"tool_count": len(self.registry.list_tools())},
            )
        ]
        for tool_name in self.registry.list_tools():
            tool = self.registry.get(tool_name)
            checks.append(tool.health_check())
        return RuntimeHealthReport(healthy=all(check.healthy for check in checks), checks=checks)

    def _resolve_tool(self, request: ToolExecutionRequest):
        if request.tool:
            return self.registry.get(request.tool)
        return self.registry.resolve_for_capability(request.capability)

    def _emit_success(
        self,
        request: ToolExecutionRequest,
        result: ToolExecutionResult,
        elapsed_seconds: float,
    ) -> None:
        payload = {
            "agent": request.agent,
            "capability": request.capability,
            "tool": request.tool,
            "duration_seconds": elapsed_seconds,
            "metadata": result.metadata,
        }
        self._logger.info(json.dumps({"runtime_event": "tool.execution.succeeded", **payload}))
        self.event_bus.publish("tool.execution.succeeded", payload)
        for hook in self.hooks:
            hook.after_execute(request, result)
