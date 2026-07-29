"""Registry for LLM providers used by Forge-AI components."""

from __future__ import annotations

from typing import Dict, Iterable, Optional

from .providers import LLMProvider, MockLLMProvider


class ProviderRegistry:
    """Registry that manages available LLM providers."""

    def __init__(self) -> None:
        self._providers: Dict[str, LLMProvider] = {}
        self._default_provider = MockLLMProvider()
        self.register(self._default_provider)

    def register(self, provider: LLMProvider) -> None:
        self._providers[provider.name] = provider
        if provider.name == self._default_provider.name:
            self._default_provider = provider

    def get(self, name: Optional[str] = None) -> LLMProvider:
        if name is None:
            return self._default_provider
        return self._providers.get(name, self._default_provider)

    def list_providers(self) -> Iterable[str]:
        return tuple(self._providers.keys())

    def set_default(self, name: str) -> None:
        provider = self._providers.get(name)
        if provider is None:
            raise KeyError(f"Unknown provider: {name}")
        self._default_provider = provider


registry = ProviderRegistry()
