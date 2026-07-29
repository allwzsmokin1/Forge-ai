"""Extended project memory service for Phase 3 orchestration.

Adds persistent storage for file metadata, agent decision logs, orchestration
summaries, and context retrieval on top of the existing MemoryManager.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .memory import MemoryManager
from .models import MemoryEntry

logger = logging.getLogger("forge.memory.project_service")


# ---------------------------------------------------------------------------
# Extended data models
# ---------------------------------------------------------------------------


@dataclass
class FileMetadata:
    """Metadata about a project file tracked by the memory service.

    Attributes:
        path: Relative file path within the project.
        language: Detected programming language or file type.
        summary: Short description of the file's purpose.
        last_modified: ISO-8601 timestamp of the most recent modification.
        agent_name: Name of the agent that last touched the file.
    """

    path: str
    language: str = ""
    summary: str = ""
    last_modified: str = ""
    agent_name: str = ""


@dataclass
class AgentDecision:
    """A recorded decision made by an agent during orchestration.

    Attributes:
        timestamp: ISO-8601 time the decision was recorded.
        agent_name: Name of the agent that made the decision.
        task_id: ID of the task this decision is associated with.
        decision: Human-readable description of the decision.
        rationale: Explanation of why the decision was taken.
    """

    timestamp: str
    agent_name: str
    task_id: str
    decision: str
    rationale: str = ""


@dataclass
class OrchestrationSummary:
    """Persisted summary of a completed orchestration run.

    Attributes:
        timestamp: ISO-8601 time the run finished.
        goal: The user goal that was orchestrated.
        total_tasks: Total number of tasks in the run.
        completed_tasks: Number of tasks that completed successfully.
        failed_tasks: Number of tasks that ultimately failed.
        skipped_tasks: Number of tasks that were never executed.
        success: True when the entire run succeeded.
    """

    timestamp: str
    goal: str
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    skipped_tasks: int
    success: bool


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class ProjectMemoryService:
    """Extended memory service that wraps MemoryManager with richer context.

    Provides additional storage buckets for:

    - **File metadata** — tracks which agents modified which files.
    - **Agent decisions** — records why an agent made a specific choice.
    - **Orchestration summaries** — persists high-level run statistics.
    - **Context retrieval** — unified keyword search across all buckets.

    The service serialises all data to a second JSON file (``extended_memory.json``
    by default) alongside the primary memory file, keeping the two concerns
    loosely coupled.

    Example::

        service = ProjectMemoryService("MyProject")
        service.record_file("src/parser.py", language="python", agent_name="CoderAgent")
        service.record_decision("TaskAgent", "t1", "Chose mock LLM", "No real LLM available")
        service.record_orchestration_summary(goal="build X", total=5, completed=5, ...)
        results = service.search_context("parser")
    """

    def __init__(
        self,
        project_name: str,
        memory_manager: MemoryManager | None = None,
        extended_path: str | None = None,
    ) -> None:
        self._project_name = project_name
        self._manager = memory_manager or MemoryManager(
            project_name=project_name,
            memory_path=extended_path or "./.forge/memory.json",
        )
        self._ext_path = Path(
            extended_path.replace("memory.json", "extended_memory.json")
            if extended_path and "memory.json" in extended_path
            else "./.forge/extended_memory.json"
        )
        self._ext_path.parent.mkdir(parents=True, exist_ok=True)
        self._logger = logger

        # In-memory stores (persisted via save/load)
        self._file_metadata: dict[str, FileMetadata] = {}
        self._agent_decisions: list[AgentDecision] = []
        self._orchestration_summaries: list[OrchestrationSummary] = []

    # ------------------------------------------------------------------
    # File metadata
    # ------------------------------------------------------------------

    def record_file(
        self,
        path: str,
        language: str = "",
        summary: str = "",
        agent_name: str = "",
    ) -> FileMetadata:
        """Record or update metadata for a project file.

        Args:
            path: Relative file path.
            language: Programming language or file type.
            summary: Short description of the file.
            agent_name: Agent that last modified the file.

        Returns:
            The updated FileMetadata entry.
        """
        meta = FileMetadata(
            path=path,
            language=language,
            summary=summary,
            last_modified=self._now_iso(),
            agent_name=agent_name,
        )
        self._file_metadata[path] = meta
        self._manager.add_important_file(path)
        self._logger.info("Recorded file metadata for '%s'.", path)
        return meta

    def get_file(self, path: str) -> FileMetadata | None:
        """Return metadata for the file at *path*, or None."""
        return self._file_metadata.get(path)

    def list_files(self) -> list[FileMetadata]:
        """Return all tracked file metadata entries."""
        return list(self._file_metadata.values())

    # ------------------------------------------------------------------
    # Agent decisions
    # ------------------------------------------------------------------

    def record_decision(
        self,
        agent_name: str,
        task_id: str,
        decision: str,
        rationale: str = "",
    ) -> AgentDecision:
        """Append a new agent decision to the log.

        Args:
            agent_name: Name of the deciding agent.
            task_id: ID of the associated task.
            decision: Short description of the decision.
            rationale: Why the decision was taken.

        Returns:
            The recorded AgentDecision.
        """
        record = AgentDecision(
            timestamp=self._now_iso(),
            agent_name=agent_name,
            task_id=task_id,
            decision=decision,
            rationale=rationale,
        )
        self._agent_decisions.append(record)
        self._manager.add_architecture_decision(f"[{agent_name}] {decision}")
        self._logger.info("Recorded decision by '%s': %s.", agent_name, decision)
        return record

    def get_decisions_for_task(self, task_id: str) -> list[AgentDecision]:
        """Return all decisions associated with the given task ID."""
        return [d for d in self._agent_decisions if d.task_id == task_id]

    # ------------------------------------------------------------------
    # Orchestration summaries
    # ------------------------------------------------------------------

    def record_orchestration_summary(
        self,
        goal: str,
        total: int,
        completed: int,
        failed: int,
        skipped: int,
        success: bool,
    ) -> OrchestrationSummary:
        """Persist a high-level summary for a completed orchestration run.

        Args:
            goal: The user goal that was orchestrated.
            total: Total task count.
            completed: Number of completed tasks.
            failed: Number of permanently failed tasks.
            skipped: Number of tasks that never ran.
            success: Overall success flag.

        Returns:
            The recorded OrchestrationSummary.
        """
        summary = OrchestrationSummary(
            timestamp=self._now_iso(),
            goal=goal,
            total_tasks=total,
            completed_tasks=completed,
            failed_tasks=failed,
            skipped_tasks=skipped,
            success=success,
        )
        self._orchestration_summaries.append(summary)
        self._manager.set_goal_summary(goal)
        self._logger.info(
            "Recorded orchestration summary for goal '%s' (success=%s).", goal, success
        )
        return summary

    def get_orchestration_history(self) -> list[OrchestrationSummary]:
        """Return all recorded orchestration summaries."""
        return list(self._orchestration_summaries)

    # ------------------------------------------------------------------
    # Unified context retrieval
    # ------------------------------------------------------------------

    def search_context(self, query: str) -> dict[str, list[Any]]:
        """Search across all memory buckets for entries matching *query*.

        Searches memory entries (task history), file metadata, and agent
        decisions using case-insensitive keyword matching.

        Args:
            query: Keyword or phrase to search for.

        Returns:
            A dictionary with keys ``"memory_entries"``, ``"files"``, and
            ``"decisions"`` — each mapping to a list of matching records.
        """
        lowered = query.lower()

        memory_entries = self._manager.search(query)

        files = [
            meta
            for meta in self._file_metadata.values()
            if lowered in meta.path.lower()
            or lowered in meta.summary.lower()
            or lowered in meta.language.lower()
        ]

        decisions = [
            d
            for d in self._agent_decisions
            if lowered in d.decision.lower()
            or lowered in d.rationale.lower()
            or lowered in d.agent_name.lower()
        ]

        self._logger.info(
            "Context search '%s': %d entries, %d files, %d decisions.",
            query,
            len(memory_entries),
            len(files),
            len(decisions),
        )
        return {"memory_entries": memory_entries, "files": files, "decisions": decisions}

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self) -> None:
        """Persist all extended data and the underlying memory."""
        import json

        data = {
            "project_name": self._project_name,
            "file_metadata": {k: asdict(v) for k, v in self._file_metadata.items()},
            "agent_decisions": [asdict(d) for d in self._agent_decisions],
            "orchestration_summaries": [asdict(s) for s in self._orchestration_summaries],
        }
        self._ext_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        self._manager.save()
        self._logger.info("Saved extended memory to '%s'.", self._ext_path)

    def load(self) -> None:
        """Load extended data and the underlying memory from disk."""
        import json

        self._manager.load()

        if not self._ext_path.exists():
            self._logger.debug("No extended memory file found; starting fresh.")
            return

        try:
            raw = json.loads(self._ext_path.read_text(encoding="utf-8"))
            self._file_metadata = {
                k: FileMetadata(**v) for k, v in raw.get("file_metadata", {}).items()
            }
            self._agent_decisions = [
                AgentDecision(**d) for d in raw.get("agent_decisions", [])
            ]
            self._orchestration_summaries = [
                OrchestrationSummary(**s) for s in raw.get("orchestration_summaries", [])
            ]
            self._logger.info("Loaded extended memory from '%s'.", self._ext_path)
        except Exception:
            self._logger.exception("Failed to load extended memory: %s", self._ext_path)
            raise

    # ------------------------------------------------------------------
    # Delegation helpers
    # ------------------------------------------------------------------

    def add_entry(self, *args: Any, **kwargs: Any) -> MemoryEntry:
        """Delegate task history recording to the underlying MemoryManager."""
        return self._manager.add_entry(*args, **kwargs)

    def get_project_summary(self) -> str:
        """Return a combined project summary string."""
        base = self._manager.get_project_summary()
        lines = [
            base,
            f"Tracked files: {len(self._file_metadata)}",
            f"Agent decisions: {len(self._agent_decisions)}",
            f"Orchestration runs: {len(self._orchestration_summaries)}",
        ]
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(tz=UTC).isoformat()
