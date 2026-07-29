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
    MemorySummary,
    ProjectMemory,
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
            "file_metadata": self._serialize_value(memory.file_metadata),
            "agent_decisions": [self._serialize_value(entry) for entry in memory.agent_decisions],
            "summaries": [self._serialize_value(entry) for entry in memory.summaries],
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
            completed_tasks=[
                self._load_memory_entry(entry) for entry in raw.get("completed_tasks", [])
            ],
            failed_tasks=[self._load_memory_entry(entry) for entry in raw.get("failed_tasks", [])],
            code_summaries=raw.get("code_summaries", []),
            file_metadata={
                path: self._load_file_metadata(file_metadata)
                for path, file_metadata in raw.get("file_metadata", {}).items()
            },
            agent_decisions=[
                self._load_agent_decision(entry) for entry in raw.get("agent_decisions", [])
            ],
            summaries=[self._load_summary(entry) for entry in raw.get("summaries", [])],
            conversation=ConversationMemory(
                goal=conversation_raw.get("goal", ""),
                project_goals=conversation_raw.get("project_goals", []),
                architecture_decisions=conversation_raw.get("architecture_decisions", []),
                important_files=conversation_raw.get("important_files", []),
                entries=[
                    self._load_memory_entry(entry) for entry in conversation_raw.get("entries", [])
                ],
            ),
        )
        return memory

    def _load_memory_entry(self, raw: dict[str, Any]) -> MemoryEntry:
        return MemoryEntry(
            timestamp=raw["timestamp"],
            task_title=raw["task_title"],
            task_description=raw["task_description"],
            agent_name=raw["agent_name"],
            status=raw["status"],
            task_id=raw.get("task_id", ""),
            attempt=raw.get("attempt", 1),
            dependencies=raw.get("dependencies", []),
            result=raw.get("result"),
            error=raw.get("error"),
            categories=raw.get("categories", []),
            metadata=raw.get("metadata", {}),
        )

    def _load_file_metadata(self, raw: dict[str, Any]) -> FileMetadata:
        return FileMetadata(
            path=raw["path"],
            summary=raw["summary"],
            updated_at=raw["updated_at"],
            tags=raw.get("tags", []),
            metadata=raw.get("metadata", {}),
        )

    def _load_agent_decision(self, raw: dict[str, Any]) -> AgentDecision:
        return AgentDecision(
            timestamp=raw["timestamp"],
            agent_name=raw["agent_name"],
            task_id=raw.get("task_id", ""),
            decision=raw["decision"],
            rationale=raw.get("rationale", ""),
            related_tasks=raw.get("related_tasks", []),
            metadata=raw.get("metadata", {}),
        )

    def _load_summary(self, raw: dict[str, Any]) -> MemorySummary:
        return MemorySummary(
            timestamp=raw["timestamp"],
            title=raw["title"],
            content=raw["content"],
            categories=raw.get("categories", []),
            metadata=raw.get("metadata", {}),
        )
