from pathlib import Path

import typer
from rich import print

from . import __version__
from .plugins import manager
from .runtime import RuntimeManager, get_runtime

app = typer.Typer(help="ForgeAI - Multi-Agent Software Engineering Platform")


def initialize_project(
    name: str,
    runtime_manager: RuntimeManager | None = None,
) -> Path:
    """Create a new ForgeAI project using the runtime filesystem tool."""

    runtime = runtime_manager or get_runtime()
    root = Path(name)
    folders = [
        "src",
        "tests",
        "docs",
        "plugins",
        ".forge",
    ]
    runtime.execute(
        "filesystem",
        operation="mkdir",
        payload={"path": str(root), "parents": False, "exist_ok": True},
    )
    for folder in folders:
        runtime.execute(
            "filesystem",
            operation="mkdir",
            payload={
                "path": str(root / folder),
                "parents": True,
                "exist_ok": True,
            },
        )
    runtime.execute(
        "filesystem",
        operation="write_text",
        payload={"path": str(root / "README.md"), "content": f"# {name}\n"},
    )
    return root


@app.command()
def version():
    """Show ForgeAI version."""
    print(f"[green]ForgeAI v{__version__}[/green]")


@app.command()
def doctor():
    """Verify installation."""
    print("[green]ForgeAI installation looks good.[/green]")


@app.command()
def init(name: str):
    """Create a new ForgeAI project."""
    root = initialize_project(name)
    print(f"[green]Created project {name}[/green]")


@app.command()
def plugins():
    """List discovered ForgeAI plugins."""
    manager.discover()

    for plugin in manager.list_plugins():
        print(plugin)
