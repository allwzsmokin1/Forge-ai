from pathlib import Path

import typer
from rich import print
from rich.panel import Panel
from rich.table import Table

from . import __version__
from .kernel import MissionDirector, MissionLog, MissionStatus
from .plugins import manager

app = typer.Typer(help="OrchestrAI — AI Operating Environment")


@app.command()
def version():
    """Show OrchestrAI version."""
    print(f"[green]OrchestrAI v{__version__}[/green]")


@app.command()
def doctor():
    """Verify installation."""
    print("[green]OrchestrAI installation looks good.[/green]")


@app.command()
def run(
    goal: str = typer.Argument(..., help="Shell command or goal to execute."),
    log_dir: str = typer.Option(
        None, "--log-dir", "-l", help="Directory for the JSON mission log (default: .forge/)."
    ),
):
    """Create, execute, and log a mission for GOAL.

    Example:

        orchestrai run "echo hello"
    """
    log = MissionLog(log_dir=log_dir) if log_dir else MissionLog()
    director = MissionDirector(log=log)

    print(f"\n[bold cyan]Mission Director[/bold cyan]  goal=[italic]{goal}[/italic]")

    mission = director.run(goal)

    # ── Status panel ──────────────────────────────────────────────────
    status_colour = "green" if mission.status == MissionStatus.COMPLETED else "red"
    status_label = mission.status.value.upper()

    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("key", style="bold")
    table.add_column("value")
    table.add_row("Mission ID", mission.mission_id)
    table.add_row("Status", f"[{status_colour}]{status_label}[/{status_colour}]")
    table.add_row("Created", mission.created_at)
    table.add_row("Finished", mission.finished_at or "—")

    if mission.task:
        table.add_row("Command", mission.task.command)
        table.add_row("Exit code", str(mission.task.exit_code))
        table.add_row("Duration", f"{mission.task.duration_ms:.1f} ms")
        if mission.task.stdout:
            table.add_row("stdout", mission.task.stdout)
        if mission.task.stderr:
            table.add_row("stderr", mission.task.stderr)

    if mission.error:
        table.add_row("Error", f"[red]{mission.error}[/red]")

    print(Panel(table, title=f"[{status_colour}]{status_label}[/{status_colour}]", expand=False))
    print(f"\n[dim]Mission log → {log.log_path}[/dim]\n")

    if mission.status != MissionStatus.COMPLETED:
        raise typer.Exit(code=1)


@app.command()
def history(
    log_dir: str = typer.Option(
        None, "--log-dir", "-l", help="Directory for the JSON mission log (default: .forge/)."
    ),
):
    """Show past mission records from the JSON log."""
    log = MissionLog(log_dir=log_dir) if log_dir else MissionLog()
    records = log.read_all()

    if not records:
        print("[yellow]No missions recorded yet.[/yellow]")
        return

    table = Table(title="Mission History", show_lines=True)
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Goal")
    table.add_column("Status")
    table.add_column("Finished")

    for rec in records:
        status = rec.get("status", "unknown")
        colour = "green" if status == "completed" else "red"
        table.add_row(
            rec.get("mission_id", "")[:8],
            rec.get("goal", ""),
            f"[{colour}]{status}[/{colour}]",
            rec.get("finished_at") or "—",
        )

    print(table)


@app.command()
def init(name: str):
    """Create a new OrchestrAI project directory."""
    root = Path(name)

    folders = ["src", "tests", "docs", "plugins", ".forge"]
    root.mkdir(exist_ok=True)
    for folder in folders:
        (root / folder).mkdir(parents=True, exist_ok=True)

    (root / "README.md").write_text(f"# {name}\n")
    print(f"[green]Created project {name}[/green]")


@app.command()
def plugins():
    """List discovered OrchestrAI plugins."""
    manager.discover()
    for plugin in manager.list_plugins():
        print(plugin)

