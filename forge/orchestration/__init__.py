"""Forge-AI orchestration package.

Provides the Phase 3 autonomous multi-agent orchestration framework:

- ``OrchestratorAgent`` — decomposes goals, schedules tasks, retries failures
- ``TaskDAG`` — directed acyclic graph for dependency management
- ``Scheduler`` — parallel task executor backed by a thread pool
- ``RetryManager`` — configurable retry logic with exponential backoff
- ``models`` — shared data models (TaskStatus, OrchestratedTask, etc.)
"""

from .dag import CycleError, TaskDAG
from .models import ExecutionSummary, OrchestratedTask, RetryPolicy, TaskStatus
from .orchestrator_agent import OrchestratorAgent
from .retry import RetryManager
from .scheduler import Scheduler

__all__ = [
    "CycleError",
    "ExecutionSummary",
    "OrchestratedTask",
    "OrchestratorAgent",
    "RetryManager",
    "RetryPolicy",
    "Scheduler",
    "TaskDAG",
    "TaskStatus",
]
