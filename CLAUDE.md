# Agent Guide

This file provides guidance for AI agents working with code in this repository.

## Project Overview

Querybook is a Big Data IDE web application that allows users to discover, create, and share data analyses, queries, and tables. It features a Python/Flask backend, TypeScript/React frontend, and supports multiple query engines (Trino, StarRocks, Hive, etc.) through a plugin architecture.

## Setup

Use `/setup` for initial local environment setup, and `/test`, `/lint`, `/docker` skills for guided execution.

## Architecture

```
querybook/
├── config/            # Configuration files
├── migrations/         # Alembic database migrations
├── plugins/           # Extensible plugins (metastore, executors, auth)
├── server/              # Python/Flask backend
│   ├── app/            # Flask app, routes, middleware
│   ├── datasources/    # REST API endpoints
│   ├── datasources_socketio/  # WebSocket handlers
│   ├── lib/            # Core libraries (metastore, executors, etc.)
│   ├── logic/          # Business logic layer
│   ├── models/         # SQLAlchemy ORM models
│   ├── tasks/          # Celery async tasks
│   └── clients/        # External service clients
├── tests/              # Unit and integration tests
└── webapp/             # TypeScript/React frontend
    ├── components/     # Business-specific React components
    ├── ui/            # Generic reusable UI components
    ├── redux/         # Redux state management
    ├── resource/      # API client layer
    ├── lib/           # Utilities and helpers
    ├── hooks/         # Custom React hooks
    └── const/         # Constants and types
```

### Plugin Architecture

-   **Metastore Loaders** (`server/lib/metastore/`): Integrate with metadata sources (Hive Metastore, AWS Glue, etc.)
-   **Query Executors** (`server/lib/query_executor/`): Execute queries on different engines
-   **Auth Handlers**: Custom authentication/authorization
-   **Exporters**: Export query results to external systems
-   **AI Assistants**: LLM-powered query helpers

### Key Data Models

-   **DataTable** / **DataSchema** / **DataTableColumn**: Table metadata (DataSchema supports optional `catalog` field for 3-level naming)
-   **Metastore**: Query engine/metastore connection configuration
-   **QueryExecution**: Query run history and results
-   **DataDoc**: Notebook documents containing cells (query, text, chart)

### MCP Server

The MCP server (`server/lib/mcp/`) exposes Querybook functionality over the Model Context Protocol. See `.claude/docs/mcp.md` for design patterns and implementation guide.

## Important Patterns

### Table Identifier Handling

Always use utility functions instead of manually constructing table names:

-   **Backend**: `get_table_display_name()` in metastore loaders, `parse_schema_identifier()` for parsing
-   **Frontend**: `getTableDisplayName()` in `webapp/lib/utils/table-identifier.ts`

### Catalog Support (3-Level Naming)

Querybook supports both `schema.table` and `catalog.schema.table` naming. `DataSchema.catalog` is nullable for backward compatibility. Metastore loader methods accept optional `catalog_name` parameter — the base loader uses runtime introspection to check whether your implementation accepts it.

### Metastore Loader Implementation

1. Extend `BaseMetastoreLoader` in `server/lib/metastore/`
2. Implement: `get_all_schema_names()`, `get_all_table_names_in_schema()`, `get_table_and_columns()`
3. Override `get_table_display_name()` for custom naming (e.g., catalog support)
4. Register in `server/lib/metastore/__init__.py`

## Detailed Context

-   `.claude/context/architecture.md`: Detailed architecture overview, data models, and development patterns
-   `.claude/context/conventions.md`: Code style, naming conventions, testing patterns, and security practices
-   `.claude/docs/mcp.md`: MCP server design principles and implementation guide
