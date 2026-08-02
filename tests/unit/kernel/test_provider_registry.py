"""Unit tests for forge.kernel.provider_registry.ProviderRegistry."""

from __future__ import annotations

import pytest

from forge.kernel.execution_provider import ExecutionProvider, ExecutionResult
from forge.kernel.provider_registry import ProviderRegistry, default_registry
from forge.kernel.shell_provider import ShellExecutionProvider


# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------


class _StubProvider(ExecutionProvider):
    """Minimal provider that records executed commands."""

    def __init__(self, name: str = "stub") -> None:
        self.name = name
        self.calls: list[str] = []

    def execute(self, command: str) -> ExecutionResult:
        self.calls.append(command)
        return ExecutionResult(stdout=self.name, stderr="", exit_code=0, duration_ms=0.0)


class _AnotherProvider(ExecutionProvider):
    def execute(self, command: str) -> ExecutionResult:
        return ExecutionResult(stdout="another", stderr="", exit_code=0, duration_ms=0.0)


# ---------------------------------------------------------------------------
# ProviderRegistry — registration
# ---------------------------------------------------------------------------


class TestProviderRegistryRegister:
    def test_register_and_get_roundtrip(self):
        reg = ProviderRegistry()
        p = _StubProvider()
        reg.register("stub", p)
        assert reg.get("stub") is p

    def test_register_replaces_existing_entry(self):
        reg = ProviderRegistry()
        first = _StubProvider("first")
        second = _StubProvider("second")
        reg.register("x", first)
        reg.register("x", second)
        assert reg.get("x") is second

    def test_register_multiple_providers(self):
        reg = ProviderRegistry()
        reg.register("a", _StubProvider("a"))
        reg.register("b", _StubProvider("b"))
        assert len(reg) == 2

    def test_register_raises_for_non_provider(self):
        reg = ProviderRegistry()
        with pytest.raises(TypeError, match="ExecutionProvider"):
            reg.register("bad", object())  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# ProviderRegistry — get
# ---------------------------------------------------------------------------


class TestProviderRegistryGet:
    def test_get_returns_registered_instance(self):
        reg = ProviderRegistry()
        p = _StubProvider()
        reg.register("mine", p)
        assert reg.get("mine") is p

    def test_get_missing_raises_key_error(self):
        reg = ProviderRegistry()
        with pytest.raises(KeyError, match="'ghost'"):
            reg.get("ghost")

    def test_get_error_lists_available_providers(self):
        reg = ProviderRegistry()
        reg.register("shell", ShellExecutionProvider())
        with pytest.raises(KeyError, match="shell"):
            reg.get("missing")

    def test_get_error_message_says_none_when_empty(self):
        reg = ProviderRegistry()
        with pytest.raises(KeyError, match="<none>"):
            reg.get("anything")


# ---------------------------------------------------------------------------
# ProviderRegistry — list_names
# ---------------------------------------------------------------------------


class TestProviderRegistryListNames:
    def test_empty_registry_returns_empty_list(self):
        reg = ProviderRegistry()
        assert reg.list_names() == []

    def test_list_names_returns_all_registered(self):
        reg = ProviderRegistry()
        reg.register("beta", _StubProvider())
        reg.register("alpha", _StubProvider())
        assert reg.list_names() == ["alpha", "beta"]

    def test_list_names_is_sorted(self):
        reg = ProviderRegistry()
        for name in ["z", "a", "m"]:
            reg.register(name, _StubProvider())
        assert reg.list_names() == ["a", "m", "z"]

    def test_list_names_returns_new_list_each_call(self):
        reg = ProviderRegistry()
        reg.register("x", _StubProvider())
        first = reg.list_names()
        second = reg.list_names()
        assert first == second
        assert first is not second


# ---------------------------------------------------------------------------
# ProviderRegistry — __len__ and __contains__
# ---------------------------------------------------------------------------


class TestProviderRegistryDunderMethods:
    def test_len_empty(self):
        assert len(ProviderRegistry()) == 0

    def test_len_after_register(self):
        reg = ProviderRegistry()
        reg.register("a", _StubProvider())
        reg.register("b", _StubProvider())
        assert len(reg) == 2

    def test_contains_true_for_registered(self):
        reg = ProviderRegistry()
        reg.register("shell", ShellExecutionProvider())
        assert "shell" in reg

    def test_contains_false_for_missing(self):
        reg = ProviderRegistry()
        assert "ghost" not in reg


# ---------------------------------------------------------------------------
# default_registry
# ---------------------------------------------------------------------------


class TestDefaultRegistry:
    def test_default_registry_is_provider_registry_instance(self):
        assert isinstance(default_registry, ProviderRegistry)

    def test_shell_provider_pre_registered(self):
        assert "shell" in default_registry

    def test_shell_provider_is_shell_execution_provider(self):
        assert isinstance(default_registry.get("shell"), ShellExecutionProvider)

    def test_list_names_includes_shell(self):
        assert "shell" in default_registry.list_names()

    def test_runtime_registration_does_not_require_director_changes(self):
        """Adding a new provider to the default registry is self-contained."""
        reg = ProviderRegistry()
        reg.register("shell", ShellExecutionProvider())
        # Simulates adding CopilotExecutionProvider at runtime
        stub = _StubProvider("copilot")
        reg.register("copilot", stub)
        assert reg.get("copilot") is stub
        assert "shell" in reg.list_names()
        assert "copilot" in reg.list_names()


# ---------------------------------------------------------------------------
# MissionDirector integration — provider_name lookup
# ---------------------------------------------------------------------------


class TestMissionDirectorProviderName:
    """MissionDirector can resolve a provider by name via the registry."""

    def _make_registry_with_stub(self) -> tuple[ProviderRegistry, _StubProvider]:
        reg = ProviderRegistry()
        stub = _StubProvider("test")
        reg.register("test", stub)
        return reg, stub

    def test_provider_name_resolves_from_default_registry(self, tmp_path):
        from forge.kernel.director import MissionDirector
        from forge.kernel.mission_log import MissionLog
        from forge.kernel.models import MissionStatus

        log = MissionLog(log_dir=tmp_path)
        d = MissionDirector(provider_name="shell", log=log)
        mission = d.run("echo registry")
        assert mission.status == MissionStatus.COMPLETED

    def test_provider_name_unknown_raises_key_error(self, tmp_path):
        from forge.kernel.director import MissionDirector
        from forge.kernel.mission_log import MissionLog

        log = MissionLog(log_dir=tmp_path)
        with pytest.raises(KeyError, match="'unknown'"):
            MissionDirector(provider_name="unknown", log=log)

    def test_explicit_provider_overrides_default(self, tmp_path):
        from forge.kernel.director import MissionDirector
        from forge.kernel.mission_log import MissionLog

        stub = _StubProvider("explicit")
        log = MissionLog(log_dir=tmp_path)
        d = MissionDirector(provider=stub, log=log)
        d.run("echo hi")
        assert stub.calls == ["echo hi"]
