"""Event bus primitives for runtime lifecycle and tool execution events."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RuntimeEvent:
    """Structured runtime event payload."""

    name: str
    data: dict[str, Any]


class EventBus:
    """Simple in-process publish/subscribe event bus."""

    def __init__(self) -> None:
        self._listeners: dict[str, list[Callable[[RuntimeEvent], None]]] = defaultdict(list)

    def subscribe(self, event_name: str, callback: Callable[[RuntimeEvent], None]) -> None:
        self._listeners[event_name].append(callback)

    def publish(self, event_name: str, data: dict[str, Any] | None = None) -> None:
        event = RuntimeEvent(name=event_name, data=data or {})
        for callback in tuple(self._listeners[event_name]):
            callback(event)
