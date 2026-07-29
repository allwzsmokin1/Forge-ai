"""Storage layer for Forge-AI memory backends."""

from __future__ import annotations

import dataclasses
import json
from abc import ABC, abstractmethod
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict

from .models import ConversationMemory, MemoryEntry, ProjectMemory
from ..runtime import RuntimeManager, get_runtime


class StorageBackend(ABC):
    """Abstract storage backend for project memory."""

    @abstractmethod
    def save(self, memory: ProjectMemory) -> None:
        raise NotImplementedError

    @abstractmethod
    def load(self) -> ProjectMemory:
        raise NotImplementedError


class JSONStorage(StorageBackend):
    """JSON file storage backend for project memory."""

    def __init__(self, path: str, runtime_manager: RuntimeManager | None = None) -> None:
        self._path = Path(path)
        self._runtime_manager = runtime_manager or get_runtime()
        self._runtime_manager.execute(
            "filesystem",
            operation="mkdir",
            payload={"path": str(self._path.parent), "parents": True, "exist_ok": True},
        )

    def save(self, memory: ProjectMemory) -> None:
        data = {
            "name": memory.name,
            "created_at": memory.created_at,
            "goal_summary": memory.goal_summary,
            "completed_tasks": [self._serialize_value(entry) for entry in memory.completed_tasks],
            "failed_tasks": [self._serialize_value(entry) for entry in memory.failed_tasks],
            "code_summaries": memory.code_summaries,
            "conversation": {
                "goal": memory.conversation.goal,
                "project_goals": memory.conversation.project_goals,
                "architecture_decisions": memory.conversation.architecture_decisions,
                "important_files": memory.conversation.important_files,
                "entries": [self._serialize_value(entry) for entry in memory.conversation.entries],
            },
        }
        self._runtime_manager.execute(
            "filesystem",
            operation="write_text",
            payload={
                "path": str(self._path),
                "content": json.dumps(data, indent=2),
                "encoding": "utf-8",
                "create_parents": True,
            },
        )

    def _serialize_value(self, value: Any) -> Any:
        if dataclasses.is_dataclass(value):
            return {
                key: self._serialize_value(val)
                for key, val in asdict(value).items()
            }
        if isinstance(value, dict):
            return {key: self._serialize_value(val) for key, val in value.items()}
        if isinstance(value, (list, tuple)):
            return [self._serialize_value(item) for item in value]
        return value

    def load(self) -> ProjectMemory:
        exists = self._runtime_manager.execute(
            "filesystem",
            operation="exists",
            payload={"path": str(self._path)},
        ).output
        if not exists:
            raise FileNotFoundError(f"Memory file {self._path} does not exist")

        raw = json.loads(
            self._runtime_manager.execute(
                "filesystem",
                operation="read_text",
                payload={"path": str(self._path), "encoding": "utf-8"},
            ).output
        )
        conversation_raw = raw.get("conversation", {})
        memory = ProjectMemory(
            name=raw["name"],
            created_at=raw["created_at"],
            goal_summary=raw.get("goal_summary"),
            completed_tasks=[MemoryEntry(**entry) for entry in raw.get("completed_tasks", [])],
            failed_tasks=[MemoryEntry(**entry) for entry in raw.get("failed_tasks", [])],
            code_summaries=raw.get("code_summaries", []),
            conversation=ConversationMemory(
                goal=conversation_raw.get("goal", ""),
                project_goals=conversation_raw.get("project_goals", []),
                architecture_decisions=conversation_raw.get("architecture_decisions", []),
                important_files=conversation_raw.get("important_files", []),
                entries=[MemoryEntry(**entry) for entry in conversation_raw.get("entries", [])],
            ),
        )
        return memory
