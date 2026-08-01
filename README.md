# OrchestrAI

> **An AI Operating Environment** — coordinates your AI coding tools so you don't have to.

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Status-Pre--Alpha-orange)](ROADMAP.md)
[![Contributing](https://img.shields.io/badge/Contributions-Welcome-brightgreen)](CONTRIBUTING.md)

---

## What Is OrchestrAI?

OrchestrAI is **not** another coding assistant.

It is an **AI Operating Environment** — a coordination layer that sits above tools like GitHub Copilot, OpenHands, Claude Code, Codex, and any other AI agent. It plans the work, preserves long-term project memory, manages context windows, and routes each task to the best available tool automatically.

Think of it as a **Mission Director** for your AI toolkit.

```
┌─────────────────────────────────────────────────────┐
│                   Your Interface                     │
│              (CLI / Web UI / API)                    │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│              OrchestrAI Kernel                       │
│   Mission Director · Context Manager · Memory        │
└──────┬──────────┬──────────────┬────────────────────┘
       │          │              │
  ┌────▼───┐ ┌────▼────┐  ┌─────▼──────┐
  │Copilot │ │OpenHands│  │Claude Code │  ...and more
  └────────┘ └─────────┘  └────────────┘
```

## Why OrchestrAI Exists

Modern AI coding tools are powerful but isolated. Each has its own context, memory, and strengths. Developers waste time context-switching, re-explaining project history, and manually routing tasks.

OrchestrAI solves this by providing:

- **Persistent project memory** — decisions, architecture, codebase history, and lessons learned survive across sessions and across tools.
- **Intelligent task routing** — the Mission Director analyzes each task and dispatches it to the tool best suited for it.
- **Unified context management** — all tools share the same project context without hitting token limits.
- **Tool agnosticism** — plug in any AI tool through a standardized adapter interface.

## Core Principles

| Principle | What it means in practice |
|---|---|
| **Reuse first** | Use mature open-source libraries before building anything custom. |
| **Replaceable dependencies** | Every component can be swapped without rewriting the core. |
| **Local-first** | Works fully offline; cloud services are optional enhancements. |
| **MVP first** | Every milestone ships a working, usable system. |
| **Simplicity over complexity** | No unnecessary abstractions; every layer earns its place. |

## Repository Structure

```
orchestrai/
├── kernel/              # Mission Director, context manager, task router
├── integrations/        # Connectors for external AI tools (Copilot, OpenHands, etc.)
├── adapters/            # Standardized adapter interfaces
├── ui/                  # CLI and optional web interface
├── tests/               # All tests
├── examples/            # Working usage examples
└── docs/                # Full project documentation
```

## Documentation

| Document | Purpose |
|---|---|
| [MISSION.md](MISSION.md) | Project purpose, non-goals, and long-term vision |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design, component relationships, data flows |
| [REUSE_FIRST_BLUEPRINT.md](REUSE_FIRST_BLUEPRINT.md) | Inventory of reused OSS components and rationale |
| [STACK_DECISIONS.md](STACK_DECISIONS.md) | Technology choices with alternatives considered |
| [ROADMAP.md](ROADMAP.md) | Milestone plan from MVP to full release |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute, coding standards, review process |

## Quick Start

> ⚠️ OrchestrAI is in pre-alpha. The interfaces described below reflect the planned MVP API and are not yet implemented.

```bash
# Install
pip install orchestrai

# Initialize a project
orchestrai init

# Run the Mission Director
orchestrai run "Refactor the authentication module to use JWT"
```

## Current Status

OrchestrAI is in **pre-alpha**. The current phase is repository foundation and architecture design. No production-ready components exist yet.

See [ROADMAP.md](ROADMAP.md) for the full milestone plan.

## Contributing

OrchestrAI is designed from the ground up to be community-driven. See [CONTRIBUTING.md](CONTRIBUTING.md) for how to get involved.

## License

Apache 2.0 — see [LICENSE](LICENSE) for details.

Apache 2.0 was chosen over MIT because it includes an explicit patent grant, which is important for a project that coordinates proprietary AI tools. See [CONTRIBUTING.md](CONTRIBUTING.md) for the full rationale.
