"""Runtime metrics collection."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class RuntimeMetrics:
    """Aggregated execution counters and timing metrics."""

    calls_total: int = 0
    calls_success: int = 0
    calls_failed: int = 0
    retries_total: int = 0
    per_tool_calls: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    per_tool_duration_ms: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def record(self, tool_name: str, success: bool, duration_ms: float, retries: int = 0) -> None:
        self.calls_total += 1
        self.calls_success += int(success)
        self.calls_failed += int(not success)
        self.retries_total += retries
        self.per_tool_calls[tool_name] += 1
        self.per_tool_duration_ms[tool_name] += duration_ms
