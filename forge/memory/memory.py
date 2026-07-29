"""Memory manager for Forge-AI project memory."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from ..tasks import TaskState
from .models import (
    AgentDecision,
    ConversationMemory,
    FileMetadata,
    MemoryEntry,
    MemorySummary,
    ProjectMemory,
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
        task_id: str = "",
        attempt: int = 1,
        dependencies: list[str] | None = None,
        result: Any = None,
        error: str | None = None,
        categories: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryEntry:
        categories = categories or []
        dependencies = dependencies or []
        entry = MemoryEntry(
            timestamp=self._now_iso(),
            task_title=task_title,
            task_description=task_description,
            agent_name=agent_name,
            status=status,
            task_id=task_id,
            attempt=attempt,
            dependencies=dependencies,
            result=result,
            error=error,
            categories=categories,
            metadata=metadata or {},
        )

        self.memory.conversation.entries.append(entry)
        if status == "completed":
            self.memory.completed_tasks.append(entry)
        elif status == "failed":
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

    def add_file_metadata(
        self,
        file_path: str,
        summary: str,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> FileMetadata:
        file_metadata = FileMetadata(
            path=file_path,
            summary=summary,
            updated_at=self._now_iso(),
            tags=tags or [],
            metadata=metadata or {},
        )
        self.memory.file_metadata[file_path] = file_metadata
        self._logger.info("Updated file metadata for %s", file_path)
        return file_metadata

    def add_agent_decision(
        self,
        agent_name: str,
        task_id: str,
        decision: str,
        rationale: str = "",
        related_tasks: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AgentDecision:
        agent_decision = AgentDecision(
            timestamp=self._now_iso(),
            agent_name=agent_name,
            task_id=task_id,
            decision=decision,
            rationale=rationale,
            related_tasks=related_tasks or [],
            metadata=metadata or {},
        )
        self.memory.agent_decisions.append(agent_decision)
        self._logger.info("Recorded agent decision for task %s", task_id)
        return agent_decision

    def add_summary(
        self,
        title: str,
        content: str,
        categories: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MemorySummary:
        summary = MemorySummary(
            timestamp=self._now_iso(),
            title=title,
            content=content,
            categories=categories or [],
            metadata=metadata or {},
        )
        self.memory.summaries.append(summary)
        self._logger.info("Added project summary %s", title)
        return summary

    def set_goal_summary(self, summary: str) -> None:
        self.memory.goal_summary = summary
        self._logger.info("Set goal summary in memory")

    def record_task_state(self, state: TaskState) -> MemoryEntry:
        return self.add_entry(
            task_title=state.task.title,
            task_description=state.task.description,
            agent_name=state.assigned_agent or state.task.agent_hint or "Unassigned",
            status=state.status.value,
            task_id=state.task.task_id,
            attempt=state.attempts,
            dependencies=list(state.task.dependencies),
            result=state.result,
            error=state.error,
            categories=[state.task.task_type],
            metadata={"agent_hint": state.task.agent_hint, "order": state.task.order},
        )

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

    def retrieve_context(self, query: str, limit: int = 5) -> dict[str, list[Any]]:
        lowered = query.lower()
        task_matches = self.search(query)[:limit]
        file_matches = [
            file_metadata
            for file_metadata in self.memory.file_metadata.values()
            if lowered in file_metadata.path.lower()
            or lowered in file_metadata.summary.lower()
            or any(lowered in tag.lower() for tag in file_metadata.tags)
        ][:limit]
        decision_matches = [
            decision
            for decision in self.memory.agent_decisions
            if lowered in decision.agent_name.lower()
            or lowered in decision.decision.lower()
            or lowered in decision.rationale.lower()
        ][:limit]
        summary_matches = [
            summary
            for summary in self.memory.summaries
            if lowered in summary.title.lower()
            or lowered in summary.content.lower()
            or any(lowered in category.lower() for category in summary.categories)
        ][:limit]
        return {
            "tasks": task_matches,
            "files": file_matches,
            "decisions": decision_matches,
            "summaries": summary_matches,
        }

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
            f"Tracked files: {len(self.memory.file_metadata)}",
            f"Agent decisions: {len(self.memory.agent_decisions)}",
            f"Stored summaries: {len(self.memory.summaries)}",
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
