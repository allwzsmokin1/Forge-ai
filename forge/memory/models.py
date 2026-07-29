"""Memory model definitions for Forge-AI."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
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
    conversation: ConversationMemory = field(default_factory=ConversationMemory)
