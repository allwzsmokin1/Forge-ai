"""Tests for the Forge-AI LLM provider system."""

from forge.llm import ProviderRegistry, MockLLMProvider, registry
from forge.llm.providers import LLMResponse


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
