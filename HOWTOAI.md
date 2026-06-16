# How to Use AI Assistants in This Repo

This guide explains how the AI-facing documentation is organized and how to drive
an AI coding assistant (Claude Code, Codex, Cursor, etc.) effectively against the
Querybook codebase. It complements — but does not duplicate — the architecture and
patterns in [`AGENTS.md`](AGENTS.md) and the human setup instructions in
[`CONTRIBUTING.md`](CONTRIBUTING.md).

## How the AI docs are organized

There is a single source of truth for AI context, with thin tool-specific stubs:

| File | Purpose |
| --- | --- |
| [`AGENTS.md`](AGENTS.md) | **Canonical** AI instructions: project overview, project structure, architecture, code patterns, and "how to add an X" recipes. |
| `.claude/CLAUDE.md` | Delegation stub for Claude Code — contains only `@../AGENTS.md`. |
| `.claude/context/architecture.md` | Deep-dive architecture, data models, development patterns. |
| `.claude/context/conventions.md` | Code style, naming, testing patterns, security practices. |
| `.claude/docs/mcp.md` | MCP server design principles and implementation guide. |
| `.claude/settings.json` | Skills marketplace configuration shared with the team. |

When you change how the codebase works, update **`AGENTS.md`** — every tool reads
from it. Do not add real content to the stub files.

## Claude Code skills

This repo ships project-specific Claude Code skills under `.claude/skills/` that
wrap common workflows. Prefer them over reconstructing commands by hand:

-   `/setup` — set up the local Python virtualenv (pyenv + deps).
-   `/test` — run unit tests (all, Python-only, JS-only, or a single file).
-   `/lint` — lint and format via pre-commit hooks and ESLint.
-   `/docker` — manage the Docker dev environment.

## Driving an assistant effectively

-   **Point it at `AGENTS.md` first.** It captures the directory layout (note that
    most code lives under the nested `querybook/` directory) and the canonical
    patterns for table identifiers, catalog support, and metastore loaders.
-   **Give it a concrete, scoped task.** Reference files by path
    (e.g. `querybook/server/lib/metastore/base_metastore_loader.py`) and line
    numbers when you can.
-   **Match existing conventions.** Ask the assistant to follow
    `.claude/context/conventions.md` — for example, Python imports go at the top of
    the file, never inline inside functions.
-   **Use the utility functions, not hand-built strings.** Table names should go
    through `parse_schema_identifier()` (backend) or `getTableDisplayName()`
    (frontend), as described in `AGENTS.md`.

## Guardrails

-   **Don't let the assistant invent paths or APIs.** This codebase has drifted
    from older docs before (e.g. the `server/`/`webapp/` directories are under
    `querybook/`, not the repo root). Verify any file path or symbol the assistant
    cites against the working tree.
-   **Plugins extend; core stays generic.** New engine/metastore/auth/exporter
    integrations belong in `plugins/` or the appropriate `loaders/` directory and
    registry — not as edits to core flow.
-   **Secrets and credentials** (Okta/AWS profiles, OAuth config) are never
    committed. Local auth lives in your environment — see `CONTRIBUTING.md`.

## Verifying AI output

Before merging assistant-generated changes:

1. **Read the diff.** Confirm it touches only the files you expect and follows the
   surrounding style.
2. **Run lint + type checks:** `yarn lint`, `yarn tsc-check`.
3. **Run the relevant tests:** `/test` (or the explicit commands in
   `CONTRIBUTING.md`). Run the focused test file for the area you changed, then the
   full suite.
4. **Check claims against source.** If the assistant asserts a function, path, or
   behavior, confirm it exists rather than trusting the prose.
