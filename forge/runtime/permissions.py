"""Permission policy for runtime-managed tool usage."""

from __future__ import annotations


class PermissionPolicy:
    """Capability policy with optional default-allow behavior."""

    def __init__(self, allow_by_default: bool = True) -> None:
        self._allow_by_default = allow_by_default
        self._grants: dict[str, set[str]] = {}

    def grant(self, agent: str, capability: str) -> None:
        self._grants.setdefault(agent, set()).add(capability)

    def revoke(self, agent: str, capability: str) -> None:
        self._grants.setdefault(agent, set()).discard(capability)

    def is_allowed(self, agent: str, capability: str) -> bool:
        agent_grants = self._grants.get(agent)
        if agent_grants is None:
            return self._allow_by_default
        return capability in agent_grants
