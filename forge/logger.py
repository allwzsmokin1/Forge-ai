import logging
from typing import Any


class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        runtime_event: Any = getattr(record, "runtime_event", None)
        if runtime_event is None:
            return super().format(record)
        timestamp = self.formatTime(record, self.datefmt)
        return f"{timestamp} runtime_event={runtime_event}"


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

logger = logging.getLogger("forge")
