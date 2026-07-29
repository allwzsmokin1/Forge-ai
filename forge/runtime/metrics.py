"""In-memory metrics collection for runtime activity."""

from __future__ import annotations

from collections import defaultdict


class RuntimeMetrics:
    """Collects counters and latencies for tool execution."""

    def __init__(self) -> None:
        self._counts: dict[str, int] = defaultdict(int)
        self._failures: dict[str, int] = defaultdict(int)
        self._latency_seconds: dict[str, float] = defaultdict(float)

    def record_success(self, tool_name: str, elapsed_seconds: float) -> None:
        self._counts[tool_name] += 1
        self._latency_seconds[tool_name] += elapsed_seconds

    def record_failure(self, tool_name: str, elapsed_seconds: float) -> None:
        self._counts[tool_name] += 1
        self._failures[tool_name] += 1
        self._latency_seconds[tool_name] += elapsed_seconds

    def snapshot(self) -> dict[str, dict[str, float | int]]:
        summary: dict[str, dict[str, float | int]] = {}
        for tool_name, count in self._counts.items():
            failures = self._failures.get(tool_name, 0)
            total_latency = self._latency_seconds.get(tool_name, 0.0)
            summary[tool_name] = {
                "count": count,
                "failures": failures,
                "successes": count - failures,
                "avg_latency_seconds": (total_latency / count) if count else 0.0,
            }
        return summary
