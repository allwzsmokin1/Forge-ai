"""Unified runtime manager for all Forge tools."""

from __future__ import annotations

import logging
import time
from typing import Any

from forge.logger import configure_logger
from forge.tools.base import BaseTool, ToolExecutionRequest, ToolExecutionResult

from .events import EventBus
from .hooks import RuntimeHook
from .metrics import RuntimeMetrics
from .models import ToolCall, ToolOutcome
from .permissions import PermissionManager
from .plugins import PluginDiscovery
from .registry import ToolRegistry


class RuntimeManager:
    """Coordinates tool execution, policy checks, retries, and observability."""

    def __init__(
        self,
        registry: ToolRegistry | None = None,
        permissions: PermissionManager | None = None,
        event_bus: EventBus | None = None,
        logger: logging.Logger | None = None,
        metrics: RuntimeMetrics | None = None,
        hooks: list[RuntimeHook] | None = None,
        default_retries: int = 0,
    ) -> None:
        self.registry = registry or ToolRegistry()
        self.permissions = permissions or PermissionManager()
        self.event_bus = event_bus or EventBus()
        self.logger = logger or configure_logger("forge.runtime")
        self.metrics = metrics or RuntimeMetrics()
        self.hooks = hooks or []
        self.default_retries = max(0, default_retries)
        self.container: dict[str, Any] = {}
        self.plugin_discovery = PluginDiscovery()

    def inject(self, key: str, dependency: Any) -> None:
        self.container[key] = dependency

    def resolve(self, key: str, default: Any = None) -> Any:
        return self.container.get(key, default)

    def register_hook(self, hook: RuntimeHook) -> None:
        self.hooks.append(hook)

    def register_tool(self, tool: BaseTool) -> None:
        self.registry.register(tool)

    def discover_plugins(self, package: str | None = None, group: str = "forge.tools") -> None:
        discovered = []
        if package:
            discovered.extend(self.plugin_discovery.discover_package_tools(package))
        discovered.extend(self.plugin_discovery.discover_entrypoint_tools(group=group))
        for tool in discovered:
            self.registry.register(tool)

    def get_tool_for_capability(self, capability: str) -> BaseTool:
        return self.registry.resolve_capability(capability)

    def execute(
        self,
        agent_name: str,
        tool_name: str,
        action: str,
        payload: dict[str, Any] | None = None,
        retries: int | None = None,
    ) -> ToolOutcome:
        tool = self.registry.get(tool_name)
        decision = self.permissions.check(agent_name, tool.required_permissions)
        if not decision.allowed:
            return ToolOutcome(success=False, error=decision.reason)

        max_retries = self.default_retries if retries is None else max(0, retries)
        attempts = 0
        last_error: str | None = None

        while attempts <= max_retries:
            attempts += 1
            call = ToolCall(
                agent_name=agent_name,
                tool_name=tool_name,
                action=action,
                payload=payload or {},
                retries=max_retries,
            )
            for hook in self.hooks:
                hook.before_execute(call)

            started = time.perf_counter()
            self.event_bus.publish(
                "tool.execution.started",
                {
                    "agent": agent_name,
                    "tool": tool_name,
                    "action": action,
                    "attempt": attempts,
                },
            )
            try:
                result = tool.execute(ToolExecutionRequest(action=action, payload=payload or {}))
                if not isinstance(result, ToolExecutionResult):
                    result = ToolExecutionResult(success=True, data=result)
                duration_ms = (time.perf_counter() - started) * 1000
                outcome = ToolOutcome(
                    success=result.success,
                    data=result.data,
                    error=result.error,
                    attempts=attempts,
                    duration_ms=duration_ms,
                    metadata=result.metadata,
                )
                self.metrics.record(
                    tool_name=tool_name,
                    success=outcome.success,
                    duration_ms=duration_ms,
                    retries=max(0, attempts - 1),
                )
                for hook in self.hooks:
                    hook.after_execute(call, outcome)

                event = "tool.execution.succeeded" if outcome.success else "tool.execution.failed"
                self.event_bus.publish(
                    event,
                    {
                        "agent": agent_name,
                        "tool": tool_name,
                        "action": action,
                        "attempt": attempts,
                        "duration_ms": duration_ms,
                        "error": outcome.error,
                    },
                )
                self.logger.info(
                    "event=tool_execution tool=%s action=%s success=%s attempts=%d duration_ms=%.3f",
                    tool_name,
                    action,
                    outcome.success,
                    attempts,
                    duration_ms,
                )
                if outcome.success or attempts > max_retries:
                    return outcome
                last_error = outcome.error or "Tool execution failed"
            except Exception as exc:  # pragma: no cover - defensive branch
                duration_ms = (time.perf_counter() - started) * 1000
                last_error = str(exc)
                self.metrics.record(
                    tool_name=tool_name,
                    success=False,
                    duration_ms=duration_ms,
                    retries=max(0, attempts - 1),
                )
                for hook in self.hooks:
                    hook.on_error(call, exc)
                self.event_bus.publish(
                    "tool.execution.failed",
                    {
                        "agent": agent_name,
                        "tool": tool_name,
                        "action": action,
                        "attempt": attempts,
                        "duration_ms": duration_ms,
                        "error": last_error,
                    },
                )
                self.logger.exception(
                    "event=tool_execution_error tool=%s action=%s attempt=%d",
                    tool_name,
                    action,
                    attempts,
                )

            if attempts <= max_retries:
                self.event_bus.publish(
                    "tool.execution.retry",
                    {"agent": agent_name, "tool": tool_name, "action": action, "attempt": attempts},
                )

        return ToolOutcome(
            success=False, error=last_error or "Tool execution failed", attempts=attempts
        )

    def execute_capability(
        self,
        agent_name: str,
        capability: str,
        action: str,
        payload: dict[str, Any] | None = None,
        retries: int | None = None,
    ) -> ToolOutcome:
        tool = self.registry.resolve_capability(capability)
        return self.execute(
            agent_name=agent_name,
            tool_name=tool.name,
            action=action,
            payload=payload,
            retries=retries,
        )

    def health_check(self) -> dict[str, bool]:
        status: dict[str, bool] = {}
        for tool in self.registry.all_tools():
            outcome = tool.health_check()
            status[tool.name] = bool(outcome.success)
        return status
