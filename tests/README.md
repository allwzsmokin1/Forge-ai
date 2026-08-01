# Tests

The `tests/` directory contains all tests for OrchestrAI.

## Structure

```
tests/
├── unit/                # Unit tests — isolated, no external dependencies
│   └── kernel/          # Unit tests for kernel components
├── integration/         # Integration tests — test adapters with real or stubbed tools
└── e2e/                 # End-to-end tests — full goal execution workflows
```

## Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# With coverage report
pytest --cov=kernel --cov=adapters --cov-report=term-missing
```

## Test Standards

- **Unit tests** must not make real network calls. Use `respx` to mock HTTP requests.
- **Integration tests** may use a local test fixture for the tool being tested.
- **End-to-end tests** run against the full stack and may use real tools in CI with proper credentials.
- Every new public function must have at least one unit test.
- Every bug fix must include a regression test.
- Test files mirror source structure: `kernel/director.py` → `tests/unit/kernel/test_director.py`.

## Test Tooling

| Tool | Purpose |
|---|---|
| `pytest` | Test runner |
| `pytest-asyncio` | Async test support |
| `pytest-cov` | Coverage reporting |
| `respx` | HTTP request mocking |
| `unittest.mock` | General mocking |

See [REUSE_FIRST_BLUEPRINT.md](../REUSE_FIRST_BLUEPRINT.md) for rationale behind each tool.
