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
