"""Structured logging helpers for Forge-AI."""

from __future__ import annotations

import json
import logging
from typing import Any


class StructuredFormatter(logging.Formatter):
    """Format log records as structured JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        return json.dumps(payload, default=str)


def configure_logger(name: str = "forge", level: int = logging.INFO) -> logging.Logger:
    """Create or update a logger with structured JSON output."""

    configured_logger = logging.getLogger(name)
    configured_logger.setLevel(level)
    configured_logger.propagate = False

    if not configured_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(StructuredFormatter())
        configured_logger.addHandler(handler)

    return configured_logger


logger = configure_logger()
