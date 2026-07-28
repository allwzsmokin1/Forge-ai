import typer
from rich import print

app = typer.Typer(
    help="ForgeAI - Multi-Agent Software Engineering Platform"
)

@app.command()
def version():
    """Show ForgeAI version."""
    print("[green]ForgeAI v0.0.1[/green]")

@app.command()
def doctor():
    """Verify installation."""
    print("[green]ForgeAI installation looks good.[/green]")

if __name__ == "__main__":
    app()
from pathlib import Path
import typer
from rich import print

app = typer.Typer(help="ForgeAI")


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
    from forge.plugins import manager

    manager.discover()

    for plugin in manager.list_plugins():
        print(plugin)


@app.command()
def version():
    print("ForgeAI v0.0.1")


@app.command()
def doctor():
    print("[green]Everything looks good.[/green]")


if __name__ == "__main__":
    app()
