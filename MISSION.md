# OrchestrAI Mission

## Purpose

OrchestrAI exists to solve a specific, painful problem: **the coordination gap in AI-assisted software development**.

As the number of capable AI coding tools grows — GitHub Copilot, OpenHands, Claude Code, Codex, Cursor, Devin, and dozens more — developers face an increasingly fragmented workflow. Each tool is capable in isolation, but none of them:

- Remembers decisions made in previous sessions.
- Knows which other tools are available and when to use them.
- Maintains a coherent view of the project's architecture, history, and current state.
- Plans multi-step work and routes subtasks to the right agent automatically.

OrchestrAI fills that gap. It is the **operating environment** for AI development tools — not a replacement for any of them.

---

## What OrchestrAI Is

OrchestrAI is an **AI Operating Environment** built around four core responsibilities:

### 1. Mission Direction
A Mission Director component accepts high-level goals from a developer ("Migrate this service from REST to GraphQL") and decomposes them into concrete, ordered tasks. It maintains awareness of what has been done, what has failed, and what remains.

### 2. Context Management
AI tools have limited context windows. OrchestrAI maintains a structured, persistent project context — architecture decisions, key files, coding conventions, past decisions, and lessons learned — and injects only the relevant slice into each tool interaction.

### 3. Long-Term Memory
Project memory persists across sessions, across tools, and across team members. When a developer returns to a task three weeks later, OrchestrAI can reconstruct the context without the developer having to re-explain it.

### 4. Intelligent Task Routing
Different AI tools have different strengths. OrchestrAI maintains a capability registry and routes each task to the most appropriate tool, with fallback strategies when a primary tool is unavailable or fails.

---

## What OrchestrAI Is Not

OrchestrAI deliberately avoids competing with the tools it coordinates.

| Not This | Why |
|---|---|
| A coding assistant | GitHub Copilot, Claude Code, and Codex already do this. |
| A code execution environment | OpenHands, E2B, and similar tools already do this. |
| A version control system | Git already does this. |
| An IDE | VS Code, JetBrains, and others already do this. |
| A CI/CD system | GitHub Actions, CircleCI, and others already do this. |

OrchestrAI's unique value is **coordination and memory**. Building any of the above would expand scope without adding differentiation.

---

## Non-Goals

The following are explicitly out of scope for OrchestrAI, even if they could theoretically be added:

- **Writing production code directly.** OrchestrAI plans and routes; other tools execute.
- **Replacing human judgment.** Developers approve plans before execution; OrchestrAI does not act autonomously by default.
- **Proprietary lock-in.** Every integration, adapter, and backend must be replaceable.
- **Cloud dependency.** The full system must work locally with no external services required.
- **Language-specific features.** OrchestrAI is language-agnostic at the kernel level.

---

## Target Users

OrchestrAI is designed for:

- **Individual developers** who use multiple AI tools and want a unified workflow.
- **Small teams** who need shared AI context and decision history.
- **Open-source maintainers** who want to accelerate contribution review and onboarding.
- **Platform teams** who want to expose AI-assisted development to internal developers through a controlled, auditable interface.

---

## Long-Term Vision

In three to five years, OrchestrAI should be the **standard coordination layer** for AI-assisted software development — the way Make, npm, and Docker became standard coordination layers for build, dependency, and deployment workflows respectively.

A developer should be able to:

1. Open a project in any editor.
2. Describe a goal in natural language.
3. Have OrchestrAI plan the work, assign it to available tools, preserve all decisions and outputs, and report back with a structured result.

The system should be fully auditable, fully local if desired, and deeply integrated with the existing development toolchain — not a replacement for it.

---

## Relationship to Forge-AI

OrchestrAI supersedes and reframes the earlier Forge-AI project. Forge-AI's agent and memory work forms the technical foundation, but OrchestrAI's scope is broader: it is an operating environment, not a single-agent system. The Forge-AI codebase will be refactored into OrchestrAI's `kernel/` and `adapters/` layers as those milestones are reached.
