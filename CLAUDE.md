# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Querybook is a Big Data IDE web application that allows users to discover, create, and share data analyses, queries, and tables. It features a Python/Flask backend, TypeScript/React frontend, and supports multiple query engines (Presto, Hive, Snowflake, BigQuery, etc.) through a plugin architecture.

## Development Commands

### Initial Setup

```bash
# Quick start - runs entire stack with Docker
make

# Install dependencies for local development
make install  # Installs both Python and Node dependencies
pip install -r ./requirements.txt
yarn install --ignore-scripts --frozen-lockfile --pure-lockfile --ignore-engines
```

### Running Services

```bash
# Development mode (individual services)
make web        # Run web server
make worker     # Run Celery worker
make scheduler  # Run scheduler
make terminal   # Run terminal

# Production mode
make prod_web
make prod_worker
make prod_scheduler

# Documentation server
make docs
```

### Building

```bash
# Build Docker images
make dev_image    # Development image
make prod_image   # Production image
make test_image   # Testing image

# Build frontend assets
npm run build     # Production webpack build
npm run dev       # Development server with hot reload
```

### Testing

```bash
# Backend tests
make test  # Run full test suite in Docker
pytest querybook/tests/  # Run specific tests locally
pytest querybook/tests/test_lib/test_metastore/  # Test specific module

# Frontend tests
npm test  # Run all Jest tests
npm test -- table-identifier.test.ts  # Run specific test
npm run tsc-check  # TypeScript type checking
```

### Code Quality

```bash
# Python
black querybook/server/  # Format code
isort querybook/server/  # Sort imports
mypy querybook/server/   # Type checking

# TypeScript
npm run lint  # ESLint with auto-fix
npm run tsc-check  # Type checking
```

### Cleanup

```bash
make clean       # Clean Python and Docker artifacts
make clean_pyc   # Clean Python cache files
make clean_docker  # Clean Docker system
```

## Architecture

### High-Level Structure

```
querybook/
├── server/              # Python/Flask backend
│   ├── app/            # Flask app, routes, middleware
│   ├── datasources/    # REST API endpoints
│   ├── datasources_socketio/  # WebSocket handlers
│   ├── lib/            # Core libraries (metastore, executors, etc.)
│   ├── logic/          # Business logic layer
│   ├── models/         # SQLAlchemy ORM models
│   ├── tasks/          # Celery async tasks
│   └── clients/        # External service clients
│
├── webapp/             # TypeScript/React frontend
│   ├── components/     # Business-specific React components
│   ├── ui/            # Generic reusable UI components
│   ├── redux/         # Redux state management
│   ├── resource/      # API client layer
│   ├── lib/           # Utilities and helpers
│   ├── hooks/         # Custom React hooks
│   └── const/         # Constants and types
│
├── migrations/         # Alembic database migrations
├── config/            # Configuration files
├── plugins/           # Extensible plugins (metastore, executors, auth)
└── tests/             # Backend integration tests
```

### Data Flow

1. User Action → React Component
2. Component dispatches Redux Action
3. Redux Action calls API Resource
4. API Resource makes REST call to Flask backend
5. Backend validates, processes via Logic layer
6. Logic layer interacts with Models (database) or external services
7. Response flows back through stack to UI update

### Plugin Architecture

Querybook uses plugins for extensibility:

- **Metastore Loaders** (`server/lib/metastore/`): Integrate with metadata sources (Hive Metastore, AWS Glue, etc.)
- **Query Executors** (`server/lib/query_executor/`): Execute queries on different engines (Presto, Hive, etc.)
- **Auth Handlers**: Custom authentication/authorization
- **Exporters**: Export query results to external systems
- **AI Assistants**: LLM-powered query helpers

### Key Data Models

- **DataTable**: Represents physical tables in query engines
- **DataSchema**: Schema/database grouping (supports optional `catalog` field for 3-level naming)
- **DataTableColumn**: Column metadata
- **Metastore**: Query engine/metastore connection configuration
- **QueryExecution**: Query run history and results
- **DataDoc**: Notebook documents containing cells (query, text, chart)
- **User**, **Environment**: User and workspace management

### Catalog Support (3-Level Naming)

Querybook supports both 2-level (`schema.table`) and 3-level (`catalog.schema.table`) naming:

- `DataSchema.catalog` field is nullable for backward compatibility
- Use display name utilities for consistent formatting:
  - Backend: `get_table_display_name()` in metastore loaders
  - Frontend: `getTableDisplayName()` in `webapp/lib/utils/table-identifier.ts`
- When implementing metastore loaders, return `List[DataSchema]` objects with explicit `catalog` field for 3-level systems

## Important Patterns

### Table Identifier Handling

**Always use utility functions** instead of manually constructing table names:

```python
# Backend - metastore loader
def get_table_display_name(self, schema_name: str, table_name: str) -> str:
    """Override for catalog-aware naming"""
    catalog, schema = parse_schema_identifier(schema_name)
    if catalog:
        return f"{catalog}.{schema}.{table_name}"
    return f"{schema}.{table_name}"
```

```typescript
// Frontend - table-identifier.ts utility
import { getTableDisplayName } from 'lib/utils/table-identifier';

const displayName = getTableDisplayName(schema, table, catalog);
```

### Metastore Loader Implementation

When adding new metastore loaders:

1. Extend `BaseMetastoreLoader` in `server/lib/metastore/`
2. Implement required methods:
   - `get_all_schema_names()`: Return `List[str]` or `List[DataSchema]`
   - `get_all_table_names_in_schema(schema_name, catalog_name=None)`: Return table names
   - `get_table_and_columns(schema_name, table_name, catalog_name=None)`: Return table metadata
