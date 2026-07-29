"""Tests for built-in Stage 4 tools."""

from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from forge.tools import (
    ArchiveTool,
    DockerTool,
    FilesystemTool,
    PythonTool,
    SearchTool,
    TerminalTool,
    ToolExecutionRequest,
    WebTool,
)


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"hello")

    def log_message(self, *_args) -> None:
        return


def test_terminal_tool_runs_command() -> None:
    result = TerminalTool().execute(ToolExecutionRequest(action="run", payload={"command": "echo ok"}))

    assert result.success is True
    assert "ok" in result.data["stdout"]


def test_filesystem_tool_read_write(tmp_path: Path) -> None:
    file_path = tmp_path / "file.txt"
    tool = FilesystemTool()

    write_result = tool.execute(
        ToolExecutionRequest(action="write_text", payload={"path": str(file_path), "content": "data"})
    )
    read_result = tool.execute(ToolExecutionRequest(action="read_text", payload={"path": str(file_path)}))

    assert write_result.success is True
    assert read_result.data == "data"


def test_python_tool_executes_code() -> None:
    result = PythonTool().execute(
        ToolExecutionRequest(action="exec", payload={"code": "print('hello')"})
    )

    assert result.success is True
    assert "hello" in result.data["stdout"]


def test_search_tool_glob_and_grep(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("print('x')\n", encoding="utf-8")
    (tmp_path / "b.txt").write_text("note\n", encoding="utf-8")
    tool = SearchTool()

    glob_result = tool.execute(
        ToolExecutionRequest(action="glob", payload={"root": str(tmp_path), "pattern": "*.py"})
    )
    grep_result = tool.execute(
        ToolExecutionRequest(
            action="grep",
            payload={"root": str(tmp_path), "pattern": "print", "include": "*.py"},
        )
    )

    assert len(glob_result.data) == 1
    assert grep_result.success is True
    assert grep_result.data[0]["line"] == 1


def test_archive_tool_create_extract(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "file.txt").write_text("archive", encoding="utf-8")
    archive_base = str(tmp_path / "bundle")
    output_dir = tmp_path / "out"

    tool = ArchiveTool()
    create_result = tool.execute(
        ToolExecutionRequest(
            action="create",
            payload={"source": str(source), "output": archive_base, "format": "zip"},
        )
    )
    extract_result = tool.execute(
        ToolExecutionRequest(
            action="extract",
            payload={"archive": create_result.data["archive"], "target": str(output_dir)},
        )
    )

    assert create_result.success is True
    assert extract_result.success is True
    assert (output_dir / "file.txt").exists()


def test_web_tool_fetches_content() -> None:
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}/"

    try:
        result = WebTool().execute(ToolExecutionRequest(action="fetch", payload={"url": url}))
    finally:
        server.shutdown()
        thread.join()

    assert result.success is True
    assert result.data["status"] == 200
    assert "hello" in result.data["body"]


def test_docker_tool_health_check_returns_result() -> None:
    result = DockerTool().health_check()

    assert isinstance(result.success, bool)
