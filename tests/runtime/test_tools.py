from __future__ import annotations

from forge.runtime import ToolContext
from forge.tools import (
    ArchiveTool,
    DockerTool,
    FilesystemTool,
    GitTool,
    PythonTool,
    SearchTool,
    TerminalTool,
    WebTool,
)


def _context() -> ToolContext:
    return ToolContext(request_id="1", agent="tester", capability="test", dependencies={})


def test_filesystem_tool_round_trip(tmp_path) -> None:
    tool = FilesystemTool()
    path = tmp_path / "sample.txt"

    write_result = tool.execute(
        {"operation": "write", "path": str(path), "content": "hello"},
        _context(),
    )
    read_result = tool.execute({"operation": "read", "path": str(path)}, _context())
    list_result = tool.execute({"operation": "list", "path": str(tmp_path)}, _context())

    assert write_result.success
    assert read_result.output == "hello"
    assert "sample.txt" in list_result.output


def test_archive_tool_create_and_extract(tmp_path) -> None:
    source_dir = tmp_path / "src"
    source_dir.mkdir()
    (source_dir / "a.txt").write_text("data", encoding="utf-8")
    archive_path = tmp_path / "out" / "data.zip"
    extract_dir = tmp_path / "extract"

    tool = ArchiveTool()
    created = tool.execute(
        {"operation": "create", "source": str(source_dir), "destination": str(archive_path)},
        _context(),
    )
    extracted = tool.execute(
        {"operation": "extract", "source": str(archive_path), "destination": str(extract_dir)},
        _context(),
    )

    assert created.success
    assert extracted.success
    assert (extract_dir / "a.txt").read_text(encoding="utf-8") == "data"


def test_terminal_python_git_tools_execute() -> None:
    terminal = TerminalTool()
    python_tool = PythonTool()
    git_tool = GitTool()

    terminal_result = terminal.execute({"command": "printf runtime"}, _context())
    python_result = python_tool.execute({"code": "print('runtime')"}, _context())
    git_result = git_tool.execute({"args": ["--version"]}, _context())

    assert terminal_result.success
    assert "runtime" in terminal_result.output["stdout"]
    assert python_result.success
    assert "runtime" in python_result.output["stdout"]
    assert git_result.success
    assert "git version" in git_result.output["stdout"]


def test_search_tool_finds_matches(tmp_path) -> None:
    (tmp_path / "one.txt").write_text("alpha beta alpha", encoding="utf-8")
    (tmp_path / "two.txt").write_text("beta gamma", encoding="utf-8")
    tool = SearchTool()

    result = tool.execute({"root": str(tmp_path), "pattern": "alpha", "glob": "*.txt"}, _context())

    assert result.success
    assert result.output == [{"path": str(tmp_path / "one.txt"), "matches": 2}]


def test_docker_tool_handles_missing_binary() -> None:
    result = DockerTool().execute({"args": ["ps"]}, _context())

    assert isinstance(result.success, bool)
    if not result.success:
        assert "docker" in (result.error or "")


def test_web_tool_fetches_content(monkeypatch) -> None:
    class FakeResponse:
        status = 200

        def __init__(self, body: bytes) -> None:
            self._body = body

        def read(self) -> bytes:
            return self._body

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

    monkeypatch.setattr(
        "forge.tools.web.urlopen",
        lambda url, timeout=10: FakeResponse(b"ok"),
    )

    result = WebTool().execute({"url": "https://example.com"}, _context())

    assert result.success
    assert result.output["status"] == 200
    assert result.output["body"] == "ok"