3. Override `get_table_display_name()` for custom naming (e.g., catalog support)
4. Register in `server/lib/metastore/__init__.py`

#### Catalog Parameter Pattern

All metastore loader methods that deal with tables include an optional `catalog_name` parameter for 3-level naming support. The base loader uses runtime introspection to check whether your implementation accepts this parameter before calling it.

**For loaders that don't support catalogs (2-level naming):**
- Option 1: Accept but ignore the parameter: `def get_table_and_columns(self, schema_name, table_name, catalog_name=None)`
- Option 2: Omit the parameter entirely: `def get_table_and_columns(self, schema_name, table_name)` - the base loader will detect this and call without it

**For loaders that support catalogs (3-level naming):**
```python
def get_table_and_columns(self, schema_name, table_name, catalog_name=None):
    if catalog_name:
        return self.client.get_table(catalog_name, schema_name, table_name)
    # Fallback to default catalog
    return self.client.get_table(self.default_catalog, schema_name, table_name)
```

This pattern provides backwards compatibility without requiring modifications to existing external loaders.

### Database Queries

Use SQLAlchemy best practices:

```python
# Avoid N+1 queries with eager loading
from sqlalchemy.orm import joinedload

tables = DataTable.query.options(
    joinedload(DataTable.schema)
).filter_by(schema_id=schema_id).all()

# Use bulk operations
db.session.bulk_save_objects(tables)
db.session.commit()
```

### React Components

Use functional components with hooks:

```typescript
interface TableViewProps {
    tableId: number;
}

export const TableView: React.FC<TableViewProps> = ({ tableId }) => {
    const [table, setTable] = useState<IDataTable | null>(null);

    useEffect(() => {
        TableResource.get(tableId).then(setTable);
    }, [tableId]);

    return <div>{table?.name}</div>;
};
```

## Testing

### Backend Tests

```bash
# Run all tests
pytest querybook/tests/

# Run specific test file
pytest querybook/tests/test_lib/test_metastore/test_base_loader.py

# Run tests with coverage
pytest --cov=querybook/server querybook/tests/
```

Tests are organized by layer:
- `tests/test_models/`: Model tests
- `tests/test_logic/`: Business logic tests
- `tests/test_lib/`: Library tests (metastore, executors)
- `tests/test_app/`: API endpoint tests

### Frontend Tests

```bash
# Run all tests
npm test

# Run specific test
npm test -- TableView.test.tsx

# Run in watch mode
npm test -- --watch
```

Test files are in `webapp/__tests__/` organized by component type.

## Git Workflow

### Branch Naming
- `feature/catalog-support` - New features
- `fix/table-refresh-bug` - Bug fixes
- `refactor/display-name-utilities` - Refactoring

### Commit Messages
Follow conventional commits:
```
feat: add catalog support to table identifiers
fix: resolve table refresh bug when catalog is present
refactor: extract display name logic to utilities
docs: update metastore loader documentation
```

## Context Documentation

This repository uses `.claude/` folder for additional context:

- `.claude/context/architecture.md`: Detailed architecture overview
- `.claude/context/conventions.md`: Comprehensive code conventions

## Docker Development

The project uses Docker Compose for development:

```bash
# Start full stack (web, worker, scheduler, databases, Elasticsearch)
docker compose --profile all --profile vectorstore up

# Development environment with code mounted for hot reload
docker-compose -f containers/docker-compose.dev.yml run web

# Run tests in isolated environment
docker-compose --file containers/docker-compose.test.yml up --abort-on-container-exit
```

Configuration files:
- `containers/docker-compose.dev.yml`: Development setup
- `containers/docker-compose.prod.yml`: Production setup
- `containers/bundled_querybook_config.yaml`: Bundled configuration

## Common Development Tasks

### Adding a New API Endpoint

1. Define route in `server/datasources/<resource>.py`
2. Implement logic in `server/logic/`
3. Add model methods if needed in `server/models/`
4. Add frontend API call in `webapp/resource/`
5. Add Redux actions/reducers if needed
6. Use in React components

### Modifying Table Metadata

1. Update `DataTable` model if schema changes
2. Create Alembic migration: `alembic revision -m "description"`
3. Update metastore loader methods
4. Update API serialization
5. Update frontend types and components

### Adding a Plugin

Create plugin in `plugins/` directory following the structure:
- `metastore_plugin/`: New metastore loaders
- `executor_plugin/`: New query executors
- `auth_plugin/`: Custom authentication
- `exporter_plugin/`: Result exporters

Each plugin has a `__init__.py` that registers with the core system.

## Performance Considerations

- Backend: Use SQLAlchemy eager loading, cache expensive metastore calls, use Celery for long operations
- Frontend: Virtualize long lists (react-window), debounce search inputs, use Redux selectors for derived data
- Database: Index catalog/schema/table fields, use bulk operations

## Security

- Always use parameterized queries (SQLAlchemy ORM)
- Sanitize user input on frontend (DOMPurify)
- Session-based auth with secure cookies
- Environment-based access control
- Never expose credentials or sensitive configuration

## Troubleshooting

### Backend Issues
- Check logs: `docker logs <container_name>`
- Verify database migrations: `alembic current`
- Test metastore connection directly in Python shell

### Frontend Issues
- Check browser console for errors
- Verify API calls in Network tab
- Check Redux DevTools for state issues
- Run `npm run tsc-check` for type errors

### Docker Issues
- Clean up: `make clean_docker`
- Rebuild images: `make dev_image`
- Check container logs: `docker-compose logs -f`
