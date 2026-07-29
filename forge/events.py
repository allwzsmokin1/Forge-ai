"""Backward-compatible event exports backed by runtime event bus."""

from .runtime.events import EventBus

bus = EventBus()

__all__ = ["EventBus", "bus"]
