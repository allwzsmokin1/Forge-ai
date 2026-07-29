"""Memory model definitions for Forge-AI."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class MemoryEntry:
    """A single memory entry describing a task or project event."""

    timestamp: str
    task_title: str
    task_description: str
    agent_name: str
    status: str
    result: Any | None = None
    error: str | None = None
    categories: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class TaskRecord:
    """Represents a task execution event within the project history."""

    task_id: str
    title: str
    description: str
    agent_name: str
    status: str
    attempt: int
    timestamp: str
    dependencies: list[str] = field(default_factory=list)
    result_summary: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class FileMetadata:
    """Represents important project file context persisted in memory."""

    path: str
    summary: str
    tags: list[str] = field(default_factory=list)
    last_updated: str | None = None


@dataclass(frozen=True)
class AgentDecision:
    """Represents an orchestration decision made by an agent."""

    agent_name: str
    task_id: str
    decision: str
    rationale: str
    timestamp: str


@dataclass
class ConversationMemory:
    """Memory about the current conversation or goal."""

    goal: str = ""
    project_goals: list[str] = field(default_factory=list)
    architecture_decisions: list[str] = field(default_factory=list)
    important_files: list[str] = field(default_factory=list)
    entries: list[MemoryEntry] = field(default_factory=list)


@dataclass
class ProjectMemory:
    """Higher-level memory for a project context."""

    name: str
    created_at: str
    goal_summary: str | None = None
    completed_tasks: list[MemoryEntry] = field(default_factory=list)
    failed_tasks: list[MemoryEntry] = field(default_factory=list)
    code_summaries: list[str] = field(default_factory=list)
    task_history: list[TaskRecord] = field(default_factory=list)
    file_metadata: list[FileMetadata] = field(default_factory=list)
    agent_decisions: list[AgentDecision] = field(default_factory=list)
    summaries: dict[str, str] = field(default_factory=dict)
    task_dependencies: dict[str, list[str]] = field(default_factory=dict)
    conversation: ConversationMemory = field(default_factory=ConversationMemory)
