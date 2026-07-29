"""Memory model definitions for Forge-AI."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class MemoryEntry:
    """A single memory entry describing a task or project event."""

    timestamp: str
    task_title: str
    task_description: str
    agent_name: str
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None
    categories: List[str] = field(default_factory=list)


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
    dependencies: List[str] = field(default_factory=list)
    result_summary: Optional[str] = None
    error: Optional[str] = None


@dataclass(frozen=True)
class FileMetadata:
    """Represents important project file context persisted in memory."""

    path: str
    summary: str
    tags: List[str] = field(default_factory=list)
    last_updated: Optional[str] = None


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
    project_goals: List[str] = field(default_factory=list)
    architecture_decisions: List[str] = field(default_factory=list)
    important_files: List[str] = field(default_factory=list)
    entries: List[MemoryEntry] = field(default_factory=list)


@dataclass
class ProjectMemory:
    """Higher-level memory for a project context."""

    name: str
    created_at: str
    goal_summary: Optional[str] = None
    completed_tasks: List[MemoryEntry] = field(default_factory=list)
    failed_tasks: List[MemoryEntry] = field(default_factory=list)
    code_summaries: List[str] = field(default_factory=list)
    task_history: List[TaskRecord] = field(default_factory=list)
    file_metadata: List[FileMetadata] = field(default_factory=list)
    agent_decisions: List[AgentDecision] = field(default_factory=list)
    summaries: Dict[str, str] = field(default_factory=dict)
    task_dependencies: Dict[str, List[str]] = field(default_factory=dict)
    conversation: ConversationMemory = field(default_factory=ConversationMemory)
