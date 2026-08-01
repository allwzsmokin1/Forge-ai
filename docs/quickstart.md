# Quickstart

> ⚠️ OrchestrAI is pre-alpha. This quickstart describes the planned MVP experience (Milestone 2). It will be updated as components are implemented.

## Prerequisites

- Python 3.12 or newer
- pip

## Installation

```bash
pip install orchestrai
```

## Initialize a Project

Navigate to your project directory and run:

```bash
orchestrai init
```

This creates an `.orchestrai/` directory with a `config.yaml` file:

```yaml
project:
  name: my-project
  description: ""

memory:
  backend: sqlite
  path: .orchestrai/memory.db

tools:
  # Register AI tools here
  # - shell  (built-in, always available)
```

## Run Your First Goal

```bash
orchestrai run "Audit this project for TODO comments and create a summary report"
```

OrchestrAI will:
1. Decompose the goal into tasks.
2. Route each task to the best available tool.
3. Execute the tasks and display a structured result.
4. Store the task history in `.orchestrai/memory.db`.

## View Task History

```bash
orchestrai history
```

## Next Steps

- [Add an integration](../integrations/README.md) to use a real AI tool
- [Understand the architecture](../../ARCHITECTURE.md)
- [Read the Mission Director docs](kernel/README.md)
