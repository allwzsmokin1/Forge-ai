"""Filesystem interaction tool."""

from __future__ import annotations

from pathlib import Path

from .base import BaseTool, ToolExecutionRequest, ToolExecutionResult


class FilesystemTool(BaseTool):
    name = "filesystem"
    description = "Read, write, and inspect files and directories."
    capabilities = ("filesystem", "file-io")
    required_permissions = ("tool:filesystem",)

    def execute(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        payload = request.payload
        action = request.action
        path_value = payload.get("path")
        if not path_value:
            return self._error("'path' is required")
        path = Path(path_value)

        if action == "read_text":
            if not path.exists():
                return self._error(f"Path does not exist: {path}")
            return self._ok(path.read_text(encoding=payload.get("encoding", "utf-8")))

        if action == "write_text":
            content = payload.get("content", "")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding=payload.get("encoding", "utf-8"))
            return self._ok({"path": str(path), "bytes": len(content.encode())})

        if action == "exists":
            return self._ok(path.exists())

        if action == "mkdir":
            path.mkdir(parents=bool(payload.get("parents", True)), exist_ok=bool(payload.get("exist_ok", True)))
            return self._ok({"path": str(path)})

        if action == "listdir":
            if not path.exists() or not path.is_dir():
                return self._error(f"Directory does not exist: {path}")
            entries = sorted(item.name for item in path.iterdir())
            return self._ok(entries)

        if action == "delete":
            if path.exists():
                if path.is_dir():
                    for item in sorted(path.rglob("*"), reverse=True):
                        if item.is_file():
                            item.unlink()
                        elif item.is_dir():
                            item.rmdir()
                    path.rmdir()
                else:
                    path.unlink()
            return self._ok({"path": str(path), "deleted": True})

        return self._error(f"Unsupported filesystem action: {action}")
