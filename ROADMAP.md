# OrchestrAI Roadmap

> Every milestone produces a working, usable system. No milestone ends with infrastructure only.

---

## Guiding Principles for the Roadmap

- **Ship working software at every milestone** — not just code, but an experience a developer can actually use.
- **Milestones are sized to be achievable** — each one should be completable by a small team in roughly 4–6 weeks.
- **Features are added depth-first** — make each piece really work before adding the next piece.
- **The MVP validates the core value proposition** — does OrchestrAI actually save developer time? Milestone 2 answers that question.

---

## Milestone 0: Repository Foundation *(Current)*

**Goal**: A professional repository that communicates the project's vision, architecture, and contribution process clearly enough that a capable developer can understand where to start.

**Deliverables**:
- [x] README.md with project overview, rationale, and quick start
- [x] MISSION.md with purpose, non-goals, and vision
- [x] ARCHITECTURE.md with layered design and data flows
- [x] REUSE_FIRST_BLUEPRINT.md with dependency inventory
- [x] STACK_DECISIONS.md with technology decisions and rationale
- [x] ROADMAP.md (this document)
- [x] CONTRIBUTING.md with contribution workflow
- [x] LICENSE (Apache 2.0)
- [x] Folder structure: `kernel/`, `integrations/`, `adapters/`, `ui/`, `tests/`, `examples/`, `docs/`
- [x] Placeholder README files in each directory explaining its purpose

**What you can do after this milestone**: Read about OrchestrAI and understand what it is, why it exists, and where to contribute.

---

## Milestone 1: Infrastructure Layer

**Goal**: The plumbing that everything else depends on. No features yet, but a solid foundation.

**Deliverables**:
- [ ] Storage abstraction with JSON backend (portable key-value store)
- [ ] SQLite backend for structured memory storage
- [ ] Configuration system (`pydantic-settings` + YAML)
- [ ] Structured logging (`structlog` integration)
- [ ] In-process event bus (publish/subscribe)
- [ ] Plugin discovery system (`importlib.metadata` entry points)
- [ ] Project setup: CI pipeline, test matrix, coverage reporting
- [ ] Developer documentation: how to run tests, how to contribute a backend

**What you can do after this milestone**: Run `orchestrai init` and get a working project configuration file. Run the test suite and see 80%+ coverage on the infrastructure layer.

---

## Milestone 2: MVP — Single-Tool Workflow

**Goal**: A developer can give OrchestrAI a goal and have it plan the work and execute it with a single integrated tool.

**Deliverables**:
- [ ] `TaskAdapter` and `CapabilityAdapter` interfaces
- [ ] Mission Director (v1): accepts a goal, produces an ordered task list
- [ ] Task Router (v1): simple capability matching, no scoring
- [ ] Context Manager (v1): assembles context from project files + config
- [ ] Memory Manager (v1): persists task history to SQLite
- [ ] Shell integration: wraps any CLI command as a TaskAdapter
- [ ] CLI: `orchestrai run "<goal>"` with Rich progress output
- [ ] CLI: `orchestrai history` shows past task runs
- [ ] Examples: two working end-to-end examples in `examples/`

**What you can do after this milestone**: Run `orchestrai run "Audit this codebase for TODO comments and generate a report"` and get a real result. Not magic, but genuinely useful.

---

## Milestone 3: Memory and Context Depth

**Goal**: OrchestrAI remembers across sessions and uses that memory to make better decisions.

**Deliverables**:
- [ ] Memory Manager (v2): semantic search over task history using ChromaDB
- [ ] Memory Manager (v2): architecture decision records (ADR) storage and retrieval
- [ ] Context Manager (v2): token-budget-aware context assembly
- [ ] Context Manager (v2): injects relevant past decisions into every tool call
- [ ] `orchestrai remember "<fact>"` — manually add a fact to project memory
- [ ] `orchestrai context` — show the current assembled context
- [ ] Memory export/import for sharing context with teammates

**What you can do after this milestone**: Start a new session on a project you worked on last week and have OrchestrAI correctly recall the decisions you made, without re-explaining them.

---

## Milestone 4: Multi-Tool Routing

