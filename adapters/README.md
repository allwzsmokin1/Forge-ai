# Adapters

The `adapters/` directory contains the standardized interface definitions that every integration must implement.

## Purpose

Adapters are the **dependency inversion boundary** between the kernel and external AI tools. The kernel imports from `adapters/` only — never from `integrations/` directly. This is what makes every integration replaceable.

## Planned Structure

```
adapters/
├── __init__.py
├── task.py              # TaskAdapter: execute a task, return a result
├── capability.py        # CapabilityAdapter: declare tool strengths
├── lifecycle.py         # LifecycleAdapter: start, stop, health check
├── context.py           # ContextAdapter: read/write project context
└── models.py            # Shared data models (Task, TaskResult, Context, etc.)
```

## Versioning Policy

Adapter interfaces are versioned separately from the kernel. Once a version is published:

- Changes that add optional methods are **minor** (backwards compatible).
- Changes that modify or remove existing methods are **major** (breaking).

All integrations declare which adapter version they implement.

## Status

Interface definitions are planned for **Milestone 2** (MVP).

See [docs/adapters/README.md](../docs/adapters/README.md) for the full interface reference.
