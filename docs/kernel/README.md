# Kernel Documentation

The kernel is the core of OrchestrAI. It contains the logic that makes OrchestrAI valuable: planning, routing, context management, and memory.

## Components

### Mission Director (`kernel/director.py`)

Accepts a high-level developer goal and produces an ordered task plan. Manages task lifecycle (pending → running → complete / failed / retrying). Re-plans when tasks fail.

**Key concepts**:
- A *goal* is a natural-language developer intent ("Migrate the auth module to use JWT").
- A *task* is a concrete, actionable unit of work with a type, description, and priority.
- A *task plan* is an ordered DAG of tasks that, when executed, achieves the goal.

### Task Router (`kernel/router.py`)

Given a task and the registered capability metadata of available tools, selects the best tool. Uses a scoring function that combines:
- Capability match score
- Tool availability
- Historical success rate for this task type
- Estimated cost

### Context Manager (`kernel/context.py`)

Maintains session-scoped project context. Assembles a token-budget-aware context slice for each tool call. Tracks the active goal, current task, recent decisions, and key files.

### Memory Manager (`kernel/memory/`)

Persists information across sessions. Stores completed task history, architecture decision records, code summaries, and lessons learned. Supports semantic search via an optional vector backend.

### Event Bus (`kernel/events.py`)

In-process publish/subscribe system for decoupled communication between kernel components.

## Design Constraints

See [ARCHITECTURE.md](../../ARCHITECTURE.md#architectural-constraints) for the full list. Key constraints:

- The kernel never imports from `integrations/` directly.
- The kernel depends only on adapter interfaces from `adapters/`.
- All disk I/O goes through `kernel/memory/backends/`.

## Status

The kernel is planned for **Milestone 1** (infrastructure) and **Milestone 2** (MVP). No production-ready implementation exists yet.
