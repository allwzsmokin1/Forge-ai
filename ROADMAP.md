# OrchestrAI Roadmap

> Every milestone produces a working, usable system. No milestone ends with infrastructure only.

---

## Guiding Principles

- **Ship working software at every milestone** — not just code, but something a developer can actually run.
- **One mission, one worker first** — the MVP proves the core loop before adding routing, memory, or team features.
- **Depth before breadth** — make each piece really work before adding the next.
- **The MVP answers one question**: can OrchestrAI plan a goal and execute it end-to-end? Everything else waits.

---

## Milestone 0: Repository Foundation *(Current)*

**Goal**: A professional repository that communicates the project's vision clearly enough that a capable developer can understand where to start.

**Deliverables**:
- [x] README.md with project overview, rationale, and quick start
- [x] MISSION.md with purpose, non-goals, and vision
- [x] ARCHITECTURE.md with MVP-scoped layered design and data flows
- [x] REUSE_FIRST_BLUEPRINT.md with dependency inventory
- [x] STACK_DECISIONS.md with technology decisions and rationale
- [x] ROADMAP.md (this document)
- [x] CONTRIBUTING.md with contribution workflow
- [x] LICENSE (Apache 2.0)
- [x] Folder structure: `kernel/`, `integrations/`, `adapters/`, `ui/`, `tests/`, `examples/`, `docs/`

**What you can do after this milestone**: Read about OrchestrAI and understand what it is, why it exists, and where to contribute.

---

## Milestone 1: MVP — One Mission, One Worker

**Goal**: A developer can give OrchestrAI a plain-text goal and get a real result. One kernel component. One integration. No database. No routing.

**Deliverables**:
- [ ] `TaskAdapter` interface and `TaskResult` model
- [ ] Mission Director: accepts a goal, calls LiteLLM to decompose it into shell commands, executes them in order
- [ ] Shell integration: wraps any CLI command as a `TaskAdapter`
- [ ] JSON storage: writes run records to a flat JSON file in the project directory
- [ ] Configuration: YAML file + env var overrides via `pydantic-settings`
- [ ] Structured logging: `structlog` with JSON and human-readable modes
- [ ] CLI: `orchestrai run "<goal>"` with Rich progress output
- [ ] CLI: `orchestrai history` shows past run records from the JSON store
- [ ] CI pipeline: tests, lint (`ruff`), type check (`mypy`), format (`black`)
- [ ] One working end-to-end example in `examples/basic_goal/`

**What you can do after this milestone**: Run `orchestrai run "Audit this codebase for TODO comments and generate a report"` and get a real result. Not magic, but genuinely useful.

---

## Milestone 2: Context and Memory

**Goal**: OrchestrAI remembers across sessions and injects relevant context into each tool call.

**Deliverables**:
- [ ] Memory Manager: persists task history and decisions to SQLite via SQLAlchemy Core
- [ ] Alembic schema migrations for the SQLite store
- [ ] Context Manager (v1): assembles project context (goal, recent decisions, key files)
- [ ] Context Manager (v1): token-budget-aware — respects the model's context window
- [ ] `orchestrai remember "<fact>"` — manually add a fact to project memory
- [ ] `orchestrai context` — show the current assembled context
- [ ] Memory export/import for sharing context with teammates

**What you can do after this milestone**: Start a new session on a project you worked on last week and have OrchestrAI correctly recall the decisions you made.

---

## Milestone 3: Multi-Tool Routing

**Goal**: OrchestrAI intelligently routes tasks to the best available tool from a set of registered integrations.

**Deliverables**:
- [ ] `CapabilityAdapter` and `LifecycleAdapter` interfaces
- [ ] Task Router: scoring function based on capability match + historical success
- [ ] Fallback strategy: retry with a different tool if the primary fails
- [ ] Claude Code integration (via subprocess/API)
- [ ] OpenHands integration (via its REST API)
- [ ] `orchestrai tools` — list registered tools and their status
- [ ] Documentation: how to write a custom integration

**What you can do after this milestone**: Have two AI tools registered and watch OrchestrAI split the work between them based on each tool's strengths.

---

## Milestone 4: Team Features

**Goal**: OrchestrAI works as a shared resource for a development team.

**Deliverables**:
- [ ] Shared memory backend (PostgreSQL option)
- [ ] Multi-user context separation (per-user and shared namespaces)
- [ ] Audit log: every action and tool call is recorded
- [ ] Role-based access: read-only observers vs. active operators
- [ ] Memory sync: push/pull project memory to a shared store
- [ ] Integration with GitHub (Issues, PRs as task sources)

**What you can do after this milestone**: A team shares a project memory and can audit every action OrchestrAI took.

---

## Milestone 5: Web Interface and Observability

**Goal**: A browser-based interface for teams running OrchestrAI as a persistent service.

**Deliverables**:
- [ ] FastAPI web interface with WebSocket for live updates
- [ ] Task timeline visualization
- [ ] Memory browser: explore project memory through a web UI
- [ ] OpenTelemetry integration: traces, metrics, logs
- [ ] Docker Compose setup for self-hosted deployment
- [ ] Prometheus metrics endpoint

**What you can do after this milestone**: Run OrchestrAI as a persistent service and monitor it through standard observability tooling.

---

## Milestone 6: Ecosystem and Extensibility

**Goal**: The plugin ecosystem is mature enough for community integrations.

**Deliverables**:
- [ ] Plugin discovery system (`importlib.metadata` entry points)
- [ ] Stable adapter interface versioning (semver enforcement in CI)
- [ ] Integration SDK: a template and test harness for building integrations
- [ ] Documentation site (MkDocs)
- [ ] GitHub Copilot integration
- [ ] VS Code extension (basic: run commands, view history)
- [ ] `orchestrai 1.0.0` release

**What you can do after this milestone**: Install a third-party OrchestrAI integration from PyPI and have it work identically to built-in integrations.

---

## Beyond 1.0

Under consideration for post-1.0 development. None are committed.

- **Semantic memory (ChromaDB)**: vector search over task history for richer context injection.
- **Multi-agent parallelism**: run independent tasks across tools concurrently.
- **Automated testing integration**: OrchestrAI writes code, runs tests, and iterates automatically.
- **Cost tracking**: estimate and report the cost of every LLM call.
- **Self-improvement**: OrchestrAI analyzes its own task history and suggests routing rule changes.
- **IDE plugins**: JetBrains, Neovim integrations.

---

## What Is Not on the Roadmap

- Building a coding assistant (we integrate them, not build them).
- Building a code execution sandbox (use OpenHands or E2B).
- Cloud-hosted OrchestrAI service (self-hosted first).
- Support for Python versions below 3.12.

---

## How the Roadmap Changes

The roadmap is reviewed at the completion of each milestone. Changes require:

1. A GitHub Discussion proposing the change with rationale.
2. At least one week of community comment period.
3. A maintainer decision posted to the discussion.

Feature requests belong in GitHub Issues, not PRs against this file.
