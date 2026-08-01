# Reuse-First Blueprint

> **Core Principle**: Build only what makes OrchestrAI unique. For everything else, use the best available open-source library.

This document catalogs every open-source component that OrchestrAI reuses, the rationale for choosing it, the alternatives that were evaluated, and the conditions under which we would replace it.

---

## Decision Framework

Before building any piece of OrchestrAI, the team asks these questions in order:

1. **Does a mature open-source library solve this problem?** If yes, use it.
2. **Do two or three libraries solve it?** Evaluate them against our stack (see [STACK_DECISIONS.md](STACK_DECISIONS.md)).
3. **Does the library fit behind a thin abstraction?** If yes, wrap it and proceed.
4. **Is the coupling acceptable if no abstraction is used?** If yes, use it directly.
5. **Is no library adequate?** Only then do we build it ourselves.

---

## Component Inventory

### Task Planning and Decomposition

| Concern | Reused Component | Alternative Considered | Decision |
|---|---|---|---|
| Task graph modeling | Python `dataclasses` + `typing` | Pydantic | stdlib first; Pydantic added only if validation complexity warrants it |
| Task prioritization | Built-in `heapq` | Third-party priority queue | stdlib is sufficient for MVP |
| Dependency resolution | `graphlib` (stdlib, Python 3.9+) | NetworkX | stdlib covers DAG resolution; NetworkX only if cycle detection or layout visualization is needed |

**What we do NOT reuse here**: The Mission Director logic itself. The rules for decomposing a natural-language goal into a task DAG are OrchestrAI's core differentiator and must be built.

---

### Language Model Interaction

| Concern | Reused Component | Alternative Considered | Decision |
|---|---|---|---|
| OpenAI-compatible API calls | `openai` Python SDK | Raw `httpx` | Official SDK reduces maintenance burden |
| Anthropic API calls | `anthropic` Python SDK | Raw `httpx` | Official SDK |
| Local model inference | `ollama` client | `llama-cpp-python` | Ollama handles model lifecycle; we call its API |
| LLM abstraction layer | `litellm` | LangChain, custom | LiteLLM is lightweight, provider-agnostic, and has no framework lock-in |
| Prompt templating | `jinja2` | f-strings, LangChain | Jinja2 is mature, testable, and separates prompts from code |

**Why not LangChain?** LangChain provides more than we need, locks in abstractions we cannot control, and has a history of breaking changes. LiteLLM covers the provider-normalization use case without the overhead.

---

### Memory and Storage

| Concern | Reused Component | Alternative Considered | Decision |
|---|---|---|---|
| In-process object model | Python `dataclasses` | Pydantic, attrs | stdlib for simplicity; upgrade path to Pydantic if JSON schema export is needed |
| JSON persistence (MVP) | `json` (stdlib) | `orjson` | stdlib for MVP; `orjson` can replace without API changes |
| Relational storage | `SQLAlchemy` (Core, not ORM) | raw `sqlite3`, Peewee | SQLAlchemy Core is portable across backends; ORM avoided to keep models simple |
| Schema migrations | `Alembic` | Manual SQL scripts | Alembic is the standard complement to SQLAlchemy |
| Semantic search over memory | `chromadb` (optional) | Weaviate, Pinecone, FAISS | Chroma is local-first, embeddable, and Apache 2.0 licensed |
| Full-text search | `sqlite-fts5` (built into SQLite) | Elasticsearch | Local-first; FTS5 is sufficient for project-scale memory |

---

### Context Window Management

| Concern | Reused Component | Alternative Considered | Decision |
|---|---|---|---|
| Token counting | `tiktoken` (OpenAI) | Model-specific tokenizers | `tiktoken` covers GPT models; Anthropic and others provide their own; abstracted behind a `count_tokens()` interface |
| Text splitting for chunking | `langchain_text_splitters` (isolated) | Custom regex splitter | The text splitter is the only LangChain component we pull in; it is isolated behind an interface |

---

### Web Interface (Optional)

