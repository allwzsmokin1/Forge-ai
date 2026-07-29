# Forge-ai

Forge-AI is a modular multi-agent assistant platform designed for extensible software engineering workflows.

## Phase 3 Architecture

Forge-AI now includes an autonomous orchestration layer with dependency-aware planning, parallel scheduling, shared memory, and specialized workflow agents.

```text
forge/
├── agents/
│   ├── base.py
│   ├── planner.py
│   ├── coder.py
│   ├── reviewer.py
│   ├── researcher.py
│   ├── tester.py
│   ├── debugger.py
│   ├── documentation.py
│   └── git.py
├── memory/
│   ├── memory.py
│   ├── models.py
│   └── storage.py
├── orchestrator.py
├── scheduler.py
└── tasks.py
```

### Specialized agents

- `PlannerAgent`: decomposes goals into dependency-aware tasks and retry policies.
- `CoderAgent`: handles implementation-oriented tasks.
- `ReviewerAgent`: performs heuristic quality and security review.
- `ResearchAgent`: captures research findings and recommendations.
- `TestAgent`: defines validation commands and focus areas.
- `DebugAgent`: diagnoses failed tasks and supports retries.
- `DocumentationAgent`: identifies docs updates and sections to cover.
- `GitAgent`: prepares branch, commit, and handoff guidance.

### Orchestration flow

1. The orchestrator receives a goal and asks the planner for a task DAG.
2. The scheduler validates the graph, tracks task states, and runs independent tasks concurrently.
3. Each runnable task is dispatched to the best matching registered agent.
4. Failed tasks are retried according to task-level retry policies.
5. Debug guidance is recorded whenever a task failure occurs.
6. The final execution report includes task results, graph metadata, and peak parallelism.

### Project memory

The shared memory service persists:

- task history and lifecycle state transitions
- file metadata and recommended updates
- agent decisions and retry guidance
- execution summaries and goal context

JSON storage remains the default backend, and the APIs are structured so additional persistent backends can be introduced later.

## Configuration

`forge/config.py` now exposes scheduler and memory settings, including default retry counts, maximum parallelism, and the memory file path.

## Validation

- `python -m pytest -q`
- `ruff check .`
- `black --check .`

GitHub Actions validation is defined in `.github/workflows/validation.yml`.
