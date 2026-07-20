# Agent Guide

This file is the canonical source of context for AI coding agents working in this
repository. It covers how the code is organized and the patterns to follow when
making changes.

> Human setup, tooling, build/lint/test commands, and local auth live in
> [`CONTRIBUTING.md`](CONTRIBUTING.md). For an overview of how the AI docs fit
> together and how to drive an assistant, see [`HOWTOAI.md`](HOWTOAI.md).

## Project Overview

Querybook is a Big Data IDE web application that lets users discover, create, and
share data analyses, queries, and tables. It pairs a **Python/Flask backend**
(Flask, Celery, SQLAlchemy, Alembic, Flask-SocketIO) with a **TypeScript/React
frontend** (React 17, Redux, webpack), and supports multiple query engines
(Trino/Presto, Hive, StarRocks, Snowflake, BigQuery, MySQL, and more) through a
plugin architecture.

## Project Structure

```
querybook/
├── querybook/              # Application code (Python backend + TS/React frontend)
│   ├── config/             # YAML configuration (query engines, settings)
│   ├── migrations/         # Alembic database migrations
│   ├── server/             # Python/Flask backend
│   │   ├── app/            # Flask app, routes, middleware
│   │   ├── datasources/    # REST API endpoints
│   │   ├── datasources_socketio/  # WebSocket (Socket.IO) handlers
│   │   ├── lib/            # Core libraries (metastore, query_executor, mcp, ...)
│   │   ├── logic/          # Business logic layer
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── tasks/          # Celery async tasks
│   │   ├── scheduler/      # Scheduled job runner
│   │   ├── clients/        # External service clients
│   │   ├── runweb.py       # Web server entry point
│   │   └── run_mcp.py      # MCP server entry point
│   ├── webapp/             # TypeScript/React frontend
│   │   ├── components/     # Business-specific React components
│   │   ├── ui/             # Generic reusable UI components
│   │   ├── redux/          # Redux state management
│   │   ├── resource/       # API client layer
│   │   ├── lib/            # Utilities and helpers
│   │   ├── hooks/          # Custom React hooks
│   │   └── const/          # Constants and types
│   ├── tests/              # Python unit/integration tests
│   ├── scripts/            # Operational scripts
│   └── static/             # Static assets
├── plugins/                # Extensible plugins (metastore, executors, auth, exporters, AI, ...)
├── docs_website/           # Docusaurus documentation site (querybook.org)
├── containers/             # Docker Compose files for dev/test/prod
├── helm/, k8s/             # Deployment manifests
├── requirements/           # Python dependency sets (base, dev, test, ...)
└── Makefile                # Top-level dev/build/test targets
```

> Note: most application code lives under the nested `querybook/` directory
> (e.g. `querybook/server/`, `querybook/webapp/`). Plugins, deployment manifests,
> and docs live at the repo root.

## Architecture

### Plugin Architecture

Plugins live in the root `plugins/` directory and extend the platform without
modifying core code:

-   **Metastore Loaders** (`querybook/server/lib/metastore/`): Integrate with
    metadata sources (Hive Metastore, AWS Glue, Databricks, SQLAlchemy, etc.)
-   **Query Executors** (`querybook/server/lib/query_executor/`): Execute queries
    on different engines
-   **Auth Handlers**: Custom authentication/authorization
-   **Exporters**: Export query results to external systems
-   **AI Assistants**: LLM-powered query helpers

### Key Data Models

ORM models live in `querybook/server/models/`:

-   **DataTable** / **DataSchema** / **DataTableColumn**: Table metadata
    (`DataSchema` supports an optional `catalog` field for 3-level naming)
-   **Metastore**: Query engine/metastore connection configuration
-   **QueryExecution**: Query run history and results
-   **DataDoc**: Notebook documents containing cells (query, text, chart)

### MCP Server

The MCP server (`querybook/server/lib/mcp/`) exposes Querybook functionality over
the Model Context Protocol. The entry point is `querybook/server/run_mcp.py`. See
[`.claude/docs/mcp.md`](.claude/docs/mcp.md) for design patterns and the
implementation guide.

