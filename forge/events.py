"""Compatibility exports for the Forge runtime event system."""

from .runtime import RuntimeEvent, RuntimeEventBus


class EventBus(RuntimeEventBus):
    """Backward-compatible alias for the runtime event bus."""


bus = EventBus()

__all__ = ["EventBus", "RuntimeEvent", "RuntimeEventBus", "bus"]
