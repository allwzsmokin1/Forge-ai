"""Permission controls for runtime tool access."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass


@dataclass(frozen=True)
class PermissionDecision:
    allowed: bool
    reason: str


class PermissionManager:
    """Manage tool permission grants by agent."""

    def __init__(self) -> None:
        self._permissions: dict[str, set[str]] = defaultdict(set)

    def grant(self, agent_name: str, permission: str) -> None:
        self._permissions[agent_name].add(permission)

    def grant_many(self, agent_name: str, permissions: tuple[str, ...] | list[str]) -> None:
        self._permissions[agent_name].update(permissions)

    def check(self, agent_name: str, required: tuple[str, ...]) -> PermissionDecision:
        granted = self._permissions.get(agent_name, set())
        if "*" in granted:
            return PermissionDecision(allowed=True, reason="Wildcard permission granted")

        missing = [permission for permission in required if permission not in granted]
        if missing:
            return PermissionDecision(
                allowed=False,
                reason=f"Missing permissions for {agent_name}: {', '.join(sorted(missing))}",
            )
        return PermissionDecision(allowed=True, reason="Permissions satisfied")