### Celery Task Routing (Location-Scoped Queues)

Some metastore syncs must run on a worker that has a projected OIDC token (only
available on K8s), so Celery routing pins them to the right worker population. A
`task_routes` callable in `querybook/server/tasks/routing.py` runs at dispatch
time and sends a metastore-sync task to the `k8s-only` queue when the target
metastore's loader requires an OIDC worker; everything else stays on the shared
`celery` queue.

-   **Queues:** `celery` (shared default) · `k8s-only` (OIDC-requiring work) ·
    `ec2-only` (reserved for future EC2-pinned work). Workers subscribe with
    `-Q`; a single-fleet deployment consumes all three, while a split deployment
    has each fleet consume `celery` plus its own location queue.
-   **Loader-declared requirement:** routing keys on the loader's
    `REQUIRES_OIDC_WORKER` class attribute (source of truth), not a hardcoded
    loader name. See Metastore Loader Implementation.
-   **Combo-aware:** for a `ComboMetastoreLoader`, the resolver recurses the
    combo's sub-loaders (reading config only, never instantiating a loader) and
    routes the whole chain — dispatcher, children, finalize — to `k8s-only` if
    any child requires OIDC.
-   **Fail loud:** `DatabricksUnityCatalogClient` raises a clear `RuntimeError`
    if the OIDC token file is missing, so a misrouted task fails obviously
    instead of with a cryptic SDK auth error.

## Important Patterns

### Table Identifier Handling

Always use utility functions instead of manually constructing table names:

-   **Backend**: `parse_schema_identifier()` in
    `querybook/server/logic/metastore.py` for parsing schema identifiers.
-   **Frontend**: `getTableDisplayName()` in
    `querybook/webapp/lib/utils/table-identifier.ts`.

### Catalog Support (3-Level Naming)

Querybook supports both `schema.table` and `catalog.schema.table` naming.
`DataSchema.catalog` is nullable for backward compatibility. Metastore loader
methods accept an optional `catalog_name` parameter — the base loader
(`querybook/server/lib/metastore/base_metastore_loader.py`) uses runtime
introspection (`_method_accepts_param`) to check whether your implementation
accepts it.

### Metastore Loader Implementation

1. Extend `BaseMetastoreLoader` in
   `querybook/server/lib/metastore/base_metastore_loader.py`.
2. Implement the abstract methods: `get_all_schema_names()`,
   `get_all_table_names_in_schema()`, `get_table_and_columns()`. Each optionally
   accepts a `catalog_name` parameter for 3-level naming.
3. Place the loader under `querybook/server/lib/metastore/loaders/`.
4. Register it in `querybook/server/lib/metastore/all_loaders.py`
   (add to `PROVIDED_METASTORE_LOADERS`), or provide it from a plugin via
   `ALL_PLUGIN_METASTORE_LOADERS` in the `metastore_plugin`.
5. Set `REQUIRES_OIDC_WORKER = True` on the loader if syncing it needs a
   projected OIDC token (i.e. it must run on a K8s worker). This routes its
   Celery sync tasks to the `k8s-only` queue (see Celery Task Routing). Defaults
   to `False` on `BaseMetastoreLoader`.

## Detailed Context

-   [`.claude/context/architecture.md`](.claude/context/architecture.md): Detailed
    architecture overview, data models, and development patterns.
-   [`.claude/context/conventions.md`](.claude/context/conventions.md): Code style,
    naming conventions, testing patterns, and security practices.
-   [`.claude/docs/mcp.md`](.claude/docs/mcp.md): MCP server design principles and
    implementation guide.

## Conventions

-   Always use the table-identifier utility functions above rather than hand-built
    table-name strings.
-   Python: put imports at the top of the file; do not use inline/local imports
    inside functions.
-   Match the style, naming, and patterns of the surrounding code. See
    `.claude/context/conventions.md` for the full set.
