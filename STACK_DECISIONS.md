# Stack Decisions

> This document records every significant technology choice made for OrchestrAI, the alternatives that were evaluated, and the reasoning behind each decision. It is a living document: when a decision is revisited, the new reasoning is added rather than replacing the old entry.

---

## SD-001: Programming Language — Python 3.12+

**Decision**: Python 3.12+ as the primary language.

**Alternatives Evaluated**:
- **TypeScript/Node.js**: Strong ecosystem for AI tooling (especially LLM SDKs), but the Python data science and ML ecosystem is unmatched, and most AI tool SDKs are Python-first.
- **Go**: Excellent concurrency and distribution properties, but lacks the ML/AI library ecosystem. Would add complexity for integrations.
- **Rust**: Performance benefits but steep onboarding curve. The bottleneck in OrchestrAI is LLM API latency, not CPU cycles.

**Reasoning**: The AI tooling ecosystem is Python-native. LLM SDKs, embedding libraries, and vector databases are all Python-first. Python 3.12 specifically provides performance improvements (up to 60% faster than 3.10 in some benchmarks) and cleaner type system improvements.

**Constraints Applied**:
- Minimum Python version is 3.12. No backports to older versions.
- All kernel code passes `mypy --strict`.
- `ruff` enforces style and lint rules.

---

## SD-002: Package Management — pip + pyproject.toml

**Decision**: Standard `pip` with `pyproject.toml` (PEP 517/518/621).

**Alternatives Evaluated**:
- **Poetry**: Good DX, but adds a non-standard lock file format and build system that complicates distribution.
- **PDM**: Modern and standards-compliant, but adds another tool that contributors must learn.
- **uv**: Extremely fast, standards-compliant, and increasingly popular. Actively considered as a future default.
- **Conda**: Appropriate for scientific computing; overkill for a developer tooling project.

**Reasoning**: `pyproject.toml` is the Python standard. Using it with standard `pip` keeps the contributor barrier low — anyone who knows Python knows how to install the project. `uv` is noted as a likely future upgrade for faster installs in CI.

---

## SD-003: HTTP Client — httpx

**Decision**: `httpx` as the primary HTTP client for all outbound calls.

**Alternatives Evaluated**:
- **requests**: Synchronous only; does not support async workflows.
- **aiohttp**: Async, but async-only; inconsistent API between sync and async modes.
- **urllib3**: Too low-level for application code.

**Reasoning**: `httpx` provides a consistent sync/async API, HTTPX/2 support, and is the standard complement to FastAPI (which is also built on Starlette/anyio). All outbound HTTP calls are wrapped behind interface methods so `httpx` can be replaced without changing callers.

---

## SD-004: LLM Provider Abstraction — LiteLLM

**Decision**: `litellm` as the provider-agnostic LLM interface.

**Alternatives Evaluated**:
- **Direct SDK calls** (openai, anthropic): Couples the kernel to specific providers; requires conditional logic for every provider.
- **LangChain LLM wrappers**: LangChain is too heavyweight and introduces lock-in.
- **Custom abstraction**: More work with equivalent outcomes; LiteLLM already exists and is mature.

**Reasoning**: LiteLLM normalizes the API across OpenAI, Anthropic, Cohere, Replicate, Ollama, and others. It supports streaming, function calling, and usage tracking. It is lightweight (does not pull in the full LangChain stack). Wrapping it behind our own `LLMProvider` interface preserves the ability to replace it.

**Constraint**: The kernel calls our `LLMProvider` interface, not LiteLLM directly. LiteLLM is an implementation detail of one `LLMProvider` implementation.

---

## SD-005: Storage Layer — SQLAlchemy Core + SQLite (→ PostgreSQL)

**Decision**: SQLAlchemy Core (not ORM) with SQLite for development; PostgreSQL for production deployments.

**Alternatives Evaluated**:
- **Raw sqlite3**: Works for MVP, but migrations and query building become manual pain points.
- **SQLAlchemy ORM**: Adds complexity for what is essentially key-value and document storage.
- **Peewee**: Simpler than SQLAlchemy, but less portable and less maintained.
- **TinyDB**: Pure Python, no SQL, suitable for tiny projects but not for the query complexity we anticipate.
- **MongoDB**: Document store is appealing for memory storage, but adds a heavyweight server dependency.

**Reasoning**: SQLAlchemy Core provides portable SQL without the ORM overhead. SQLite means zero external infrastructure for local development. The same code runs against PostgreSQL in production deployments by changing the connection string. Alembic handles schema migrations in both environments.

---

## SD-006: Semantic Memory — ChromaDB (Optional)

**Decision**: `chromadb` as the optional vector store for semantic memory search.

**Alternatives Evaluated**:
- **FAISS**: High performance, but no built-in persistence or query API; requires more wrapper code.
- **Weaviate**: Feature-rich, but requires a separate server process.
- **Pinecone**: Cloud-only; violates local-first principle.
- **Qdrant**: Strong alternative; local-first, Rust-based. Actively reconsidered if Chroma's Python-heavy implementation becomes a performance concern.
- **pgvector**: PostgreSQL extension; viable for teams already using PostgreSQL.

**Reasoning**: ChromaDB is embedded (no separate server), open-source (Apache 2.0), and Python-native. It is suitable for local-first development and can be replaced by any of the above for production deployments. Semantic memory is an optional enhancement; the core system works without it.

---

## SD-007: API Framework — FastAPI

**Decision**: FastAPI for the optional web interface and programmatic API.

