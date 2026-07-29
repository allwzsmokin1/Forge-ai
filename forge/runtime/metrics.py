"""Metrics collection for runtime tool executions."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .models import ToolExecutionResult


@dataclass
class ToolMetrics:
    """Aggregated execution metrics for one tool."""

    tool_name: str
    executions: int = 0
    successes: int = 0
    failures: int = 0
    retries: int = 0
    total_duration_ms: float = 0.0
    last_duration_ms: float = 0.0

    @property
    def average_duration_ms(self) -> float:
        if self.executions == 0:
            return 0.0
        return self.total_duration_ms / self.executions


class MetricsCollector:
    """Collect runtime metrics per tool."""

    def __init__(self) -> None:
        self._metrics: dict[str, ToolMetrics] = {}

    def record(self, result: ToolExecutionResult, retries: int = 0) -> None:
        metrics = self._metrics.setdefault(
            result.tool_name, ToolMetrics(tool_name=result.tool_name)
        )
        metrics.executions += 1
        metrics.retries += retries
        metrics.total_duration_ms += result.duration_ms
        metrics.last_duration_ms = result.duration_ms
        if result.success:
            metrics.successes += 1
        else:
            metrics.failures += 1

    def snapshot(self) -> dict[str, dict[str, float | int | str]]:
        return {
            name: {
                **asdict(metrics),
                "average_duration_ms": metrics.average_duration_ms,
            }
            for name, metrics in self._metrics.items()
        }
