"""Archive management tool."""

from __future__ import annotations

import shutil
from pathlib import Path

from .base import BaseTool, ToolExecutionRequest, ToolExecutionResult


class ArchiveTool(BaseTool):
    name = "archive"
    description = "Create and extract archives."
    capabilities = ("archive", "packaging")
    required_permissions = ("tool:archive",)

    def execute(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        payload = request.payload
        action = request.action

        if action == "create":
            source = payload.get("source")
            output = payload.get("output")
            fmt = payload.get("format", "zip")
            if not source or not output:
                return self._error("'source' and 'output' are required")
            archive_path = shutil.make_archive(output, fmt, root_dir=source)
            return self._ok({"archive": archive_path})

        if action == "extract":
            archive = payload.get("archive")
            target = payload.get("target")
            if not archive or not target:
                return self._error("'archive' and 'target' are required")
            target_path = Path(target)
            target_path.mkdir(parents=True, exist_ok=True)
            shutil.unpack_archive(archive, target)
            return self._ok({"target": str(target_path)})

        return self._error(f"Unsupported archive action: {action}")
