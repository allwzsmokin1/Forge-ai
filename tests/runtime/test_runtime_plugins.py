"""Tests for runtime plugin discovery."""

from __future__ import annotations

import sys
from pathlib import Path

from forge.runtime.plugins import PluginDiscovery


def test_discover_package_tools(tmp_path: Path) -> None:
    package_root = tmp_path / "plugins_pkg"
    package_root.mkdir()
    (package_root / "__init__.py").write_text("", encoding="utf-8")
    (package_root / "sample.py").write_text(
        "from forge.tools.base import BaseTool, ToolExecutionRequest, ToolExecutionResult\n"
        "class SampleTool(BaseTool):\n"
        "    name='sample'\n"
        "    capabilities=('sample',)\n"
        "    def execute(self, request: ToolExecutionRequest) -> ToolExecutionResult:\n"
        "        del request\n"
        "        return ToolExecutionResult(success=True, data='ok')\n"
        "def load_tool():\n"
        "    return SampleTool()\n",
        encoding="utf-8",
    )

    sys.path.insert(0, str(tmp_path))
    try:
        tools = PluginDiscovery().discover_package_tools("plugins_pkg")
    finally:
        sys.path.remove(str(tmp_path))

    assert len(tools) == 1
    assert tools[0].name == "sample"
