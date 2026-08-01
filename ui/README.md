# UI

The `ui/` directory contains all user-facing interfaces for OrchestrAI.

## Structure

```
ui/
├── cli/                 # Command-line interface (primary)
│   ├── __init__.py
│   └── main.py          # Typer CLI entry point
└── web/                 # Optional web interface
    ├── __init__.py
    └── app.py           # FastAPI application
```

## CLI (Primary Interface)

Built on [Typer](https://typer.tiangolo.com/) with [Rich](https://rich.readthedocs.io/) output formatting.

Planned commands:

| Command | Description |
|---|---|
| `orchestrai init` | Initialize OrchestrAI in a project |
| `orchestrai run "<goal>"` | Execute a goal |
| `orchestrai history` | Show past task runs |
| `orchestrai context` | Display current project context |
| `orchestrai remember "<fact>"` | Add a fact to project memory |
| `orchestrai tools` | List registered tools and their status |
| `orchestrai tools add <integration>` | Register a new tool |

## Web Interface (Optional)

Built on [FastAPI](https://fastapi.tiangolo.com/). Provides a browser-based interface and a REST API for programmatic access.

The web interface is optional — the CLI covers all functionality. It is planned for **Milestone 6**.

## Design Principle

The UI layer is thin. It translates user input into kernel calls and formats kernel output for display. No business logic lives here.
