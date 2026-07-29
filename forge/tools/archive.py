"""Archive tool for Forge runtime."""

from __future__ import annotations

import tarfile
import zipfile
from pathlib import Path

from ..runtime import RuntimeContext, ToolExecutionRequest, ToolExecutionResult
from .base import BaseTool


class ArchiveTool(BaseTool):
    """Create, inspect, and extract archive files."""

    capabilities = ("archive", "filesystem")

    @property
    def name(self) -> str:
        return "archive"

    @property
    def description(self) -> str:
        return "List, create, and extract zip or tar archives."

    def execute(
        self,
        request: ToolExecutionRequest,
        context: RuntimeContext,
    ) -> ToolExecutionResult:
        payload = request.payload
        archive_path = Path(payload["path"])

        if request.operation == "list":
            output = self._list_archive(archive_path)
        elif request.operation == "extract":
            output = self._extract_archive(archive_path, Path(payload["destination"]))
        elif request.operation == "create":
            output = self._create_archive(archive_path, [Path(item) for item in payload["items"]])
        else:
            raise ValueError(f"Unsupported archive operation: {request.operation}")

        return ToolExecutionResult(tool_name=self.name, success=True, output=output)

    def _list_archive(self, archive_path: Path) -> list[str]:
        if zipfile.is_zipfile(archive_path):
            with zipfile.ZipFile(archive_path) as archive:
                return archive.namelist()
        with tarfile.open(archive_path) as archive:
            return archive.getnames()

    def _extract_archive(self, archive_path: Path, destination: Path) -> str:
        destination.mkdir(parents=True, exist_ok=True)
        if zipfile.is_zipfile(archive_path):
            with zipfile.ZipFile(archive_path) as archive:
                archive.extractall(destination)
        else:
            with tarfile.open(archive_path) as archive:
                archive.extractall(destination)
        return str(destination)

    def _create_archive(self, archive_path: Path, items: list[Path]) -> str:
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        if archive_path.suffix == ".zip":
            with zipfile.ZipFile(archive_path, "w") as archive:
                for item in items:
                    archive.write(item, arcname=item.name)
        else:
            with tarfile.open(archive_path, "w:gz") as archive:
                for item in items:
                    archive.add(item, arcname=item.name)
        return str(archive_path)
