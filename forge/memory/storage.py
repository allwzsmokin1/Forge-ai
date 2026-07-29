"""Storage layer for Forge-AI memory backends."""

from __future__ import annotations

import dataclasses
import json
from abc import ABC, abstractmethod
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .models import (
    AgentDecision,
    ConversationMemory,
    FileMetadata,
    MemoryEntry,
    ProjectMemory,
    TaskRecord,
)


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

    def __init__(self, path: str) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, memory: ProjectMemory) -> None:
        data = {
            "name": memory.name,
            "created_at": memory.created_at,
            "goal_summary": memory.goal_summary,
            "completed_tasks": [self._serialize_value(entry) for entry in memory.completed_tasks],
            "failed_tasks": [self._serialize_value(entry) for entry in memory.failed_tasks],
            "code_summaries": memory.code_summaries,
            "task_history": [self._serialize_value(entry) for entry in memory.task_history],
            "file_metadata": [self._serialize_value(entry) for entry in memory.file_metadata],
            "agent_decisions": [self._serialize_value(entry) for entry in memory.agent_decisions],
            "summaries": memory.summaries,
            "task_dependencies": memory.task_dependencies,
            "conversation": {
                "goal": memory.conversation.goal,
                "project_goals": memory.conversation.project_goals,
                "architecture_decisions": memory.conversation.architecture_decisions,
                "important_files": memory.conversation.important_files,
                "entries": [self._serialize_value(entry) for entry in memory.conversation.entries],
            },
        }
        self._path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _serialize_value(self, value: Any) -> Any:
        if dataclasses.is_dataclass(value):
            return {key: self._serialize_value(val) for key, val in asdict(value).items()}
        if isinstance(value, dict):
            return {key: self._serialize_value(val) for key, val in value.items()}
        if isinstance(value, (list, tuple)):
            return [self._serialize_value(item) for item in value]
        return value

    def load(self) -> ProjectMemory:
        if not self._path.exists():
            raise FileNotFoundError(f"Memory file {self._path} does not exist")

        raw = json.loads(self._path.read_text(encoding="utf-8"))
        conversation_raw = raw.get("conversation", {})
        memory = ProjectMemory(
            name=raw["name"],
            created_at=raw["created_at"],
            goal_summary=raw.get("goal_summary"),
            completed_tasks=[MemoryEntry(**entry) for entry in raw.get("completed_tasks", [])],
            failed_tasks=[MemoryEntry(**entry) for entry in raw.get("failed_tasks", [])],
            code_summaries=raw.get("code_summaries", []),
            task_history=[TaskRecord(**entry) for entry in raw.get("task_history", [])],
            file_metadata=[FileMetadata(**entry) for entry in raw.get("file_metadata", [])],
            agent_decisions=[AgentDecision(**entry) for entry in raw.get("agent_decisions", [])],
            summaries=raw.get("summaries", {}),
            task_dependencies=raw.get("task_dependencies", {}),
            conversation=ConversationMemory(
                goal=conversation_raw.get("goal", ""),
                project_goals=conversation_raw.get("project_goals", []),
                architecture_decisions=conversation_raw.get("architecture_decisions", []),
                important_files=conversation_raw.get("important_files", []),
                entries=[MemoryEntry(**entry) for entry in conversation_raw.get("entries", [])],
            ),
        )
        return memory
