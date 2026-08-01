# Integrations

The `integrations/` directory contains connectors for external AI tools and services.

## What Goes Here

Each subdirectory is a self-contained integration for one external tool:

```
integrations/
├── shell/               # Generic shell command integration (built-in)
├── claude_code/         # Anthropic Claude Code
├── openhands/           # OpenHands code execution
└── copilot/             # GitHub Copilot
```

## What Does Not Go Here

- Business logic (that belongs in `kernel/`)
- Adapter interface definitions (those belong in `adapters/`)
- Configuration management (that belongs in `kernel/config.py`)

## Building an Integration

Each integration must:

1. Implement `TaskAdapter` at minimum.
2. Implement `CapabilityAdapter` to enable intelligent routing.
3. Include its own tests in a `tests/` subdirectory.
4. Include a `README.md` with setup instructions.

See [docs/integrations/README.md](../docs/integrations/README.md) for the full guide.

## Status

The `shell` integration is planned for **Milestone 2** (MVP).
Additional integrations are planned for **Milestone 4**.
