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
    conversation: ConversationMemory = field(default_factory=ConversationMemory)
