# OrchestrAI Architecture

## Overview

OrchestrAI is structured as a layered system. The layers are strictly ordered: higher layers depend on lower layers, never the reverse. This constraint is enforced at the code level through module boundaries and is what makes individual components replaceable.

```
┌──────────────────────────────────────────────────────────────┐
│                        User Interfaces                        │
│              CLI (Typer) · Web UI (optional) · API            │
├──────────────────────────────────────────────────────────────┤
│                      OrchestrAI Kernel                        │
│         Mission Director · Task Router · Context Manager      │
│                     Memory Manager                            │
├──────────────────────────────────────────────────────────────┤
│                     Adapter Layer                             │
│    Standardized interfaces every integration must implement   │
├──────────────────────────────────────────────────────────────┤
│                   Integration Layer                           │
│   Copilot · OpenHands · Claude Code · Codex · Custom tools   │
├──────────────────────────────────────────────────────────────┤
│                   Infrastructure Layer                        │
│    Storage · Logging · Config · Event Bus · Plugin System    │
└──────────────────────────────────────────────────────────────┘
```

---

## Layer Descriptions

### Infrastructure Layer

The foundation. Contains no business logic. Provides:

- **Storage abstraction**: Key-value and document storage with pluggable backends (JSON → SQLite → PostgreSQL).
- **Configuration**: File-based configuration using YAML with environment variable overrides.
- **Logging**: Structured logging (JSON output in production, human-readable in development).
- **Event Bus**: In-process publish/subscribe for decoupled communication between components.
- **Plugin System**: Discovery and loading of external plugins without modifying core code.

No component in a higher layer calls storage or disk directly. All persistence goes through the storage abstraction.

### Integration Layer

Concrete implementations of connections to external AI tools and services.

Each integration is a self-contained Python package located in `integrations/<tool-name>/`. An integration knows how to:

- Start and stop the tool.
- Send a task to the tool.
- Receive structured output from the tool.
- Report capability metadata (what tasks this tool handles well).

Integrations have **no direct dependencies on the kernel**. They communicate upward through the adapter interfaces only.

### Adapter Layer

The contract between integrations and the kernel.

Every integration implements one or more adapter interfaces. The kernel depends only on these interfaces, never on concrete integrations. This is the dependency inversion boundary that makes OrchestrAI extensible.

Core adapter interfaces:

```
TaskAdapter          - Execute a single task, return structured result
ContextAdapter       - Read/write project context for a tool
CapabilityAdapter    - Declare what this tool is good at
LifecycleAdapter     - Start, stop, health-check a tool
```

### OrchestrAI Kernel

The core of the system. Contains the unique logic that makes OrchestrAI valuable.

**Mission Director**
Accepts a high-level developer goal and produces an ordered task plan. Manages task state (pending, running, complete, failed, retrying). Re-plans when tasks fail. Knows when a goal is complete.

**Task Router**
Given a task and the registered capability metadata of available tools, selects the best tool for the job. Uses a scoring function that combines capability match, current tool availability, historical success rate, and cost estimate.

**Context Manager**
Maintains the active project context. Tracks:
- The current goal and task plan.
- Recent decisions and their rationale.
- Key files and their summaries.
- Architecture constraints and conventions.
- Open questions and blockers.

The context manager is responsible for selecting what context to inject into each tool call, staying within token limits while maximizing relevance.

**Memory Manager**
Persists information that survives across sessions. Separate from the context manager (which is session-scoped). Stores:
- Completed task history with outcomes.
- Architecture decisions and their rationale (ADR format).
- Code summaries for key modules.
- Lessons learned and failure postmortems.
- Team preferences and conventions.

### User Interface Layer

Thin wrappers that translate user input into kernel calls and kernel output into user-readable form.

**CLI** — built on Typer. The primary interface. All kernel capabilities are accessible from the command line.

**Web UI** — optional. Provides a browser-based interface for developers who prefer visual interaction. Built on FastAPI + a minimal frontend. Not required for core functionality.

**Programmatic API** — the kernel exposes a stable Python API. Third-party tools and scripts can drive OrchestrAI programmatically.

---

## Data Flows

### Goal Execution Flow

```
Developer Input
      │
      ▼
  CLI / API
      │
      ▼
Mission Director
  │  Decompose goal into tasks
  │  Persist task plan to memory
      │
      ▼ (for each task)
  Task Router
  │  Score available tools against task
  │  Select best match
      │
      ▼
  Context Manager
  │  Assemble relevant context slice
  │  Respect token budget for selected tool
      │
      ▼
  Adapter Interface
      │
      ▼
  Integration (e.g., Claude Code)
  │  Execute task with injected context
  │  Return structured TaskResult
      │
      ▼
  Context Manager
  │  Update session context with result
      │
      ▼
  Memory Manager
  │  Persist result and any new decisions
      │
      ▼
  Mission Director
  │  Update task plan state
  │  Determine next task or goal completion
      │
      ▼
  CLI / API
      │
      ▼
Developer Output
```

