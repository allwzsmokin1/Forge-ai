"""Logging utilities for Forge-AI."""

from __future__ import annotations

import json
import logging
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

logger = logging.getLogger("forge")


def log_structured(
    logger_instance: logging.Logger,
    level: int,
    event: str,
    **context: Any,
) -> None:
    """Emit a structured log event."""

    if context:
        logger_instance.log(
            level,
            "%s | %s",
            event,
            json.dumps(context, sort_keys=True, default=str),
        )
        return

    logger_instance.log(level, event)
