# OrchestrAI Documentation

This directory contains all project documentation beyond the top-level files.

## Contents

| Directory / File | Purpose |
|---|---|
| `index.md` | Documentation home page and navigation guide |
| `quickstart.md` | Get OrchestrAI running in 5 minutes |
| `kernel/` | Kernel component documentation (Mission Director, Context Manager, Memory, Router) |
| `adapters/` | Adapter interface reference and implementation guide |
| `integrations/` | How to build and register integrations |
| `contributing/` | Detailed contribution guides (supplements top-level CONTRIBUTING.md) |

## Building the Docs

> Documentation tooling is set up at Milestone 1. This section will be updated then.

The documentation site will be built with [MkDocs](https://www.mkdocs.org/) + [Material theme](https://squidfunk.github.io/mkdocs-material/).

```bash
pip install mkdocs mkdocs-material
mkdocs serve       # local preview
mkdocs build       # build static site
```

## Contributing to Docs

Documentation improvements are always welcome. See [CONTRIBUTING.md](../CONTRIBUTING.md) for the pull request process.

Docs changes that fix factual errors or improve clarity do not require a prior Discussion. Structural reorganizations of the docs should be discussed first.
