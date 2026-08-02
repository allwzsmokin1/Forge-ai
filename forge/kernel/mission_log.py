"""MissionLog — JSON persistence for Mission records.

Writes one JSON file per mission log session to ``<log_dir>/missions.json``.
The file contains a JSON array; each call to :meth:`append` adds one entry.
The entire array is rewritten atomically (write-then-rename) so a crash
mid-write never corrupts the log.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from .models import Mission


class MissionLog:
    """Append-only JSON log of completed missions.

    Args:
        log_dir: Directory where ``missions.json`` is written.
            Defaults to ``.forge`` in the current working directory.
    """

    DEFAULT_FILENAME = "missions.json"

    def __init__(self, log_dir: str | Path | None = None) -> None:
        self._log_dir = Path(log_dir) if log_dir else Path.cwd() / ".forge"
        self._log_path = self._log_dir / self.DEFAULT_FILENAME

    @property
    def log_path(self) -> Path:
        """Absolute path to the JSON log file."""
        return self._log_path

    def append(self, mission: Mission) -> None:
        """Append *mission* to the log file.

        Creates the log directory and file if they do not exist.
        Writes atomically: a temp file is written and renamed so the log is
        never left in a partial state on crash.

        Args:
            mission: The completed (or failed) mission to record.
        """
        self._log_dir.mkdir(parents=True, exist_ok=True)
        records = self._read_all()
        records.append(mission.to_dict())
        self._write_all(records)

    def read_all(self) -> list[dict]:
        """Return all mission records as a list of raw dicts.

        Returns an empty list when the log file does not exist.
        """
        return self._read_all()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _read_all(self) -> list[dict]:
        if not self._log_path.exists():
            return []
        try:
            text = self._log_path.read_text(encoding="utf-8")
            data = json.loads(text)
            if isinstance(data, list):
                return data
            return []
        except (json.JSONDecodeError, OSError):
            return []

    def _write_all(self, records: list[dict]) -> None:
        """Atomically write *records* to the log file."""
        fd, tmp_path = tempfile.mkstemp(dir=self._log_dir, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(records, fh, indent=2, ensure_ascii=False)
            # Atomic replace
            os.replace(tmp_path, self._log_path)
        except Exception:
            # Clean up temp file on failure, then re-raise
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
