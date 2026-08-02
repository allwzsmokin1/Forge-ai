"""Unit tests for forge.kernel.shell_provider.ShellExecutionProvider."""

import pytest

from forge.kernel.execution_provider import ExecutionResult
from forge.kernel.shell_provider import ShellExecutionProvider, _is_safe


class TestIsSafe:
    @pytest.mark.parametrize(
        "cmd",
        [
            "rm -rf /",
            "rm file.txt",
            "sudo apt install vim",
            "sudo rm file",
            "mkfs.ext4 /dev/sda",
            "dd if=/dev/zero of=/dev/sda",
            "> /dev/sda",
            ":(){ :|:& };:",
        ],
    )
    def test_blocked_commands(self, cmd):
        assert _is_safe(cmd) is False

    @pytest.mark.parametrize(
        "cmd",
        [
            "echo hello",
            "ls -la",
            "cat README.md",
            "python --version",
            "pytest tests/",
        ],
    )
    def test_allowed_commands(self, cmd):
        assert _is_safe(cmd) is True


class TestShellExecutionProvider:
    def test_echo_returns_stdout(self):
        p = ShellExecutionProvider()
        result = p.execute('echo "Mission Complete"')
        assert result.stdout == "Mission Complete"
        assert result.exit_code == 0
        assert result.succeeded is True
        assert result.duration_ms >= 0

    def test_exit_code_propagated_on_failure(self):
        p = ShellExecutionProvider()
        # `false` is a standard shell command that always exits with 1
        result = p.execute("false")
        assert result.exit_code != 0
        assert result.succeeded is False

    def test_stderr_captured(self):
        p = ShellExecutionProvider()
        result = p.execute("echo error_msg >&2")
        assert "error_msg" in result.stderr

    def test_blocked_command_raises_value_error(self):
        p = ShellExecutionProvider()
        with pytest.raises(ValueError, match="blocked"):
            p.execute("rm -rf /")

    def test_result_is_execution_result_instance(self):
        p = ShellExecutionProvider()
        result = p.execute("echo hi")
        assert isinstance(result, ExecutionResult)

    def test_multi_word_echo(self):
        p = ShellExecutionProvider()
        result = p.execute("echo hello world")
        assert result.stdout == "hello world"

    def test_timeout_returns_negative_exit_code(self):
        p = ShellExecutionProvider(timeout=0.01)
        result = p.execute("sleep 10")
        assert result.exit_code == -1
        assert "timed out" in result.stderr.lower()

    def test_duration_is_positive(self):
        p = ShellExecutionProvider()
        result = p.execute("echo fast")
        assert result.duration_ms > 0
