# Kernel

The `kernel/` directory contains the core OrchestrAI components: the Mission Director, Task Router, Context Manager, Memory Manager, and Event Bus.

## Planned Structure

```
kernel/
├── __init__.py
├── director.py          # Mission Director: goal → task plan
├── router.py            # Task Router: task → best tool
├── context.py           # Context Manager: session-scoped project context
├── events.py            # Event Bus: in-process pub/sub
├── config.py            # Configuration loading and validation
└── memory/
    ├── __init__.py
    ├── manager.py        # Memory Manager interface
    ├── models.py         # Data models for memory entries
    └── backends/
        ├── __init__.py
        ├── base.py       # StorageBackend abstract base
        ├── json.py       # JSON file backend (MVP)
        └── sqlite.py     # SQLite backend (Milestone 1)
```

## Design Constraints

The kernel has hard boundaries:

- **No imports from `integrations/`** — the kernel knows nothing about specific AI tools.
- **No raw disk I/O** — all persistence goes through `kernel/memory/backends/`.
- **No hardcoded configuration** — all values come from `kernel/config.py`.
- **Fully typed** — all public APIs pass `mypy --strict`.

## Status

Implementation is planned for **Milestone 1** (infrastructure) and **Milestone 2** (MVP).

See [ARCHITECTURE.md](../ARCHITECTURE.md) for the full design.
See [docs/kernel/README.md](../docs/kernel/README.md) for component documentation.
