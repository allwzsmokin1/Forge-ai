"""Tests for the Forge-AI LLM provider system."""

from forge.agents.coder import CoderAgent
from forge.agents.researcher import ResearchAgent
from forge.llm import LLMProvider, MockLLMProvider, ProviderRegistry, registry
from forge.llm.providers import LLMResponse


class StaticProvider(LLMProvider):
    def __init__(self, name: str, text: str) -> None:
        self._name = name
        self._text = text

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return "Static test provider."

    def generate(self, prompt: str, **kwargs: object) -> LLMResponse:
        return LLMResponse(text=self._text, metadata={"prompt": prompt, "options": kwargs})


def test_mock_provider_generates_code_response() -> None:
    provider = MockLLMProvider()
    response = provider.generate("Write a simple function", task_type="coder")

    assert isinstance(response, LLMResponse)
    assert "def hello_world" in response.text
    assert response.metadata["source"] == "mock"
    assert response.metadata["task_type"] == "coder"


def test_mock_provider_handles_refactor_request() -> None:
    provider = MockLLMProvider()
    response = provider.generate("Refactor this function", task_type="coder")

    assert "compute_total" in response.text
    assert "Refactored" in response.text


def test_mock_provider_returns_empty_text_for_empty_prompt() -> None:
    provider = MockLLMProvider()
    response = provider.generate("", task_type="coder")

    assert response.text == ""
    assert response.metadata["source"] == "mock"


def test_provider_registry_default_and_custom_registration() -> None:
    local_registry = ProviderRegistry()
    provider = MockLLMProvider()
    local_registry.register(provider)

    assert local_registry.get() is provider
    assert local_registry.get("mock") is provider
    assert "mock" in tuple(local_registry.list_providers())


def test_provider_registry_falls_back_to_default_unknown_provider() -> None:
    local_registry = ProviderRegistry()

    assert local_registry.get("unknown").name == "mock"


def test_provider_registry_set_default_supports_registered_provider() -> None:
    local_registry = ProviderRegistry()
    provider = StaticProvider("static", "CODE:\npass\nEXPLANATION:\ncustom")
    local_registry.register(provider)

    local_registry.set_default("static")

    assert local_registry.get() is provider


def test_coder_agent_uses_selected_provider() -> None:
    original_provider_name = registry.get().name
    provider = StaticProvider(
        "coder-test",
        "CODE:\ndef custom() -> str:\n    return 'ok'\nEXPLANATION:\nCustom response",
    )
    registry.register(provider)
    registry.set_default(provider.name)

    try:
        result = CoderAgent().run("Write something")
    finally:
        registry.set_default(original_provider_name)

    assert result.code == "def custom() -> str:\n    return 'ok'"
    assert result.explanation == "Custom response"


def test_coder_agent_handles_unstructured_provider_response() -> None:
    original_provider_name = registry.get().name
    provider = StaticProvider("coder-unstructured", "def fallback() -> str:\n    return 'ok'")
    registry.register(provider)
    registry.set_default(provider.name)

    try:
        result = CoderAgent().run("Write something")
    finally:
        registry.set_default(original_provider_name)

    assert result.code == "def fallback() -> str:\n    return 'ok'"
    assert result.explanation == ""


def test_research_agent_uses_selected_provider() -> None:
    original_provider_name = registry.get().name
    provider = StaticProvider(
        "research-test",
        "FINDINGS:\nCustom findings\nRECOMMENDATIONS:\nCustom recommendations",
    )
    registry.register(provider)
    registry.set_default(provider.name)

    try:
        result = ResearchAgent().run("Async patterns")
    finally:
        registry.set_default(original_provider_name)

    assert result.topic == "Async patterns"
    assert result.findings == "Custom findings"
    assert result.recommendations == "Custom recommendations"


def test_research_agent_handles_unstructured_provider_response() -> None:
    original_provider_name = registry.get().name
    provider = StaticProvider("research-unstructured", "Fallback research guidance")
    registry.register(provider)
    registry.set_default(provider.name)

    try:
        result = ResearchAgent().run("Async patterns")
    finally:
        registry.set_default(original_provider_name)

    assert result.topic == "Async patterns"
    assert result.findings == "Fallback research guidance"
    assert result.recommendations == ""
