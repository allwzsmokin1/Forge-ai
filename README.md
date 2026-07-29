# Forge-ai

Forge-AI is a modular multi-agent assistant platform designed for extensible software engineering workflows.

## Architecture

Forge-AI uses a clean agent-based architecture with a shared abstract base class, a unified runtime/tool layer, and specialized agents for planning, coding, reviewing, and researching.

```text
forge/
├── agents/
│   ├── __init__.py
│   ├── base.py
│   ├── planner.py
│   ├── coder.py
│   ├── reviewer.py
│   └── researcher.py
├── runtime/
│   ├── __init__.py
│   ├── manager.py
│   ├── registry.py
│   ├── permissions.py
│   ├── metrics.py
│   └── lifecycle.py
└── tools/
    ├── __init__.py
    ├── filesystem.py
    ├── terminal.py
    ├── git.py
    ├── python.py
    ├── docker.py
    ├── search.py
    ├── web.py
    └── archive.py
```

- `BaseAgent`: abstract contract for all agents.
- `RuntimeManager`: shared tool runtime with permissions, retries, metrics, hooks, and health checks.
- `ToolRegistry`: central registry for built-in and plugin-provided tools.
- `forge.tools`: common execution interface for Terminal, Filesystem, Git, Python, Docker, Search, Web, and Archive tools.
- `PlannerAgent`: decomposes user goals into ordered tasks with priority.
- `CoderAgent`: generates Python code, performs refactors, and explains code.
- `ReviewerAgent`: reviews code, highlights issues, and returns severity levels.
- `ResearchAgent`: gathers documentation, summarizes findings, and recommends best practices.

## Design Goals

- Strong typing with Python 3.12+ support.
- Dataclasses for structured results.
- Google style docstrings and extensive inline comments.
- Clean architecture for easy future extension.

## Execution Flow

The orchestrator coordinates the full workflow:

1. The user submits a goal.
2. The planner decomposes the goal into ordered tasks.
3. Each task is dispatched to the most suitable registered agent.
4. The orchestrator collects every task result into a structured execution report.
5. Memory is loaded on startup, updated after every task, and saved before the run completes.

This flow is designed to be extensible: new agents can be registered with keywords without altering the orchestrator logic.

## Memory Architecture

Forge-AI maintains a persistent project memory layer that records task execution, failures, code summaries, goals, architecture decisions, and important files.

```text
forge/
└── memory/
    ├── __init__.py
    ├── memory.py
    ├── models.py
    └── storage.py
```

- `MemoryEntry`: captures task metadata, result, error, timestamp, and responsible agent.
- `ConversationMemory`: stores conversation-specific goals, decisions, files, and entries.
- `ProjectMemory`: aggregates completed/failed tasks, code summaries, and conversation state.
- `MemoryManager`: provides add, search, recent, summary, save, and load operations.
- `JSONStorage`: initial pluggable storage backend with JSON persistence.

The memory layer is designed so a SQL backend can replace JSON storage without changing the orchestrator or agent APIs.

## Runtime & Tooling

The runtime layer mediates all tool execution behind a shared registry and permission model. Services such as the CLI, plugin discovery, and JSON memory storage now request filesystem capabilities through the runtime instead of calling the operating system directly. Tools publish lifecycle events, collect execution metrics, support retries, and expose health checks for integration diagnostics.

## Testing

Pytest coverage exists for each agent, the orchestrator, and the memory layer, ensuring planning, code generation, review, research, persistence, and failure handling are exercised.