**Alternatives Evaluated**:
- **Flask**: Synchronous default; less ergonomic for modern async Python.
- **Django REST Framework**: Too heavyweight for a tool that may not need a full web framework.
- **Starlette**: FastAPI is built on Starlette; using Starlette directly provides no advantage.
- **Litestar**: Strong alternative with excellent async support; considered for future re-evaluation.

**Reasoning**: FastAPI provides automatic OpenAPI documentation, type validation through Pydantic, and excellent async support. It is the standard for modern Python APIs. The web interface is optional; the CLI is the primary interface.

---

## SD-008: CLI Framework — Typer + Rich

**Decision**: Typer for CLI structure; Rich for output formatting.

**Alternatives Evaluated**:
- **Click**: Typer is built on Click and adds type inference, reducing boilerplate.
- **argparse**: Too verbose for the command surface we anticipate.
- **docopt**: Deprecated in practice; unmaintained.
- **Colorama**: Rich is a superset of Colorama's capabilities.

**Reasoning**: Typer infers CLI arguments from Python type hints, eliminating repetitive decorator code. Rich provides tables, progress bars, syntax-highlighted output, and Markdown rendering in one library, which is exactly what a tool status interface needs.

---

## SD-009: Testing — pytest Ecosystem

**Decision**: pytest as the test runner with standard plugins.

**Alternatives Evaluated**:
- **unittest**: Requires more boilerplate; pytest is the community standard.
- **nose2**: Effectively deprecated.
- **hypothesis**: Added as a property-testing complement, not a replacement.

**Reasoning**: pytest is the de facto standard for Python testing. Its fixture system, parametrize decorator, and plugin ecosystem (pytest-asyncio, pytest-cov, pytest-mock) cover all of our testing needs. No alternative provides meaningful advantages.

---

## SD-010: Linting and Formatting — Ruff + Black + Mypy

**Decision**: Ruff for linting and import sorting; Black for formatting; Mypy for type checking.

**Alternatives Evaluated**:
- **Flake8 + isort**: Ruff replaces both with a Rust-based implementation that runs 10-100x faster.
- **Pylint**: More opinionated and slower than Ruff; most useful rules are covered by Ruff + Mypy.
- **Pyright**: Considered as a complement or replacement to Mypy; both can run in CI.

**Reasoning**: Ruff + Black + Mypy is the emerging standard for modern Python projects. Ruff's speed makes it practical to run on every commit without slowing down development. Black is non-negotiable (zero configuration) and reduces formatting debates entirely.

---

## SD-011: Configuration Format — YAML

**Decision**: YAML for all configuration files.

**Alternatives Evaluated**:
- **TOML**: Strongly considered. Less ambiguous than YAML, native to `pyproject.toml`. Preferred for simple key-value config.
- **JSON**: No comments; bad for human-edited config files.
- **INI**: Too limited for nested configuration.
- **Python files**: Executable config is a security risk in a tool that processes untrusted input.

**Reasoning**: YAML is the most widely understood config format in the developer tooling space (Docker Compose, GitHub Actions, Kubernetes, Ansible). It handles nested structures naturally. The ambiguity issues (YAML Norway problem, type coercion) are mitigated by loading all config through `pydantic-settings` which validates and types all values.

**Note**: `pyproject.toml` is used for Python package metadata (TOML); YAML is used for runtime configuration. These are different concerns and can coexist.

---

## SD-012: Event System — In-Process Pub/Sub

**Decision**: A lightweight in-process event bus, implemented from scratch over a `threading.local`-backed callback registry.

**Alternatives Evaluated**:
- **PyPubSub**: Adequate but unmaintained.
- **Redis Pub/Sub**: Requires external infrastructure; violates local-first principle.
- **Kafka**: Entirely disproportionate for the use case.
- **asyncio events**: Viable; reconsidered if we move to a fully async kernel.

**Reasoning**: OrchestrAI's event volume at MVP scale (a few dozen events per task execution) does not require a distributed message broker. A simple in-process event bus is sufficient, adds no infrastructure dependency, and can be replaced with a Redis-backed implementation for multi-process deployments later.

---

## SD-013: Plugin Discovery — importlib.metadata Entry Points

**Decision**: Python entry points (`importlib.metadata`) for plugin discovery.

**Alternatives Evaluated**:
- **Pluggy** (used by pytest): More ergonomic for complex plugin interfaces, but adds a dependency.
- **stevedore**: More structured, but adds dependencies and complexity.
- **Custom file-based discovery**: Fragile and non-standard.

**Reasoning**: Entry points are the Python standard for plugin discovery. They are supported by all package managers and require no additional dependencies. For the complexity of OrchestrAI's plugin interface, stdlib entry points are sufficient. Pluggy can be introduced if the plugin interface grows complex enough to warrant it.

---

## Decision Log

| ID | Date | Status | Summary |
|---|---|---|---|
| SD-001 | 2026-08 | Active | Python 3.12+ |
| SD-002 | 2026-08 | Active | pip + pyproject.toml |
| SD-003 | 2026-08 | Active | httpx |
| SD-004 | 2026-08 | Active | LiteLLM |
| SD-005 | 2026-08 | Active | SQLAlchemy Core + SQLite |
| SD-006 | 2026-08 | Active | ChromaDB (optional) |
| SD-007 | 2026-08 | Active | FastAPI |
| SD-008 | 2026-08 | Active | Typer + Rich |
| SD-009 | 2026-08 | Active | pytest |
| SD-010 | 2026-08 | Active | Ruff + Black + Mypy |
| SD-011 | 2026-08 | Active | YAML config |
| SD-012 | 2026-08 | Active | In-process event bus |
| SD-013 | 2026-08 | Active | importlib.metadata entry points |
