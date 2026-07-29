"""Runtime manager coordinating tool execution."""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass
from typing import Any

from .container import ServiceContainer
from .events import RuntimeEventBus
from .lifecycle import RuntimeHook
from .metrics import MetricsCollector
from .models import RuntimeContext, ToolExecutionRequest, ToolExecutionResult, ToolHealthStatus
from .permissions import PermissionManager
from .registry import ToolRegistry


@dataclass(frozen=True)
class RetryPolicy:
    """Retry configuration for tool execution."""

    max_attempts: int = 1
    backoff_seconds: float = 0.0
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,)


class ToolExecutionError(RuntimeError):
    """Raised when a tool fails after retries are exhausted."""


class RuntimeManager:
    """Central runtime used by Forge agents and services."""

    def __init__(
        self,
        registry: ToolRegistry | None = None,
        permission_manager: PermissionManager | None = None,
        event_bus: RuntimeEventBus | None = None,
        metrics: MetricsCollector | None = None,
        container: ServiceContainer | None = None,
        logger_instance: logging.Logger | None = None,
        retry_policy: RetryPolicy | None = None,
        plugin_directories: list[str] | None = None,
        register_builtins: bool = True,
    ) -> None:
        from ..logger import logger
        from ..tools import register_builtin_tools

        self.registry = registry or ToolRegistry()
        self.permission_manager = permission_manager or PermissionManager()
        self.event_bus = event_bus or RuntimeEventBus()
        self.metrics = metrics or MetricsCollector()
        self.container = container or ServiceContainer()
        self._logger = logger_instance or logger
        self.retry_policy = retry_policy or RetryPolicy()
        self._hooks: list[RuntimeHook] = []

        self.container.register_instance("runtime_manager", self)
        self.container.register_instance("tool_registry", self.registry)
        self.container.register_instance("permission_manager", self.permission_manager)
        self.container.register_instance("event_bus", self.event_bus)
        self.container.register_instance("metrics_collector", self.metrics)
        self.container.register_instance("logger", self._logger)

        if register_builtins:
            register_builtin_tools(self.registry)
        for directory in plugin_directories or []:
            self.registry.discover_plugins(directory=directory)

    def add_hook(self, hook: RuntimeHook) -> None:
        self._hooks.append(hook)

    def execute(
        self,
        tool_name: str,
        operation: str = "run",
        payload: dict[str, Any] | None = None,
        *,
        metadata: dict[str, Any] | None = None,
        timeout: float | None = None,
        retries: int | None = None,
        correlation_id: str | None = None,
    ) -> ToolExecutionResult:
        tool = self.registry.get(tool_name)
        capabilities = getattr(tool, "capabilities", ())
        self.permission_manager.require(tool_name, capabilities)

        request = ToolExecutionRequest(
            tool_name=tool_name,
            operation=operation,
            payload=payload or {},
            metadata=metadata or {},
            timeout=timeout,
            retries=retries,
            correlation_id=correlation_id or str(uuid.uuid4()),
        )
        context = RuntimeContext(
            container=self.container,
            event_bus=self.event_bus,
            logger=self._logger,
            metadata={"correlation_id": request.correlation_id, **request.metadata},
        )

        attempts_limit = max(1, retries if retries is not None else self.retry_policy.max_attempts)
        self.event_bus.publish(
            "tool.execution.started",
            {
                "tool_name": tool_name,
                "operation": operation,
                "correlation_id": request.correlation_id,
            },
        )
        for hook in self._hooks:
            hook.before_execution(request, context)

        last_error: Exception | None = None
        for attempt in range(1, attempts_limit + 1):
            started = time.perf_counter()
            try:
                raw_result = tool.execute(request, context)
                if isinstance(raw_result, ToolExecutionResult):
                    base_result = raw_result
                else:
                    base_result = ToolExecutionResult(
                        tool_name=tool_name,
                        success=True,
                        output=raw_result,
                    )
                duration_ms = (time.perf_counter() - started) * 1000
                result = ToolExecutionResult(
                    tool_name=base_result.tool_name,
                    success=base_result.success,
                    output=base_result.output,
                    error=base_result.error,
                    metadata=base_result.metadata,
                    duration_ms=duration_ms,
                    attempts=attempt,
                )
                self.metrics.record(result, retries=attempt - 1)
                self._log_event(
                    "tool.execution.completed",
                    tool_name=tool_name,
                    operation=operation,
                    correlation_id=request.correlation_id,
                    success=result.success,
                    duration_ms=round(duration_ms, 3),
                    attempts=attempt,
                )
                self.event_bus.publish(
                    "tool.execution.completed",
                    {
                        "tool_name": tool_name,
                        "operation": operation,
                        "correlation_id": request.correlation_id,
                        "success": result.success,
                        "attempts": attempt,
                    },
                )
                for hook in self._hooks:
                    hook.after_execution(request, result, context)
                return result
            except self.retry_policy.retryable_exceptions as exc:
                last_error = exc
                duration_ms = (time.perf_counter() - started) * 1000
                self._log_event(
                    "tool.execution.failed",
                    tool_name=tool_name,
                    operation=operation,
                    correlation_id=request.correlation_id,
                    success=False,
                    duration_ms=round(duration_ms, 3),
                    attempts=attempt,
                    error=str(exc),
                )
                self.event_bus.publish(
                    "tool.execution.failed",
                    {
                        "tool_name": tool_name,
                        "operation": operation,
                        "correlation_id": request.correlation_id,
                        "attempts": attempt,
                        "error": str(exc),
                    },
                )
                for hook in self._hooks:
                    hook.on_error(request, exc, attempt, context)
                if attempt >= attempts_limit:
                    result = ToolExecutionResult(
                        tool_name=tool_name,
                        success=False,
                        error=str(exc),
                        duration_ms=duration_ms,
                        attempts=attempt,
                    )
                    self.metrics.record(result, retries=attempt - 1)
                    raise ToolExecutionError(
                        f"Tool '{tool_name}' failed after {attempt} attempt(s): {exc}"
                    ) from exc
                if self.retry_policy.backoff_seconds > 0:
                    time.sleep(self.retry_policy.backoff_seconds)

        raise ToolExecutionError(
            f"Tool '{tool_name}' failed without producing a result: {last_error}"
        )

    def check_health(self) -> list[ToolHealthStatus]:
        context = RuntimeContext(
            container=self.container,
            event_bus=self.event_bus,
            logger=self._logger,
            metadata={},
        )
        statuses: list[ToolHealthStatus] = []
        for tool_name in self.registry.list_tools():
            tool = self.registry.get(tool_name)
            statuses.append(tool.health_check(context))
        for hook in self._hooks:
            hook.after_health_checks(statuses, context)
        return statuses

    def _log_event(self, event: str, **fields: Any) -> None:
        payload = {"event": event, **fields}
        self._logger.info(json.dumps(payload, sort_keys=True, default=str))


_runtime_singleton: RuntimeManager | None = None


def get_runtime() -> RuntimeManager:
    """Return the process-wide runtime singleton."""

    global _runtime_singleton
    if _runtime_singleton is None:
        _runtime_singleton = RuntimeManager()
    return _runtime_singleton
