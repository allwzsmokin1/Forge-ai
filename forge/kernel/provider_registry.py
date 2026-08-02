"""ProviderRegistry — discovers and manages ExecutionProvider implementations.

The registry is the single place where provider names are mapped to concrete
:class:`~forge.kernel.execution_provider.ExecutionProvider` instances.  The
Mission Director (and any other caller) can request a provider by name without
importing or instantiating the concrete class.

Usage::

    from forge.kernel.provider_registry import default_registry

    # Look up the built-in shell provider
    provider = default_registry.get("shell")

    # Register a new provider at runtime (no Mission Director changes needed)
    default_registry.register("copilot", CopilotExecutionProvider())

The module ships with a single pre-registered provider:

* ``"shell"`` → :class:`~forge.kernel.shell_provider.ShellExecutionProvider`

Adding ``CopilotExecutionProvider``, ``OpenHandsExecutionProvider``,
``ClaudeExecutionProvider``, or any future provider requires only a
``default_registry.register(...)`` call — the Mission Director is untouched.
"""

from __future__ import annotations

from .execution_provider import ExecutionProvider
from .shell_provider import ShellExecutionProvider


class ProviderRegistry:
    """A name-to-instance registry for :class:`ExecutionProvider` objects.

    Args:
        None.  Start empty and populate with :meth:`register`.
    """

    def __init__(self) -> None:
        self._providers: dict[str, ExecutionProvider] = {}

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def register(self, name: str, provider: ExecutionProvider) -> None:
        """Register *provider* under *name*, replacing any existing entry.

        Args:
            name:     Case-sensitive string key (e.g. ``"shell"``).
            provider: A concrete :class:`ExecutionProvider` instance.

        Raises:
            TypeError: If *provider* is not an :class:`ExecutionProvider`.
        """
        if not isinstance(provider, ExecutionProvider):
            raise TypeError(
                f"provider must be an ExecutionProvider instance, got {type(provider)!r}"
            )
        self._providers[name] = provider

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def get(self, name: str) -> ExecutionProvider:
        """Return the provider registered under *name*.

        Args:
            name: The key used when :meth:`register` was called.

        Returns:
            The :class:`ExecutionProvider` instance.

        Raises:
            KeyError: If no provider is registered under *name*.
        """
        try:
            return self._providers[name]
        except KeyError:
            available = ", ".join(self._providers) or "<none>"
            raise KeyError(
                f"Provider {name!r} not found. Available providers: {available}"
            ) from None

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def list_names(self) -> list[str]:
        """Return a sorted list of registered provider names.

        Returns:
            A new list of name strings in alphabetical order.
        """
        return sorted(self._providers)

    def __len__(self) -> int:
        return len(self._providers)

    def __contains__(self, name: object) -> bool:
        return name in self._providers


# ---------------------------------------------------------------------------
# Module-level default registry
# ---------------------------------------------------------------------------

#: Singleton registry pre-loaded with :class:`ShellExecutionProvider`.
#: Import and call ``default_registry.register(name, provider)`` to add new
#: providers without touching the Mission Director.
default_registry: ProviderRegistry = ProviderRegistry()
default_registry.register("shell", ShellExecutionProvider())
