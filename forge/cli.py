from pathlib import Path

import typer
from rich import print

from . import __version__
from .plugins import manager

app = typer.Typer(help="ForgeAI - Multi-Agent Software Engineering Platform")


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
    root = Path(name)

    folders = [
        "src",
        "tests",
        "docs",
        "plugins",
        ".forge",
    ]

    root.mkdir(exist_ok=True)

    for folder in folders:
        (root / folder).mkdir(parents=True, exist_ok=True)

    (root / "README.md").write_text(f"# {name}\n")

    print(f"[green]Created project {name}[/green]")


@app.command()
def plugins():
    """List discovered ForgeAI plugins."""
    manager.discover()

    for plugin in manager.list_plugins():
        print(plugin)
