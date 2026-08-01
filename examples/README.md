# Examples

The `examples/` directory contains working, end-to-end examples that demonstrate OrchestrAI in realistic scenarios.

## Purpose

Examples serve two purposes:
1. **Learning** — show new users and contributors how OrchestrAI works in practice.
2. **Validation** — examples are run as part of the CI pipeline to verify the system works end-to-end.

## Planned Examples

### `basic_goal/`
Demonstrates a single-tool workflow:
- Initialize OrchestrAI in a project.
- Run a simple goal using the built-in shell integration.
- View task history.

### `multi_tool_workflow/`
Demonstrates multi-tool routing:
- Register two integrations (e.g., shell + claude_code).
- Run a goal that requires both tools.
- Observe how the Task Router splits the work.

## Adding an Example

Examples must:
1. Work without modification on a clean install.
2. Include a `README.md` explaining what the example demonstrates and how to run it.
3. Include any required fixture files or test data.
4. Not require paid API keys to run the basic scenario (use a mock or stub for LLM calls).

## Status

Examples are planned for **Milestone 2** (MVP). This directory will be populated with working code at that milestone.
