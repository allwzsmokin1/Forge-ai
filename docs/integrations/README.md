# Integration Guide

Integrations connect OrchestrAI to external AI tools and services. Each integration is a self-contained Python package that implements one or more adapter interfaces.

## Built-In Integrations

| Integration | Tool | Status | Notes |
|---|---|---|---|
| `shell` | Any CLI command | Planned (M2) | Execute arbitrary shell commands as tasks |
| `claude_code` | Claude Code | Planned (M4) | Anthropic's coding agent |
| `openhands` | OpenHands | Planned (M4) | OpenHands code execution environment |
| `copilot` | GitHub Copilot | Planned (M7) | GitHub's AI coding assistant |

## Building a Custom Integration

### 1. Create the package structure

```
integrations/
└── my_tool/
    ├── __init__.py
    ├── adapter.py        # Implements TaskAdapter (required)
    ├── capabilities.py   # Implements CapabilityAdapter (recommended)
    ├── lifecycle.py      # Implements LifecycleAdapter (if tool needs start/stop)
    ├── config.py         # Tool-specific configuration model
    ├── tests/
    │   └── test_adapter.py
    └── README.md         # Setup and configuration guide
```

### 2. Implement TaskAdapter

```python
from adapters.task import TaskAdapter, Task, TaskResult, Context

class MyToolAdapter:
    def execute(self, task: Task, context: Context) -> TaskResult:
        # Call your tool here
        output = call_my_tool(task.description, context)
        return TaskResult(
            task_id=task.id,
            status="completed",
            output=output,
        )
```

### 3. Declare Capabilities

```python
from adapters.capability import CapabilityAdapter, CapabilityProfile, TaskType

class MyToolCapabilities:
    def capabilities(self) -> CapabilityProfile:
        return CapabilityProfile(
            name="my-tool",
            version="1.0.0",
            strengths=[TaskType.CODE_GENERATION, TaskType.REFACTORING],
            max_context_tokens=100_000,
        )
```

### 4. Register via Entry Points

In your `pyproject.toml`:

```toml
[project.entry-points."orchestrai.integrations"]
my_tool = "integrations.my_tool:MyToolAdapter"
```

### 5. Write Tests

Your integration must pass the adapter compliance test suite:

```python
from tests.integration.compliance import run_task_adapter_compliance_tests

def test_my_tool_adapter():
    adapter = MyToolAdapter(config=test_config())
    run_task_adapter_compliance_tests(adapter)
```

### 6. Document Setup

Your `README.md` must cover:
- Prerequisites (API keys, installed tools, etc.)
- Configuration options
- Example usage
- Known limitations

## Distributing as a Package

Integrations can be distributed as separate PyPI packages. Users install them with:

```bash
pip install orchestrai-my-tool
```

The entry point registration handles discovery automatically.

## Contributing an Integration

To include your integration in the official OrchestrAI repository:

1. Open a GitHub Discussion describing the tool and your intended implementation.
2. Receive maintainer acknowledgment.
3. Implement following the guide above.
4. Open a pull request with the full integration and passing tests.

Third-party integrations not in the official repository are listed in the [Plugin Registry](https://github.com/allwzsmokin1/Forge-ai/wiki/Plugin-Registry) (created at Milestone 7).
