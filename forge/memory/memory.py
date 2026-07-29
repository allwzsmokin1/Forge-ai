"""Memory manager for Forge-AI project memory."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from .models import (
    AgentDecision,
    ConversationMemory,
    FileMetadata,
    MemoryEntry,
    ProjectMemory,
    TaskRecord,
)
from .storage import JSONStorage, StorageBackend

logger = logging.getLogger("forge.memory")


class MemoryManager:
    """Manage project memory with a pluggable storage backend."""

    def __init__(
        self,
        project_name: str,
        storage: StorageBackend | None = None,
        memory_path: str | None = None,
    ) -> None:
        self.project_name = project_name
        self.storage = storage or JSONStorage(memory_path or "./.forge/memory.json")
        self.memory = ProjectMemory(
            name=project_name,
            created_at=self._now_iso(),
            conversation=ConversationMemory(goal=""),
        )
        self._logger = logger

    def _now_iso(self) -> str:
        return datetime.now(tz=UTC).isoformat()

    def add_entry(
        self,
        task_title: str,
        task_description: str,
        agent_name: str,
        status: str,
        result: Any = None,
        error: str | None = None,
        categories: list[str] | None = None,
    ) -> MemoryEntry:
        categories = categories or []
        entry = MemoryEntry(
            timestamp=self._now_iso(),
            task_title=task_title,
            task_description=task_description,
            agent_name=agent_name,
            status=status,
            result=result,
            error=error,
            categories=categories,
        )

        self.memory.conversation.entries.append(entry)
        if status == "completed":
            self.memory.completed_tasks.append(entry)
        else:
            self.memory.failed_tasks.append(entry)

        self._logger.info("Added memory entry for task %s with status %s", task_title, status)
        return entry

    def add_project_goal(self, goal: str) -> None:
        self.memory.conversation.project_goals.append(goal)
        self._logger.info("Added project goal to memory: %s", goal)

    def add_architecture_decision(self, decision: str) -> None:
        self.memory.conversation.architecture_decisions.append(decision)
        self._logger.info("Added architecture decision to memory: %s", decision)

    def add_important_file(self, file_path: str) -> None:
        self.memory.conversation.important_files.append(file_path)
        self._logger.info("Recorded important file in memory: %s", file_path)

    def add_code_summary(self, summary: str) -> None:
        self.memory.code_summaries.append(summary)
        self._logger.info("Added code summary to memory")

    def add_summary(self, key: str, summary: str) -> None:
        self.memory.summaries[key] = summary
        self._logger.info("Added named summary to memory: %s", key)

    def set_goal_summary(self, summary: str) -> None:
        self.memory.goal_summary = summary
        self._logger.info("Set goal summary in memory")

    def record_task_dependencies(self, task_id: str, dependencies: list[str]) -> None:
        self.memory.task_dependencies[task_id] = list(dependencies)
        self._logger.info("Recorded dependencies for task %s", task_id)

    def record_task_state(
        self,
        task_id: str,
        title: str,
        description: str,
        agent_name: str,
        status: str,
        attempt: int,
        dependencies: list[str] | None = None,
        result_summary: str | None = None,
        error: str | None = None,
    ) -> TaskRecord:
        record = TaskRecord(
            task_id=task_id,
            title=title,
            description=description,
            agent_name=agent_name,
            status=status,
            attempt=attempt,
            timestamp=self._now_iso(),
            dependencies=dependencies or [],
            result_summary=result_summary,
            error=error,
        )
        self.memory.task_history.append(record)
        self._logger.info("Recorded task state %s for task %s", status, task_id)
        return record

    def record_file_metadata(
        self,
        path: str,
        summary: str,
        tags: list[str] | None = None,
        last_updated: str | None = None,
    ) -> FileMetadata:
        metadata = FileMetadata(
            path=path,
            summary=summary,
            tags=tags or [],
            last_updated=last_updated or self._now_iso(),
        )
        self.memory.file_metadata.append(metadata)
        self._logger.info("Recorded file metadata for %s", path)
        return metadata

    def record_agent_decision(
        self,
        agent_name: str,
        task_id: str,
        decision: str,
        rationale: str,
    ) -> AgentDecision:
        decision_record = AgentDecision(
            agent_name=agent_name,
            task_id=task_id,
            decision=decision,
            rationale=rationale,
            timestamp=self._now_iso(),
        )
        self.memory.agent_decisions.append(decision_record)
        self._logger.info("Recorded agent decision for task %s", task_id)
        return decision_record

    def get_context(self, query: str, limit: int = 5) -> dict[str, list[Any]]:
        lowered = query.lower()

        task_matches = [
            record
            for record in self.memory.task_history
            if lowered in record.title.lower()
            or lowered in record.description.lower()
            or lowered in record.agent_name.lower()
            or lowered in (record.result_summary or "").lower()
            or lowered in (record.error or "").lower()
        ][:limit]
        file_matches = [
            item
            for item in self.memory.file_metadata
            if lowered in item.path.lower()
            or lowered in item.summary.lower()
            or any(lowered in tag.lower() for tag in item.tags)
        ][:limit]
        decision_matches = [
            item
            for item in self.memory.agent_decisions
            if lowered in item.agent_name.lower()
            or lowered in item.task_id.lower()
            or lowered in item.decision.lower()
            or lowered in item.rationale.lower()
        ][:limit]
        summary_matches = [
            f"{key}: {value}"
            for key, value in self.memory.summaries.items()
            if lowered in key.lower() or lowered in value.lower()
        ][:limit]

        self._logger.info("Retrieved context for query '%s'", query)
        return {
            "tasks": task_matches,
            "files": file_matches,
            "decisions": decision_matches,
            "summaries": summary_matches,
        }

    def search(self, query: str) -> list[MemoryEntry]:
        lowered = query.lower()
        results = [
            entry
            for entry in self.memory.conversation.entries
            if lowered in entry.task_title.lower()
            or lowered in entry.task_description.lower()
            or lowered in entry.agent_name.lower()
            or lowered in (entry.error or "")
        ]
        self._logger.info("Search query '%s' returned %d entries", query, len(results))
        return results

    def get_recent(self, count: int = 5) -> list[MemoryEntry]:
        recent = self.memory.conversation.entries[-count:]
        self._logger.info("Retrieved %d recent memory entries", len(recent))
        return recent

    def get_project_summary(self) -> str:
        summary = [
            f"Project: {self.memory.name}",
            f"Created at: {self.memory.created_at}",
            f"Goal summary: {self.memory.goal_summary or 'None'}",
            f"Completed tasks: {len(self.memory.completed_tasks)}",
            f"Failed tasks: {len(self.memory.failed_tasks)}",
            f"Code summaries: {len(self.memory.code_summaries)}",
            f"Task history: {len(self.memory.task_history)}",
            f"Tracked files: {len(self.memory.file_metadata)}",
            f"Agent decisions: {len(self.memory.agent_decisions)}",
        ]
        if self.memory.conversation.architecture_decisions:
            summary.append(
                f"Architecture decisions: {len(self.memory.conversation.architecture_decisions)}"
            )
        self._logger.info("Generated project summary")
        return "\n".join(summary)

    def save(self) -> None:
        self.storage.save(self.memory)
        self._logger.info("Saved memory to storage")

    def load(self) -> None:
        try:
            self.memory = self.storage.load()
            self._logger.info("Loaded memory from storage")
        except FileNotFoundError:
            self._logger.warning("Memory file not found; starting with empty memory")
        except Exception:
            self._logger.exception("Failed to load memory")
            raise
