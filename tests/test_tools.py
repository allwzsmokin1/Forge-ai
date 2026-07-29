from __future__ import annotations

import tarfile
import zipfile
from pathlib import Path

from forge.runtime import RuntimeManager, ToolExecutionError


def test_terminal_git_python_and_search_tools(tmp_path: Path) -> None:
    runtime = RuntimeManager(register_builtins=True)
    sample_file = tmp_path / "sample.txt"
    sample_file.write_text("alpha\nbeta\n", encoding="utf-8")

    terminal_result = runtime.execute(
        "terminal",
        payload={"command": ["python", "-c", "print('hello')"]},
    )
    python_result = runtime.execute(
        "python",
        payload={"code": "print('runtime-python')"},
    )
    git_result = runtime.execute(
        "git",
        payload={"args": ["rev-parse", "--is-inside-work-tree"], "cwd": str(Path.cwd())},
    )
    search_result = runtime.execute(
        "search",
        operation="grep",
        payload={"path": str(tmp_path), "pattern": "beta", "glob": "*.txt"},
    )

    assert terminal_result.output["stdout"].strip() == "hello"
    assert python_result.output["stdout"].strip() == "runtime-python"
    assert git_result.output["stdout"].strip() in {"true", "false"}
    assert search_result.output[0]["line"] == "beta"


def test_archive_tool_lists_extracts_and_creates_archives(tmp_path: Path) -> None:
    runtime = RuntimeManager(register_builtins=True)
    source_file = tmp_path / "artifact.txt"
    source_file.write_text("payload", encoding="utf-8")
    zip_path = tmp_path / "artifact.zip"
    tar_path = tmp_path / "artifact.tar.gz"

    runtime.execute(
        "archive",
        operation="create",
        payload={"path": str(zip_path), "items": [str(source_file)]},
    )
    runtime.execute(
        "archive",
        operation="create",
        payload={"path": str(tar_path), "items": [str(source_file)]},
    )

    zip_names = runtime.execute("archive", operation="list", payload={"path": str(zip_path)}).output
    tar_names = runtime.execute("archive", operation="list", payload={"path": str(tar_path)}).output
    extract_dir = tmp_path / "extracted"
    runtime.execute(
        "archive",
        operation="extract",
        payload={"path": str(zip_path), "destination": str(extract_dir)},
    )

    assert zipfile.is_zipfile(zip_path)
    assert tarfile.is_tarfile(tar_path)
    assert zip_names == ["artifact.txt"]
    assert tar_names == ["artifact.txt"]
    assert (extract_dir / "artifact.txt").read_text(encoding="utf-8") == "payload"


def test_archive_tool_blocks_path_traversal_entries(tmp_path: Path) -> None:
    runtime = RuntimeManager(register_builtins=True)
    archive_path = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("../escape.txt", "bad")

    try:
        runtime.execute(
            "archive",
            operation="extract",
            payload={"path": str(archive_path), "destination": str(tmp_path / "extract")},
        )
    except ToolExecutionError as exc:
        assert "outside" in str(exc)
    else:  # pragma: no cover - defensive branch
        raise AssertionError("Expected archive extraction to reject path traversal")


def test_terminal_tool_blocks_sensitive_commands() -> None:
    runtime = RuntimeManager(register_builtins=True)

    try:
        runtime.execute("terminal", payload={"command": ["rm", "-rf", "/tmp/example"]})
    except ToolExecutionError as exc:
        assert "allow_sensitive" in str(exc)
    else:  # pragma: no cover - defensive branch
        raise AssertionError("Expected terminal tool to reject sensitive commands")