### Memory Read Flow

When a new session starts or a new tool call is made, the Context Manager:

1. Reads the session goal and active task from the Mission Director.
2. Queries Memory Manager for relevant history (semantic search over past tasks and decisions).
3. Queries Memory Manager for key file summaries.
4. Assembles a ranked context slice that fits within the target tool's token budget.
5. Passes the assembled context to the Task Router for injection.

---

## Key Design Decisions

### Decision 1: Strict Layer Separation

Each layer only calls downward. The integration layer never calls the kernel. The kernel never calls the UI. This is enforced through import rules checked by the CI pipeline.

**Why**: Prevents circular dependencies. Allows any layer to be replaced without breaking layers above or below.

### Decision 2: Adapter Interfaces Are Stable Contracts

Once an adapter interface is published, it follows semantic versioning and breaking changes require a major version bump. Integrations that implement an adapter will not break on minor kernel upgrades.

**Why**: External contributors need confidence that their integrations will continue working. Without this guarantee, the integration ecosystem will not grow.

### Decision 3: Memory and Context Are Separate

Session context (what's happening right now) is separate from project memory (what has happened over time). The context manager is stateful per session and discarded when the session ends. The memory manager is persistent.

**Why**: Session context must be fast and in-memory for low latency. Project memory must be durable and queryable. Different access patterns require different implementations.

### Decision 4: Event Bus for Cross-Component Communication

Components emit events (TaskStarted, TaskCompleted, TaskFailed, ContextUpdated) on the event bus rather than calling each other directly. Components subscribe to events they care about.

**Why**: Reduces coupling between kernel components. Enables future features like real-time UI updates, audit logging, and monitoring without modifying core components.

### Decision 5: Plugin System for Third-Party Extensions

OrchestrAI provides a plugin discovery mechanism (entry points via `importlib.metadata`) so third-party packages can register new integrations, adapters, and even kernel extensions without modifying the OrchestrAI codebase.

**Why**: An open-source project grows through community contributions. Making extension easy without requiring forks is essential for ecosystem growth.

---

## File and Module Structure

```
orchestrai/
├── kernel/
│   ├── __init__.py
│   ├── director.py          # Mission Director
│   ├── router.py            # Task Router
│   ├── context.py           # Context Manager
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── manager.py       # Memory Manager interface
│   │   ├── models.py        # Memory data models
│   │   └── backends/        # Storage backend implementations
│   │       ├── json.py
│   │       └── sqlite.py
│   └── events.py            # Event Bus
│
├── adapters/
│   ├── __init__.py
│   ├── task.py              # TaskAdapter interface
│   ├── context.py           # ContextAdapter interface
│   ├── capability.py        # CapabilityAdapter interface
│   └── lifecycle.py         # LifecycleAdapter interface
│
├── integrations/
│   ├── __init__.py
│   ├── copilot/             # GitHub Copilot integration
│   ├── openhands/           # OpenHands integration
│   ├── claude_code/         # Claude Code integration
│   └── shell/               # Generic shell command integration
│
├── ui/
│   ├── cli/
│   │   ├── __init__.py
│   │   └── main.py          # Typer CLI entry point
│   └── web/
│       ├── __init__.py
│       └── app.py           # FastAPI web interface (optional)
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── examples/
│   ├── basic_goal/
│   └── multi_tool_workflow/
│
└── docs/
    ├── index.md
    ├── quickstart.md
    ├── kernel/
    ├── adapters/
    ├── integrations/
    └── contributing/
```

---

## Architectural Constraints

These constraints are non-negotiable. Proposals that violate them require an architecture review.

1. **No circular imports** — enforced by CI.
2. **Kernel has no direct knowledge of any specific integration** — the kernel sees only adapter interfaces.
3. **All disk I/O goes through the storage abstraction** — no raw `open()` calls outside the storage layer.
4. **All configuration goes through the config module** — no hardcoded values.
5. **All external HTTP calls are behind an interface** — to allow mocking in tests and replacement in production.
6. **Every public API is typed** — `mypy --strict` must pass for all kernel code.

---

## Extensibility Points

The following are designed extension points where community contributions are explicitly welcome:

| Extension Point | What you can add |
|---|---|
| `integrations/` | New AI tool integrations |
| `kernel/memory/backends/` | New storage backends (Redis, PostgreSQL, etc.) |
| `kernel/router.py` | Custom routing strategies |
| Plugin entry points | Integrations distributed as separate packages |
| `adapters/` | New adapter interfaces for new interaction patterns |
