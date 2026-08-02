# Stack Decisions

> This document records every significant technology choice made for OrchestrAI, the alternatives evaluated, and the reasoning behind each decision.
>
> **MVP scope**: Decisions marked **[V2+]** are deferred — they are the right choice for a later milestone but add unnecessary complexity to the MVP.

---

## SD-001: Programming Language — Python 3.12+

**Decision**: Python 3.12+ as the primary language.

**Alternatives Evaluated**:
- **TypeScript/Node.js**: Strong AI tooling ecosystem, but Python is the language of AI-first SDKs.
- **Go**: Excellent concurrency, but lacks the ML/AI library ecosystem.
- **Rust**: Performance benefits, but steep onboarding curve and the bottleneck is LLM API latency, not CPU.

**Reasoning**: The AI tooling ecosystem is Python-native. LLM SDKs, embedding libraries, and vector databases are Python-first. Python 3.12 adds meaningful performance improvements and cleaner type system features.

**Constraints**:
- Minimum Python version is 3.12. No backports.
- All kernel code passes `mypy --strict`.
- `ruff` enforces style and lint rules.

---

## SD-002: Package Management — pip + pyproject.toml

**Decision**: Standard `pip` with `pyproject.toml` (PEP 517/518/621).

**Alternatives Evaluated**:
- **Poetry**: Non-standard lock file format; complicates distribution.
- **PDM**: Modern and standards-compliant, but adds a tool contributors must learn.
- **uv**: Extremely fast and standards-compliant. Noted as a likely future upgrade.
- **Conda**: Appropriate for scientific computing; overkill here.

**Reasoning**: `pyproject.toml` is the Python standard. Using it with standard `pip` keeps the contributor barrier low.

---

## SD-003: LLM Provider Abstraction — LiteLLM

**Decision**: `litellm` as the provider-agnostic LLM interface.

**Alternatives Evaluated**:
- **Direct SDK calls** (openai, anthropic): Couples the kernel to specific providers.
- **LangChain LLM wrappers**: Too heavyweight; lock-in.
- **Custom abstraction**: More work with equivalent outcomes; LiteLLM already exists.

**Reasoning**: LiteLLM normalizes the API across OpenAI, Anthropic, Cohere, Ollama, and others. It supports streaming, function calling, and usage tracking. It is lightweight. The kernel calls our own `LLMProvider` interface; LiteLLM is one implementation of it.

---

## SD-004: Storage — JSON Files (MVP) → SQLAlchemy + SQLite (V2+)

**MVP Decision**: Flat JSON files written to the project directory.

**V2+ Decision**: SQLAlchemy Core (not ORM) with SQLite → PostgreSQL for team deployments.

**Reasoning**: JSON requires no schema, no migrations, no external tooling, and is fully human-readable. It is the right choice when the only query needed is "show me the last N runs". SQLAlchemy + Alembic become necessary in Milestone 2 when semantic memory, cross-session queries, and team-shared storage are added.

**Alternatives Evaluated**:
- **Raw sqlite3**: Works, but migrations and query building become manual pain points at scale.
- **SQLAlchemy ORM**: Adds complexity for what starts as key-value storage.
- **TinyDB**: Suitable for tiny projects; not for the query complexity anticipated in V2+.
- **MongoDB**: Heavyweight server dependency; violates local-first for MVP.

---

## SD-005: CLI Framework — Typer + Rich

**Decision**: Typer for CLI structure; Rich for output formatting.

**Alternatives Evaluated**:
- **Click**: Typer is built on Click and adds type inference, reducing boilerplate.
- **argparse**: Too verbose for the command surface anticipated.
- **Colorama**: Rich is a superset of Colorama's capabilities.

**Reasoning**: Typer infers CLI arguments from Python type hints, eliminating repetitive decorator code. Rich provides tables, progress bars, syntax-highlighted output, and Markdown rendering — exactly what a task execution interface needs.

---

## SD-006: Configuration — YAML + pydantic-settings

**Decision**: YAML for config files; `pydantic-settings` for validation and env-var overrides.

**Alternatives Evaluated**:
- **TOML**: Less ambiguous than YAML. Strongly considered; YAML wins on familiarity with developer tooling (Docker Compose, GitHub Actions).
- **JSON**: No comments; bad for human-edited config.
- **Python files**: Executable config is a security risk.

