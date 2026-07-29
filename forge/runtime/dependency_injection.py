"""Simple dependency injection container for runtime services."""

from __future__ import annotations

from typing import Any


class ServiceContainer:
    """Stores singleton services and factories for runtime dependencies."""

    def __init__(self) -> None:
        self._services: dict[str, Any] = {}

    def register(self, name: str, service: Any) -> None:
        self._services[name] = service

    def resolve(self, name: str) -> Any:
        if name not in self._services:
            raise KeyError(f"Unknown service: {name}")
        return self._services[name]

    def snapshot(self) -> dict[str, Any]:
        return dict(self._services)
