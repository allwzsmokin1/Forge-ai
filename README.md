# Forge-ai

Forge-AI is a modular multi-agent assistant platform designed for extensible software engineering workflows.

## Phase 3 Highlights

Forge-AI now includes an autonomous orchestration layer that can break complex goals into dependency-aware tasks, schedule independent work in parallel, retry transient failures, and persist execution context across runs.

## Architecture

Forge-AI uses a clean agent-based architecture with a shared abstract base class and specialized agents for planning, coding, reviewing, testing, debugging, documentation, git workflow coordination, and researching.

```text
forge/
└── agents/
    ├── __init__.py
    ├── base.py
    ├── planner.py
    ├── coder.py
    ├── reviewer.py
    ├── tester.py
    ├── debugger.py
    ├── documentation.py
    ├── git.py
    └── researcher.py
forge/
├── orchestrator.py
└── scheduler.py
```

- `BaseAgent`: abstract contract for all agents.
- `PlannerAgent`: decomposes user goals into typed tasks with priorities and inferred dependencies.
- `CoderAgent`: generates Python code, performs refactors, and explains code.
- `ReviewerAgent`: reviews code, highlights issues, and returns severity levels.
- `TestAgent`: summarizes validation readiness and recommended checks.
- `DebugAgent`: analyzes failures and proposes next remediation steps.
- `DocumentationAgent`: prepares documentation summaries and update outlines.
- `GitAgent`: summarizes repository follow-up actions and commit readiness.
- `ResearchAgent`: gathers documentation, summarizes findings, and recommends best practices.
- `OrchestratorAgent`: builds a task DAG, routes work to specialized agents, and manages retries and state transitions.
- `TaskScheduler`: executes independent tasks concurrently while respecting dependencies.

## Design Goals

- Strong typing with Python 3.12+ support.
- Dataclasses for structured results.
- Google style docstrings and extensive inline comments.
- Clean architecture for easy future extension.

## Execution Flow

The orchestrator coordinates the full workflow:

1. The user submits a goal.
2. The planner decomposes the goal into typed tasks with dependency metadata.
3. A directed acyclic graph is validated before execution begins.
4. Independent tasks run concurrently while blocked tasks wait for dependencies.
5. Failed tasks are retried with configurable policies before being marked failed.
6. The orchestrator collects every task result and task state into a structured execution report.
7. Memory is loaded on startup, updated after every task transition, and saved before the run completes.

This flow is designed to be extensible: new agents can be registered with keywords without altering the orchestrator logic.

## Memory Architecture

Forge-AI maintains a persistent project memory layer that records task execution, failures, file metadata, agent decisions, code summaries, goals, architecture decisions, and dependency mappings.

```text
forge/
└── memory/
    ├── __init__.py
    ├── memory.py
    ├── models.py
    └── storage.py
```

- `MemoryEntry`: captures task metadata, result, error, timestamp, and responsible agent.
- `TaskRecord`: tracks task state history, attempts, dependencies, and result summaries.
- `FileMetadata`: stores important file context for retrieval across runs.
- `AgentDecision`: records routing and orchestration decisions.
- `ConversationMemory`: stores conversation-specific goals, decisions, files, and entries.
- `ProjectMemory`: aggregates completed/failed tasks, code summaries, dependency maps, and conversation state.
- `MemoryManager`: provides task history recording, context retrieval, summary storage, save, and load operations.
- `JSONStorage`: initial pluggable storage backend with JSON persistence.

The memory layer is designed so a SQL backend can replace JSON storage without changing the orchestrator or agent APIs.

## Validation

- `python -m pytest -q`
- `python -m ruff check .`
- `python -m black --check .`

GitHub Actions runs the same validation workflow on pushes and pull requests.