**Reasoning**: YAML is the most widely understood config format in the tooling space. Pydantic Settings integrates validation and env-var overrides in one step. The YAML Norway problem and type coercion issues are mitigated by loading everything through Pydantic.

---

## SD-007: Logging — structlog

**Decision**: `structlog` for structured logging.

**Alternatives Evaluated**:
- **stdlib `logging`**: Works, but lacks structured context and JSON output without additional setup.

**Reasoning**: `structlog` adds structured context and JSON output without replacing `logging`. JSON in production, human-readable in development. No meaningful additional complexity.

---

## SD-008: Testing — pytest Ecosystem

**Decision**: pytest as the test runner with standard plugins.

**Alternatives Evaluated**:
- **unittest**: More boilerplate; pytest is the community standard.
- **nose2**: Effectively deprecated.

**Reasoning**: pytest's fixture system, parametrize decorator, and plugin ecosystem (pytest-asyncio, pytest-cov, pytest-mock) cover all testing needs.

---

## SD-009: Linting and Formatting — Ruff + Black + Mypy

**Decision**: Ruff for linting and import sorting; Black for formatting; Mypy for type checking.

**Alternatives Evaluated**:
- **Flake8 + isort**: Ruff replaces both with a Rust-based implementation 10-100x faster.
- **Pylint**: More opinionated and slower; most useful rules covered by Ruff + Mypy.
- **Pyright**: Strong alternative to Mypy; can run as an optional second pass.

**Reasoning**: Ruff + Black + Mypy is the emerging standard for modern Python projects. Ruff's speed makes it practical to run on every commit.

---

## Deferred Stack Decisions (V2+)

The following technology decisions are correct for the long term but are not needed for the MVP.

| ID | Decision | Deferred Until | Reason |
|---|---|---|---|
| SD-D01 | **httpx** as the HTTP client | Milestone 3 | No outbound HTTP calls are needed in the MVP (Shell integration uses subprocess). httpx becomes necessary when the Claude Code or OpenHands integrations are added. |
| SD-D02 | **FastAPI** for web interface | Milestone 5 | The web UI is a convenience layer over the CLI. Building it before the CLI is proven adds risk. FastAPI is still the right choice when the time comes. |
| SD-D03 | **SQLAlchemy Core + Alembic** | Milestone 2 | JSON files are sufficient for single-developer run history. SQLAlchemy is needed when the Memory Manager requires cross-session queries and team-shared storage. |
| SD-D04 | **ChromaDB** for semantic memory | Beyond 1.0 | Semantic search over task history improves context relevance but requires an embedding model and vector store. Not needed until semantic memory is a roadmap feature. |
| SD-D05 | **In-process Event Bus** | Milestone 2 | With one synchronous CLI workflow, direct function calls are simpler. An event bus becomes useful when the web UI needs real-time updates and the audit log needs to observe every component. |
| SD-D06 | **importlib.metadata Plugin System** | Milestone 6 | Plugin discovery requires a stable adapter interface API and a mature community. Both are Version 3+ concerns. |

---

## Decision Log

| ID | Date | Status | Summary |
|---|---|---|---|
| SD-001 | 2026-08 | Active | Python 3.12+ |
| SD-002 | 2026-08 | Active | pip + pyproject.toml |
| SD-003 | 2026-08 | Active | LiteLLM |
| SD-004 | 2026-08 | Active (MVP: JSON; V2+: SQLAlchemy+SQLite) | Storage |
| SD-005 | 2026-08 | Active | Typer + Rich |
| SD-006 | 2026-08 | Active | YAML + pydantic-settings |
| SD-007 | 2026-08 | Active | structlog |
| SD-008 | 2026-08 | Active | pytest |
| SD-009 | 2026-08 | Active | Ruff + Black + Mypy |
| SD-D01 | 2026-08 | Deferred (Milestone 3) | httpx |
| SD-D02 | 2026-08 | Deferred (Milestone 5) | FastAPI |
| SD-D03 | 2026-08 | Deferred (Milestone 2) | SQLAlchemy + Alembic |
| SD-D04 | 2026-08 | Deferred (Beyond 1.0) | ChromaDB |
| SD-D05 | 2026-08 | Deferred (Milestone 2) | In-process Event Bus |
| SD-D06 | 2026-08 | Deferred (Milestone 6) | Plugin System |
