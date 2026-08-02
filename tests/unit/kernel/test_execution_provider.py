"""Unit tests for forge.kernel.execution_provider."""

import dataclasses

import pytest

from forge.kernel.execution_provider import ExecutionProvider, ExecutionResult


class TestExecutionResult:
    def test_succeeded_true_for_zero_exit(self):
        r = ExecutionResult(stdout="ok", stderr="", exit_code=0, duration_ms=1.0)
        assert r.succeeded is True

    def test_succeeded_false_for_nonzero_exit(self):
        r = ExecutionResult(stdout="", stderr="fail", exit_code=127, duration_ms=1.0)
        assert r.succeeded is False

    def test_is_frozen(self):
        r = ExecutionResult(stdout="x", stderr="", exit_code=0, duration_ms=1.0)
        with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
            r.stdout = "mutated"  # type: ignore[misc]


class TestExecutionProviderABC:
    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            ExecutionProvider()  # type: ignore[abstract]

    def test_concrete_subclass_must_implement_execute(self):
        class Incomplete(ExecutionProvider):
            pass

        with pytest.raises(TypeError):
            Incomplete()  # type: ignore[abstract]

    def test_concrete_subclass_works_when_execute_implemented(self):
        class Stub(ExecutionProvider):
            def execute(self, command: str) -> ExecutionResult:
                return ExecutionResult(
                    stdout="stubbed", stderr="", exit_code=0, duration_ms=0.0
                )

        provider = Stub()
        result = provider.execute("anything")
        assert result.stdout == "stubbed"
        assert result.succeeded is True
