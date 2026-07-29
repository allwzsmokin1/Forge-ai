"""Runtime event bus primitives."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from typing import Any

EventListener = Callable[[str, dict[str, Any]], None]


class EventBus:
    """Simple in-process pub/sub for runtime events."""

    def __init__(self) -> None:
        self._listeners: dict[str, list[EventListener]] = defaultdict(list)

    def subscribe(self, event: str, listener: EventListener) -> None:
        self._listeners[event].append(listener)

    def publish(self, event: str, payload: dict[str, Any] | None = None) -> None:
        event_payload = payload or {}
        for listener in list(self._listeners.get(event, ())):
            listener(event, event_payload)
