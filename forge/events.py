from collections import defaultdict
from collections.abc import Callable
from typing import Any


class EventBus:
    def __init__(self):
        self._listeners = defaultdict(list)

    def subscribe(self, event: str, callback: Callable):
        self._listeners[event].append(callback)

    def publish(self, event: str, data: Any = None):
        for callback in self._listeners[event]:
            callback(data)


bus = EventBus()
