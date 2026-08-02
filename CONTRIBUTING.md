# Contributing to OrchestrAI

Thank you for your interest in contributing. OrchestrAI is designed from the ground up to be community-driven, and contributions of all kinds are welcome — not just code.

---

## Ways to Contribute

| Contribution Type | Where to Start |
|---|---|
| **Bug report** | [Open a GitHub Issue](../../issues/new?template=bug_report.md) |
| **Feature request** | [Start a GitHub Discussion](../../discussions/new) |
| **Documentation improvement** | Edit files in `docs/` or top-level `.md` files |
| **New integration** | Read the [Integration Guide](docs/integrations/README.md) first |
| **Kernel contribution** | Read [ARCHITECTURE.md](ARCHITECTURE.md) and open a Discussion first |
| **Test coverage** | Look for untested paths in `tests/` |
| **Translation** | Ask in Discussions before starting |

---

## Before You Start

### For small changes (docs, typos, test additions)
Open a pull request directly. No prior Discussion needed.

### For medium changes (new features, new integrations)
Open a GitHub Discussion to validate the approach before writing code. This saves everyone time if the direction needs adjustment.

### For large changes (kernel architecture, adapter interface changes, new layers)
Open a Discussion and wait for explicit maintainer acknowledgment before starting work. Adapter interface changes require a major version bump and affect every integration.

---

## Development Setup

### Prerequisites

- Python 3.12 or newer
- Git
- A virtual environment manager (`venv`, `pyenv`, or `uv`)

### Clone and Install

```bash
git clone https://github.com/allwzsmokin1/Forge-ai.git
cd Forge-ai
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### Run the Tests

```bash
pytest
```

### Run the Linter and Type Checker

```bash
ruff check .
mypy .
```

### Run the Formatter

```bash
black .
```

All of the above run automatically on every pull request via GitHub Actions. Your PR must pass all checks before it can be merged.

---

## Code Standards

### Style

- **Black** enforces formatting. Run `black .` before committing. No style debates.
- **Ruff** enforces lint rules. Run `ruff check .` to see violations.
- Line length is 100 characters.

### Types

- All new kernel code must pass `mypy --strict`.
- All new adapter interfaces must be fully typed.
- Integrations and UI code must pass `mypy` at normal strictness.

### Docstrings

- Google-style docstrings on all public functions, classes, and modules.
- Private helpers (prefixed `_`) do not require docstrings but benefit from a single-line comment when the purpose is not obvious.

### Tests

- Every new public function must have at least one unit test.
- Every bug fix must include a regression test that fails before the fix and passes after.
- Test files mirror the source structure: `kernel/director.py` → `tests/unit/kernel/test_director.py`.
- Integration tests go in `tests/integration/`.
- End-to-end tests go in `tests/e2e/`.
- Tests must not make real network calls. Use `respx` to mock HTTP requests.

### Commits

- Use [Conventional Commits](https://www.conventionalcommits.org/) format:
  ```
  feat(kernel): add task retry logic to Mission Director
  fix(memory): handle empty history gracefully
  docs: clarify adapter interface contract in ARCHITECTURE.md
  test(integration): add tests for shell adapter
  ```
- Keep commits atomic: one logical change per commit.
- Do not mix refactoring with feature changes in the same commit.

---

## Pull Request Process

1. **Fork** the repository and create a branch from `main`.
2. Name your branch descriptively: `feat/shell-integration`, `fix/memory-empty-history`, `docs/contributing-cleanup`.
3. Make your changes following the code standards above.
4. Run `pytest`, `ruff check .`, `mypy .`, and `black --check .` locally before pushing.
5. Open a pull request against `main`.
6. Fill in the pull request template completely.
7. A maintainer will review within 7 days. Large changes may take longer.
8. Address review feedback in additional commits on the same branch. Do not force-push after review has started.
9. Once approved, a maintainer will squash-merge your PR.

### Pull Request Checklist

Every PR must satisfy the following before merge:

- [ ] All CI checks pass (tests, lint, type check, format)
- [ ] New code has tests
- [ ] Documentation updated if public API changed
- [ ] `CHANGELOG.md` entry added (for user-facing changes)
- [ ] No new dependencies added without a `REUSE_FIRST_BLUEPRINT.md` update and maintainer approval
- [ ] Adapter interface changes (if any) noted prominently with versioning impact

---

## Architecture Constraints (Must Not Violate)

All contributors must read [ARCHITECTURE.md](ARCHITECTURE.md) before contributing to the kernel. The following constraints are enforced by CI and will cause your PR to fail if violated:

1. **No circular imports** — `ruff` checks import order; `mypy` catches circular type dependencies.
2. **Kernel has no direct imports from `integrations/`** — the kernel depends only on adapter interfaces.
3. **No hardcoded configuration values** — all configuration goes through `kernel/config.py`.
4. **No test code in production code** — no `if __name__ == "__main__"` blocks in library code.

---

## Adding a New Integration

Integrations live in `integrations/<tool-name>/`. Each integration must:

1. Implement the `TaskAdapter` interface.
2. Include its own tests in `tests/integration/<tool-name>/`.
3. Include a `README.md` in the integration directory explaining setup and configuration.
4. Add a dependency health checklist for any new packages it requires.

The Shell integration (`integrations/shell/`) is the reference implementation.

> **Note**: `CapabilityAdapter` and `LifecycleAdapter` are deferred to Version 2. New integrations only need to implement `TaskAdapter` for the MVP milestone.

See `docs/integrations/README.md` for the full integration guide.

---

## Reporting Security Vulnerabilities

**Do not open a public GitHub Issue for security vulnerabilities.**

Email the maintainers at security@orchestrai.dev (or open a private GitHub Security Advisory). Include:

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if known)

We commit to acknowledging reports within 48 hours and resolving confirmed vulnerabilities within 90 days.

---

## License

By contributing to OrchestrAI, you agree that your contributions will be licensed under the Apache 2.0 License.

### Why Apache 2.0?

OrchestrAI coordinates proprietary AI tools and services. Apache 2.0 was chosen over MIT for the following reasons:

1. **Explicit patent grant** — Apache 2.0 includes an explicit, royalty-free patent grant from contributors to users. This is important for a project that may interact with patented AI systems and models. MIT does not include an explicit patent grant.

2. **Enterprise adoption** — Many organizations require Apache 2.0 for their open-source usage policies. MIT is generally acceptable too, but Apache 2.0 is more explicitly permissive on patents.

3. **Compatibility** — Apache 2.0 is compatible with MIT, BSD, and most permissive licenses used by OrchestrAI's dependencies. It is not compatible with GPL v2 (only v3), which is why GPL v2 dependencies are avoided.

4. **Contributor protection** — The contribution terms are explicit. Contributors grant a patent license for their contributions, protecting both contributors and users.

5. **Industry standard for infrastructure** — Apache Kafka, Apache Spark, Kubernetes, TensorFlow, and hundreds of other infrastructure projects use Apache 2.0. OrchestrAI aspires to be infrastructure; Apache 2.0 fits that positioning.

The full license text is in [LICENSE](LICENSE).

---

## Code of Conduct

OrchestrAI follows the [Contributor Covenant](https://www.contributor-covenant.org/) Code of Conduct. By participating, you agree to uphold it.

In short: be respectful, be constructive, be patient. Technical disagreements are healthy. Personal attacks are not.

---

## Recognition

All contributors are listed in [CONTRIBUTORS.md](CONTRIBUTORS.md) (created at Milestone 1). Significant contributors may be invited to become maintainers.
