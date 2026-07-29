"""Simple dependency injection container used by the runtime."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


class ServiceContainer:
    """Store and resolve runtime-scoped dependencies."""

    def __init__(self) -> None:
        self._instances: dict[str, Any] = {}
        self._factories: dict[str, Callable[[], Any]] = {}

    def register_instance(self, name: str, instance: Any) -> None:
        self._instances[name] = instance

    def register_factory(self, name: str, factory: Callable[[], Any]) -> None:
        self._factories[name] = factory

    def resolve(self, name: str, default: Any = None) -> Any:
        if name in self._instances:
            return self._instances[name]
        if name in self._factories:
            instance = self._factories[name]()
            self._instances[name] = instance
            return instance
        return default