**Goal**: OrchestrAI intelligently routes tasks to the best available tool from a set of registered integrations.

**Deliverables**:
- [ ] `LifecycleAdapter` interface (start, stop, health check)
- [ ] Claude Code integration (via subprocess/API)
- [ ] OpenHands integration (via its REST API)
- [ ] Task Router (v2): scoring function based on capability match + historical success
- [ ] Fallback strategy: retry with a different tool if the primary fails
- [ ] `orchestrai tools` — list registered tools and their status
- [ ] `orchestrai tools add <integration>` — register a new tool
- [ ] Documentation: how to write a custom integration

**What you can do after this milestone**: Have two or more AI tools registered, run a complex goal, and watch OrchestrAI split the work between them based on each tool's strengths.

---

## Milestone 5: Team Features

**Goal**: OrchestrAI works as a shared resource for a development team, not just individual developers.

**Deliverables**:
- [ ] Shared memory backend (PostgreSQL option)
- [ ] Multi-user context separation (per-user and shared namespaces)
- [ ] Audit log: every action, every tool call, every decision is recorded
- [ ] `orchestrai audit` — browse the audit log
- [ ] Role-based access: read-only observers vs. active operators
- [ ] Memory sync: push/pull project memory to a shared store
- [ ] Integration with GitHub (Issues, PRs as task sources)

**What you can do after this milestone**: A team of developers shares a project memory, assigns tasks to OrchestrAI, and can audit every action it took.

---

## Milestone 6: Web Interface and Observability

**Goal**: A browser-based interface for developers who prefer visual interaction, and observability tooling for teams running OrchestrAI in production.

**Deliverables**:
- [ ] FastAPI web interface with WebSocket for live updates
- [ ] Task timeline visualization
- [ ] Memory browser: explore project memory through a web UI
- [ ] OpenTelemetry integration: traces, metrics, logs
- [ ] Docker Compose setup for self-hosted deployment
- [ ] Health check endpoint and readiness probe
- [ ] Prometheus metrics endpoint

**What you can do after this milestone**: Run OrchestrAI as a persistent service, monitor it through standard observability tooling, and use the web interface for task planning.

---

## Milestone 7: Ecosystem and Extensibility

**Goal**: The plugin ecosystem is mature enough for community integrations to exist independently.

**Deliverables**:
- [ ] Stable adapter interface versioning (semver enforcement in CI)
- [ ] Plugin registry: a curated list of community integrations
- [ ] Integration SDK: a template and test harness for building integrations
- [ ] Documentation site (MkDocs or Docusaurus)
- [ ] Integration certification: CI pipeline that validates community integrations against the adapter interface
- [ ] GitHub Copilot integration
- [ ] VS Code extension (basic: run commands, view history)
- [ ] `orchestrai 1.0.0` release

**What you can do after this milestone**: Install a third-party OrchestrAI integration from PyPI, register it in your project, and have it work identically to built-in integrations.

---

## Beyond 1.0

The following are under consideration for post-1.0 development. None are committed.

- **Multi-agent parallelism**: run independent tasks across tools concurrently.
- **Automated testing integration**: OrchestrAI writes code, runs tests, and iterates automatically.
- **Cost tracking**: estimate and report the cost of every LLM call across all tools.
- **Self-improvement**: OrchestrAI analyzes its own task history and suggests changes to its routing rules.
- **IDE plugins**: JetBrains, Neovim integrations.
- **Mobile companion app**: monitor running tasks from a phone.

---

## What Is Not on the Roadmap

The following are explicitly not planned for any milestone:

- Building a coding assistant (we integrate them, not build them).
- Building a code execution sandbox (use OpenHands or E2B).
- Cloud-hosted OrchestrAI service (self-hosted first; cloud is a community decision for later).
- Support for Python versions below 3.12.

---

## How the Roadmap Changes

The roadmap is reviewed at the completion of each milestone. Changes require:

1. A GitHub Discussion proposing the change with rationale.
2. At least one week of community comment period.
3. A maintainer decision posted to the discussion.

Feature requests belong in GitHub Issues, not PRs against this file.
