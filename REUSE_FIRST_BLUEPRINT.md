# Reuse-First Blueprint

> **Core Principle**: Build only what makes OrchestrAI unique. For everything else, use the best available open-source library.
>
> **MVP scope**: This document is organized into **MVP dependencies** (required for Milestone 1) and **deferred dependencies** (needed in V2+ but not now). The MVP dependency list is intentionally short.

---

## Decision Framework

Before building any piece of OrchestrAI, the team asks these questions in order:

1. **Does a mature open-source library solve this problem?** If yes, use it.
2. **Do two or three libraries solve it?** Evaluate them against our stack (see [STACK_DECISIONS.md](STACK_DECISIONS.md)).
3. **Does the library fit behind a thin abstraction?** If yes, wrap it and proceed.
4. **Is the coupling acceptable if no abstraction is used?** If yes, use it directly.
5. **Is no library adequate?** Only then do we build it ourselves.

---

## MVP Dependencies (Milestone 1)

These are the only dependencies needed to ship `orchestrai run "<goal>"`.

### Task Planning and Decomposition

| Concern | Reused Component | Decision |
|---|---|---|
| Task graph modeling | Python `dataclasses` + `typing` | stdlib first; upgrade to Pydantic if validation complexity warrants it |
| Task prioritization | Built-in `list` (ordered) | An ordered list is sufficient for MVP; `heapq` added only if priority queues are needed |
| Dependency resolution | `graphlib` (stdlib, Python 3.9+) | stdlib covers DAG resolution; NetworkX only if cycle detection or layout visualization is needed |

**What we do NOT reuse here**: The Mission Director logic. The rules for decomposing a natural-language goal into a task list are OrchestrAI's core differentiator.

---

### Language Model Interaction

| Concern | Reused Component | Decision |
|---|---|---|
| LLM abstraction layer | `litellm` | Provider-agnostic, lightweight, no framework lock-in |
| Prompt templating | `jinja2` | Mature, testable, separates prompts from code |

**Why not LangChain?** LangChain provides more than we need, creates lock-in, and has a history of breaking changes. LiteLLM covers provider normalization without the overhead.

---

### Storage (MVP: JSON)

| Concern | Reused Component | Decision |
|---|---|---|
| Run history persistence | `json` (stdlib) | Flat JSON file; zero infrastructure required for MVP |
| In-process object model | Python `dataclasses` | stdlib for simplicity |

---

### CLI

| Concern | Reused Component | Decision |
|---|---|---|
| CLI framework | `Typer` | Built on Click, adds type inference, produces help text automatically |
| Terminal output | `Rich` | Tables, progress bars, and syntax highlighting in one library |

---

### Configuration

| Concern | Reused Component | Decision |
|---|---|---|
| Config file format | YAML via `PyYAML` | Human-friendly, widely understood |
| Environment variable override | `python-dotenv` | Handles `.env` files cleanly for local development |
| Config validation | `pydantic-settings` | Validation and env-var override in one step |

---

### Logging

| Concern | Reused Component | Decision |
|---|---|---|
| Structured logging | `structlog` | Adds structured context and JSON output without replacing stdlib `logging` |

---

### Testing

| Concern | Reused Component | Decision |
|---|---|---|
| Test runner | `pytest` | Community standard |
| Mocking | `unittest.mock` (stdlib) | stdlib is sufficient; `pytest-mock` added only if fixture integration is needed |
| Async test support | `pytest-asyncio` | Standard complement to async Python code |
| Coverage | `coverage` + `pytest-cov` | Standard combination |
| Static analysis | `ruff` | Replaces Flake8, isort, and many Pylint rules |
| Type checking | `mypy` | Reference implementation |
| Formatting | `black` | De facto Python formatter |

---

## Deferred Dependencies (V2+)

The following components are needed for later milestones but are explicitly excluded from the MVP. Adding them before they are needed increases complexity and dependency surface without delivering value.

| Component | Deferred Until | Reason |
|---|---|---|
| `httpx` | Milestone 3 | No outbound HTTP calls in the MVP. The Shell integration uses subprocess. httpx becomes necessary when HTTP-based integrations (Claude Code, OpenHands) are added. |
| `SQLAlchemy` Core | Milestone 2 | Relational storage is needed when cross-session queries, team-shared memory, and schema migrations are required. JSON is sufficient for MVP run history. |
| `Alembic` | Milestone 2 | Schema migrations are only needed when SQLAlchemy is introduced. |
| `chromadb` | Beyond 1.0 | Semantic search over task history requires an embedding model and vector store. Not needed until the Memory Manager gains semantic search capability. |
| `tiktoken` | Milestone 2 | Token counting is only needed when the Context Manager must stay within a tool's context window budget. Not needed in the MVP (the goal string is the only context). |
| `langchain_text_splitters` | Milestone 2 | Text splitting for context chunking is part of the Context Manager, which is a Milestone 2 deliverable. |
| `FastAPI` + `uvicorn` | Milestone 5 | The web interface is a convenience layer over the CLI. Not needed until team features and task timeline visualization are required. |
| `opentelemetry-sdk` | Milestone 5 | Tracing and metrics are valuable when running OrchestrAI as a persistent service. A local CLI tool does not need distributed observability. |
| `importlib.metadata` entry points (plugin system) | Milestone 6 | Plugin discovery requires a stable adapter interface API and a mature community — both are Milestone 6+ concerns. |
| `openai` / `anthropic` SDKs (direct) | Milestone 3 | LiteLLM abstracts these for MVP. Direct SDK usage is only needed if LiteLLM's abstraction proves insufficient for a specific integration. |

---

## Replacement Conditions

Each reused component has defined conditions under which we would replace it:

| Component | Replace if... |
|---|---|
| `litellm` | It introduces breaking changes frequently or adds significant overhead to the dependency tree |
| `SQLAlchemy` (Milestone 2+) | The project moves to an async-only stack where SQLAlchemy's async support proves insufficient |
| `FastAPI` (Milestone 5+) | A lighter alternative matures that provides equivalent OpenAPI generation with fewer dependencies |
| `PyYAML` | Security vulnerabilities are discovered that cannot be patched promptly |
| `chromadb` (Beyond 1.0) | Query latency becomes unacceptable at project scale or licensing changes |

---

## Explicitly Avoided Dependencies

The following well-known libraries are **not used** in OrchestrAI, by deliberate decision:

| Library | Why Avoided |
|---|---|
| **LangChain** | Over-abstracts, frequent breaking changes, creates lock-in, covers far more scope than we need |
| **LlamaIndex** | Same concerns as LangChain |
| **Celery** | Heavyweight distributed task queue; OrchestrAI is local-first and single-process for MVP |
| **Redis** | Runtime dependency; can be added as an optional backend in V2+ |
| **Docker** (as a hard dependency) | Optional for containerized deployments; not required for local development |
| **Kubernetes** | Premature complexity for the current stage |

---

## Dependency Health Criteria

Before adding any new dependency, it must satisfy at least four of these five criteria:

1. **Active maintenance** — committed in the last 6 months with responsive maintainers.
2. **Liberal license** — MIT, Apache 2.0, BSD, or equivalent. GPL-licensed dependencies require explicit approval.
3. **Reasonable size** — pulling in a 50-package transitive dependency tree to solve a 20-line problem is not acceptable.
4. **Test coverage** — the library itself has meaningful tests.
5. **Stable API** — follows semantic versioning with a history of not breaking consumers.

Proposals to add new dependencies must include a completed dependency health checklist in the PR.