| Concern | Reused Component | Alternative Considered | Decision |
|---|---|---|---|
| HTTP framework | `FastAPI` | Flask, Starlette | FastAPI provides automatic OpenAPI docs and type validation out of the box |
| ASGI server | `uvicorn` | Hypercorn, Gunicorn | `uvicorn` is the standard FastAPI server |
| WebSocket (live updates) | FastAPI WebSocket support | Socket.IO | Built-in; no additional dependency |

---

### CLI

| Concern | Reused Component | Alternative Considered | Decision |
|---|---|---|---|
| CLI framework | `Typer` | Click, argparse | Typer is built on Click, adds type inference, and produces help text automatically |
| Terminal output | `Rich` | Colorama, termcolor | Rich provides tables, progress bars, and syntax highlighting in one library |

---

### Configuration

| Concern | Reused Component | Alternative Considered | Decision |
|---|---|---|---|
| Config file format | YAML via `PyYAML` | TOML, INI | YAML is human-friendly and widely understood; TOML considered but YAML wins on familiarity |
| Environment variable override | `python-dotenv` | `os.environ` directly | `python-dotenv` handles `.env` files cleanly for local development |
| Config validation | `pydantic-settings` | Manual validation | Pydantic Settings integrates validation and env-var override in one step |

---

### Plugin System

| Concern | Reused Component | Alternative Considered | Decision |
|---|---|---|---|
| Plugin discovery | `importlib.metadata` entry points (stdlib) | Pluggy, stevedore | stdlib is sufficient; no additional dependency needed |

---

### Testing

| Concern | Reused Component | Alternative Considered | Decision |
|---|---|---|---|
| Test runner | `pytest` | unittest | Pytest is the standard for modern Python projects |
| Mocking | `unittest.mock` (stdlib) | `pytest-mock` | stdlib is sufficient; `pytest-mock` added only if fixture integration is needed |
| HTTP mocking | `respx` | `responses`, `httpretty` | `respx` integrates cleanly with `httpx` |
| Async test support | `pytest-asyncio` | `anyio` | Standard complement to async Python code |
| Coverage | `coverage` + `pytest-cov` | — | Standard combination |
| Static analysis | `ruff` | Flake8, Pylint | Ruff replaces Flake8, isort, and many Pylint rules in one fast tool |
| Type checking | `mypy` | Pyright | Mypy is the reference implementation; Pyright as an optional second pass |
| Formatting | `black` | autopep8, YAPF | Black is the de facto Python formatter |

---

### Logging and Observability

| Concern | Reused Component | Alternative Considered | Decision |
|---|---|---|---|
| Structured logging | `structlog` | stdlib `logging` | `structlog` adds structured context and JSON output without replacing `logging` |
| Tracing (optional, future) | `opentelemetry-sdk` | Jaeger client | OpenTelemetry is the vendor-neutral standard |

---

## Replacement Conditions

Each reused component has defined conditions under which we would replace it:

| Component | Replace if... |
|---|---|
| `litellm` | It introduces breaking changes frequently or adds significant overhead to the dependency tree |
| `chromadb` | Query latency becomes unacceptable at project scale or licensing changes |
| `SQLAlchemy` | The project moves to an async-only stack where SQLAlchemy's async support proves insufficient |
| `FastAPI` | A lighter alternative matures that provides equivalent OpenAPI generation with fewer dependencies |
| `PyYAML` | Security vulnerabilities are discovered that cannot be patched promptly |
| `tiktoken` | A model-agnostic token counting library matures enough to replace provider-specific tools |

---

## Explicitly Avoided Dependencies

The following well-known libraries are **not used** in OrchestrAI, by deliberate decision:

| Library | Why Avoided |
|---|---|
| **LangChain** | Over-abstracts, frequent breaking changes, creates lock-in, covers far more scope than we need |
| **LlamaIndex** | Same concerns as LangChain; we build only what we need |
| **Celery** | Heavyweight distributed task queue; OrchestrAI is local-first and does not need distributed workers at MVP stage |
| **Redis** | Runtime dependency that makes local-first development harder; can be added as an optional backend |
| **Docker** (as a hard dependency) | Some users run OrchestrAI in constrained environments; Docker is optional for containerized deployments |
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
