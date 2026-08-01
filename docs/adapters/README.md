# Adapter Interface Reference

Adapters are the contracts between the OrchestrAI kernel and external integrations. The kernel depends only on these interfaces, never on concrete integrations. This is the dependency inversion boundary that makes OrchestrAI extensible.

## Core Interfaces

### TaskAdapter

The minimum interface every integration must implement.

```python
class TaskAdapter(Protocol):
    def execute(self, task: Task, context: Context) -> TaskResult:
        """Execute a task using this tool and return a structured result."""
        ...
```

### CapabilityAdapter

Declares what the tool is good at, used by the Task Router for scoring.

```python
class CapabilityAdapter(Protocol):
    def capabilities(self) -> CapabilityProfile:
        """Return a profile describing this tool's strengths."""
        ...
```

### LifecycleAdapter

For integrations that require startup and shutdown (subprocesses, servers).

```python
class LifecycleAdapter(Protocol):
    def start(self) -> None: ...
    def stop(self) -> None: ...
    def health_check(self) -> HealthStatus: ...
```

### ContextAdapter

For integrations that need to read or write project context.

```python
class ContextAdapter(Protocol):
    def read_context(self) -> Context: ...
    def write_context(self, context: Context) -> None: ...
```

## Versioning

Adapter interfaces follow semantic versioning. Once an interface version is published:

- **Patch**: Bug fixes to documentation or default implementations. No breaking changes.
- **Minor**: New optional methods added. Backwards compatible.
- **Major**: Any change that breaks existing implementations.

Integrations that implement an adapter will not break on minor or patch upgrades.

## Implementing an Adapter

See [integrations/README.md](../integrations/README.md) for a step-by-step guide to building a new integration that implements these interfaces.

## Status

Adapter interfaces are designed for **Milestone 2** (MVP). The full specification with types and validation will be implemented then.
