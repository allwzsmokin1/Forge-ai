"""Runtime event bus and event models."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict


@dataclass(frozen=True)
class RuntimeEvent:
    """Structured runtime event."""

    name: str
    payload: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(tz=timezone.utc).isoformat()
    )


class RuntimeEventBus:
    """Publish and subscribe to runtime events."""

    def __init__(self) -> None:
        self._listeners: dict[str, list[Callable[[RuntimeEvent], None]]] = defaultdict(list)

    def subscribe(self, event: str, callback: Callable[[RuntimeEvent], None]) -> None:
        self._listeners[event].append(callback)

    def publish(
        self,
        event: str,
        data: Any = None,
        metadata: Dict[str, Any] | None = None,
    ) -> RuntimeEvent:
        runtime_event = RuntimeEvent(name=event, payload=data, metadata=metadata or {})
        for callback in list(self._listeners[event]):
            callback(runtime_event)
        return runtime_event
