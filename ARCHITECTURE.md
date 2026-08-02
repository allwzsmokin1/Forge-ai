# OrchestrAI Architecture — MVP

> **Scope**: This document describes the MVP architecture only — the minimum required to run one goal with one worker. Components deferred to Version 2 or later are listed in the [Deferred Components](#deferred-components) section with their rationale.

## Overview

The MVP is a three-layer system. A developer submits a goal on the CLI. The Mission Director decomposes it into ordered tasks and executes each one through the Shell integration. Results are printed back to the CLI.

```
┌──────────────────────────────────────────────────┐
│                  CLI (Typer + Rich)               │
├──────────────────────────────────────────────────┤
│               OrchestrAI Kernel                  │
│              Mission Director only               │
├──────────────────────────────────────────────────┤
│          Infrastructure (Config · Logging · JSON) │
└──────────────────────────────────────────────────┘
         │
  TaskAdapter interface
         │
  Shell integration (the one worker)
```

Layers are strictly ordered: each layer only calls downward, never upward.

---

## Layer Descriptions

### Infrastructure Layer

The foundation. Contains no business logic. Provides:

- **JSON storage**: Flat JSON files for run history and configuration. No database required for MVP.
- **Configuration**: YAML file + environment variable overrides via `pydantic-settings`.
- **Logging**: Structured logging via `structlog` (JSON in production, human-readable in development).

### Kernel — Mission Director

The only kernel component in the MVP. Responsible for:

1. Accepting a high-level developer goal as plain text.
2. Calling an LLM (via LiteLLM) to decompose the goal into an ordered list of shell tasks.
3. Iterating over the task list, executing each task through the Shell integration.
4. Tracking task state: `pending → running → complete | failed`.
5. Writing a JSON run record to disk on completion.

The Mission Director does **not** route tasks, manage context windows, or maintain cross-session memory in the MVP. Those responsibilities are deferred.

### Adapter Layer

One interface in the MVP:

```
TaskAdapter    - Execute a single task, return a structured TaskResult
```

`TaskResult` contains: `task_id`, `stdout`, `stderr`, `exit_code`, `duration_ms`.

All other adapter interfaces (`ContextAdapter`, `CapabilityAdapter`, `LifecycleAdapter`) are deferred to Version 2 when a second integration is added.

### Integration Layer — Shell

One integration in the MVP: the **Shell integration**.

The Shell integration wraps any command-line program as a `TaskAdapter`. It receives a task description (a shell command string), executes it as a subprocess, captures stdout/stderr/exit code, and returns a `TaskResult`.

This is the only "worker" in the MVP. All AI tool integrations (Copilot, OpenHands, Claude Code) are deferred to Version 2.

### User Interface — CLI

One interface in the MVP:

```bash
orchestrai run "<goal>"      # Plan and execute a goal
orchestrai history           # Show past run records from JSON store
```

Built on Typer + Rich. The web interface and programmatic API are deferred to Version 2.

---

## Data Flow

```
Developer types: orchestrai run "Audit this codebase for TODOs"
      │
      ▼
  CLI (Typer)
  │  Parse goal string
  │  Call Mission Director
      │
      ▼
  Mission Director
  │  Call LiteLLM: "Decompose this goal into shell commands"
  │  Receive ordered task list: [task_1, task_2, ...]
  │  Write task plan to JSON store
      │
      ▼ (for each task)
  TaskAdapter (Shell integration)
  │  Run shell command as subprocess
  │  Capture stdout, stderr, exit_code
  │  Return TaskResult
      │
      ▼
  Mission Director
  │  Record result in JSON store
  │  Mark task complete or failed
  │  Move to next task or report completion
      │
      ▼
  CLI
  │  Print Rich progress and final summary
      │
      ▼
Developer sees result
```

---

## Key Design Decisions

### Decision 1: Layer Separation

Each layer calls only downward. The Shell integration never calls the kernel. The kernel never calls the CLI. Enforced by import rules in CI.

**Why**: Prevents circular dependencies. Allows any layer to be replaced.

### Decision 2: One Adapter Interface for MVP

Only `TaskAdapter` exists in the MVP. Adding a second integration requires implementing this one interface and nothing more.

**Why**: Every additional interface is a contract that must be maintained across all integrations. With one worker, `CapabilityAdapter`, `ContextAdapter`, and `LifecycleAdapter` add complexity without value.

### Decision 3: JSON Storage for MVP

Task history is written to a flat JSON file in the project directory. No database.

**Why**: SQLite and PostgreSQL are the right choice when multiple sessions, multiple users, or complex queries are needed. For MVP (single developer, single session history), JSON is simpler, more transparent, and requires no migration tooling.

---

## File and Module Structure

```
forge/                        # Package root (current repo name)
├── kernel/
│   ├── __init__.py
│   ├── director.py           # Mission Director
│   └── config.py             # Config loading (pydantic-settings)
│
├── adapters/
│   ├── __init__.py
│   └── task.py               # TaskAdapter interface + TaskResult model
│
├── integrations/
│   ├── __init__.py
│   └── shell/                # Shell integration (the one worker)
│       ├── __init__.py
│       └── adapter.py
│
├── ui/
│   └── cli/
│       ├── __init__.py
│       └── main.py           # Typer CLI entry point
│
├── tests/
│   ├── unit/
│   └── integration/
│
└── examples/
    └── basic_goal/
```

---

## Architectural Constraints

1. **No circular imports** — enforced by CI.
2. **Kernel has no direct imports from `integrations/`** — the kernel sees only `TaskAdapter`.
3. **All configuration goes through `kernel/config.py`** — no hardcoded values.
4. **Every public API is typed** — `mypy --strict` must pass for kernel and adapter code.

---

## Deferred Components

The following components from the original design are explicitly deferred. Each entry states why it is not needed for the MVP and when it becomes necessary.

| Component | Deferred Until | Reason |
|---|---|---|
| **Task Router** | Version 2 (multi-tool) | With one worker, routing is `return shell_worker`. A scoring function adds complexity without value until there are at least two integrations to choose from. |
| **Context Manager** | Version 2 | Injecting relevant context per tool call requires knowing the tool's token budget. With one worker and no token management, the goal string is the only context needed. |
| **Memory Manager** | Version 2 | Cross-session memory and semantic search are valuable but require ChromaDB or a vector store. A simple JSON run log is sufficient for MVP history. |
| **Event Bus** | Version 2 | An in-process pub/sub system decouples components for real-time UI updates and audit logging. With one synchronous CLI workflow, direct function calls are simpler and equally correct. |
| **Plugin System** | Version 3 | `importlib.metadata` entry points enable community integrations distributed as separate packages. This requires a stable adapter interface API and a mature ecosystem — both are Version 2+ concerns. |
| **ContextAdapter interface** | Version 2 | Only needed when a tool requires project context injected into its calls. Not needed for the Shell integration. |
| **CapabilityAdapter interface** | Version 2 | Only needed when the Task Router must score tools against tasks. Not needed with one worker. |
| **LifecycleAdapter interface** | Version 2 | Only needed for integrations that require startup/shutdown (long-running subprocesses or servers). The Shell integration is stateless. |
| **Web UI (FastAPI)** | Version 2 | A browser interface is useful for task timeline visualization and memory browsing. The CLI is sufficient for MVP and faster to build. |
| **Programmatic API** | Version 2 | A stable Python API for third-party scripts is a V2 concern after the internal API stabilizes through MVP usage. |
| **Copilot integration** | Version 2 | A second worker is only useful after the routing layer exists. Adding it before the router creates dead code. |
| **OpenHands integration** | Version 2 | Same as Copilot. |
| **Claude Code integration** | Version 2 | Same as Copilot. |
| **SQLAlchemy + Alembic** | Version 2 | Relational storage and schema migrations are needed for shared team memory and multi-user scenarios. JSON is sufficient for single-developer MVP history. |
| **ChromaDB (semantic memory)** | Version 3 | Semantic search over task history dramatically improves context relevance. Requires an embedding model and vector store. Not needed until Memory Manager V2. |
| **Token-budget-aware context assembly** | Version 2 | Staying within a tool's token limit while maximizing context relevance is a non-trivial problem. It is only worth solving when context injection is implemented. |
| **Multi-user / team features** | Version 3 | Shared memory, per-user namespaces, audit log, and role-based access require PostgreSQL, authentication, and significant infrastructure. |
| **OpenTelemetry / observability** | Version 3 | Traces and metrics are valuable when running OrchestrAI as a persistent service. Not needed for a local CLI tool. |
