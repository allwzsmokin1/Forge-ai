"""OrchestrAI kernel — MVP implementation.

Exports the public surface of the kernel package so callers can import from
``forge.kernel`` directly without knowing the internal module layout.
"""

from .director import MissionDirector
from .execution_provider import ExecutionProvider, ExecutionResult
from .mission_log import MissionLog
from .models import Mission, MissionStatus, TaskRecord
from .provider_registry import ProviderRegistry, default_registry
from .shell_provider import ShellExecutionProvider

__all__ = [
    "ExecutionProvider",
    "ExecutionResult",
    "Mission",
    "MissionDirector",
    "MissionLog",
    "MissionStatus",
    "ProviderRegistry",
    "ShellExecutionProvider",
    "TaskRecord",
    "default_registry",
]
