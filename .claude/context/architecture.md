# Querybook Architecture Overview

## High-Level System Architecture

Querybook is a web-based SQL IDE and notebook platform with a layered architecture:

- **Backend**: Python/Flask REST API (`querybook/server/`)
- **Frontend**: TypeScript/React SPA (`querybook/webapp/`)
- **Database**: MySQL/PostgreSQL for metadata storage
- **Search**: Elasticsearch for table/query search
- **Task Queue**: Celery for async jobs (data syncing, query execution)
- **Plugins**: Extensible metastore, executor, and authentication integrations

## Key Directory Structure

```
querybook/
├── server/              # Python backend (Flask)
│   ├── app/            # Flask app initialization, routes
│   ├── datasources/    # REST API endpoints
│   ├── datasources_socketio/  # WebSocket handlers
│   ├── lib/            # Core libraries (metastore, executors, etc.)
│   ├── logic/          # Business logic layer
│   ├── models/         # SQLAlchemy ORM models
│   ├── tasks/          # Celery async tasks
│   └── clients/        # External service clients
│
├── webapp/             # TypeScript/React frontend
│   ├── components/     # React components
│   ├── ui/            # Shared UI components
│   ├── redux/         # Redux state management
│   ├── lib/           # Utilities and helpers
│   ├── resource/      # API client and data fetching
│   ├── hooks/         # Custom React hooks
│   └── const/         # Constants and types
│
├── migrations/         # Alembic database migrations
├── config/            # Configuration files
├── scripts/           # CLI scripts and utilities
└── tests/             # Integration tests
```

## Backend Architecture (Python/Flask)

### Core Components

**Flask Application** (`server/app/`)
- REST API endpoints
- Authentication middleware
- Request/response handling
- Environment management

**Data Sources** (`server/datasources/`)
- REST API route definitions
- Request validation
- Response formatting
- Organized by resource type (tables, queries, datadocs, etc.)

**Business Logic** (`server/logic/`)
- Core business logic layer
- Separates business rules from routes
- Handles data transformations and validations

**Models** (`server/models/`)
- SQLAlchemy ORM models
- Database schema definitions
- Key models:
  - `DataTable`: Physical tables in query engines
  - `DataSchema`: Schema/database grouping
  - `DataTableColumn`: Column metadata
  - `QueryExecution`: Query run history
  - `DataDoc`: Notebook documents
  - `User`, `Environment`: User and workspace management

**Libraries** (`server/lib/`)
- **`metastore/`**: Metastore integrations (Hive, Glue, etc.)
  - Base class: `BaseMetastoreLoader`
  - Implementations: `HMSMetastoreLoader`, `GlueMetastoreLoader`
- **`query_executor/`**: Query engine integrations (Presto, Hive, etc.)
- **`table_upload/`**: CSV/Excel data upload
- **`elasticsearch/`**: Search indexing
- **`export/`**: Query result export

**Async Tasks** (`server/tasks/`)
- Celery tasks for background jobs
- Table metadata syncing
- Query execution
- Scheduled data refreshes

### Plugin Architecture

Querybook uses a plugin system for extensibility:

**Metastore Loaders** (`server/lib/metastore/`)
- Abstract base: `BaseMetastoreLoader`
- Implement methods:
  - `get_all_schema_names()`: List schemas/databases
  - `get_all_table_names_in_schema()`: List tables in schema
  - `get_table_and_columns()`: Fetch table metadata
  - `get_table_display_name()` (optional): Custom table naming

**Query Executors** (`server/lib/query_executor/`)
- Abstract base: `QueryExecutor`
- Handle query execution, cancellation, status polling

**Auth Handlers**
- Custom authentication/authorization logic
- Integration with OAuth, LDAP, etc.

## Frontend Architecture (TypeScript/React)

### Component Organization

**UI Components** (`webapp/ui/`)
- Reusable, generic UI components
- Button, Input, Modal, Table, etc.
- Not business-logic specific

**Domain Components** (`webapp/components/`)
- Business-specific components
- `DataDocCell`, `QueryEditor`, `TableView`, etc.
- Organized by feature area

**State Management** (`webapp/redux/`)
- Redux for global state
- Slices for different domains (datadocs, queries, tables, users)
- Async actions for API calls

**API Client** (`webapp/resource/`)
- Centralized API calls
- Type-safe interfaces
- Auto-generated from backend routes

**Utilities** (`webapp/lib/`)
- Helper functions
- Data transformations
- Business logic utilities
- Key files:
  - `table-identifier.ts`: Table name parsing and formatting
  - `query-result-export.ts`: Result export logic

### Data Flow

1. **User Action** → Component
2. **Component** → Redux Action
3. **Redux Action** → API Resource call
4. **API Resource** → Backend REST endpoint
5. **Backend** → Database/Metastore/Query Engine
6. **Response** → Redux State Update
7. **Redux State** → Component Re-render

## Database Models Overview

### Core Data Models

**DataTable** (`server/models/data_table.py`)
- Represents a physical table in a query engine
- Fields: `schema_id`, `name`, `type`, `owner`, `table_created_at`
- Relationships: columns, schema, warnings, lineage

**DataSchema** (`server/models/data_schema.py`)
- Represents a schema/database grouping
- Fields: `metastore_id`, `name`, `catalog` (nullable)
- Relationships: tables, metastore

**DataTableColumn** (`server/models/data_table_column.py`)
- Column metadata for tables
- Fields: `table_id`, `name`, `type`, `comment`

**Metastore** (`server/models/metastore.py`)
- Query engine/metastore connection
- Fields: `name`, `metastore_params`, `loader`
- One metastore can have multiple schemas

**QueryExecution** (`server/models/query_execution.py`)
- Query run history and results
- Fields: `query`, `engine_id`, `status`, `result_row_count`

**DataDoc** (`server/models/datadoc.py`)
- Notebook documents
- Contains multiple cells (query, text, chart)

### Catalog Support (Recent Addition)

Querybook is being enhanced to support 3-level naming: `catalog.schema.table`

**Key Changes:**
- `DataSchema.catalog` field added (nullable for backward compatibility)
- Table identifiers support optional catalog prefix
- Metastore loaders can optionally implement catalog-aware methods
- UI components updated to display and parse catalog names

See `DataSchema` model and metastore loader implementations for details.

## Metastore Integration Patterns

### Metastore Loader Flow

1. **Configuration**: Admin configures metastore in UI
2. **Loader Selection**: System selects appropriate loader based on `metastore_params.loader`
3. **Schema Discovery**: `get_all_schema_names()` called on schedule
4. **Table Discovery**: For each schema, `get_all_table_names_in_schema()` called
5. **Metadata Sync**: For each table, `get_table_and_columns()` fetches metadata
6. **Indexing**: Metadata indexed in Elasticsearch for search

### Catalog-Aware Loaders

For 3-level naming systems (e.g., Glue, Unity Catalog):
- Loader can return `catalog.schema` strings from `get_all_schema_names()`
- Or use DataSchema objects with explicit catalog field
- System parses identifier and stores catalog separately

See metastore loader implementations for examples.

## Backend/Frontend Interaction

### REST API Communication

**API Endpoints** (`server/datasources/`)
- RESTful routes organized by resource
- Example: `/api/table/<table_id>` → `table.py`

**Frontend API Client** (`webapp/resource/`)
- Typed API calls
- Example: `TableResource.get(tableId)` → `/api/table/<table_id>`

**WebSocket Communication** (`server/datasources_socketio/`)
- Real-time updates for query execution
- Live collaboration on datadocs

### Authentication Flow

1. User logs in → Backend validates credentials
2. Backend creates session → Cookie stored
3. Frontend includes session cookie in API requests
4. Backend validates session on each request

## Testing Patterns

### Backend Tests
- **Unit tests**: `tests/` (pytest)
- **Model tests**: Test SQLAlchemy models
- **Logic tests**: Test business logic functions
- **Integration tests**: Test API endpoints

### Frontend Tests
- **Unit tests**: `webapp/__tests__/` (Jest)
- **Component tests**: React Testing Library
- **Snapshot tests**: UI component snapshots

### Running Tests

```bash
# Backend tests
pytest tests/

# Frontend tests
npm test

# Type checking
mypy querybook/server/
npm run type-check
```

## Development Workflow

### Local Setup

1. **Backend**: Python virtual environment, Flask dev server
2. **Frontend**: Node.js, Webpack dev server with hot reload
3. **Database**: Local MySQL/PostgreSQL
4. **Elasticsearch**: Docker container
5. **Celery**: Local worker for async tasks

### Code Style

**Python**:
- PEP 8 style guide
- Type hints (mypy)
- Black for formatting

**TypeScript**:
- ESLint + Prettier
- Strict TypeScript config
- React best practices

See `.claude/context/conventions.md` for detailed code conventions.

## Key Architectural Decisions

### Catalog Support Design

**Decision**: Use nullable `DataSchema.catalog` field
**Rationale**: Backward compatibility with 2-level naming systems
**Impact**: All table identifier parsing must handle both 2-level and 3-level formats

See `lib/utils/table-identifier.ts` and metastore base loader for implementation.

### Table Display Names

**Pattern**: Use utility functions for consistent table naming
- Backend: `get_table_display_name()` in metastore loaders
- Frontend: `getTableDisplayName()` in `lib/utils/table-identifier.ts`

**Formats**:
- 2-level: `schema.table`
- 3-level: `catalog.schema.table`

### Metastore Loader Abstraction

**Pattern**: Abstract base class with concrete implementations
**Benefits**:
- Easy to add new metastore integrations
- Consistent interface across loaders
- Testable in isolation

## Common Development Patterns

### Adding a New Metastore Loader

1. Create new file in `server/lib/metastore/`
2. Extend `BaseMetastoreLoader`
3. Implement required methods
4. Register loader in `server/lib/metastore/__init__.py`
5. Add tests in `tests/lib/metastore/`

### Adding a New API Endpoint

1. Define route in `server/datasources/<resource>.py`
2. Implement logic in `server/logic/`
3. Add model methods if needed in `server/models/`
4. Add frontend API call in `webapp/resource/`
5. Add Redux actions/reducers if needed
6. Use in React components

### Modifying Table Metadata

1. Update `DataTable` model if schema changes
2. Create Alembic migration in `migrations/`
3. Update metastore loader methods
4. Update API serialization
5. Update frontend types and components

## Performance Considerations

**Backend**:
- Use SQLAlchemy eager loading to avoid N+1 queries
- Cache expensive metastore calls
- Use Celery for long-running operations

**Frontend**:
- Virtualize long lists (react-window)
- Debounce search inputs
- Code splitting for large components
- Redux selectors for derived data

## Security Considerations

**Authentication**:
- Session-based auth with secure cookies
- Pluggable auth handlers

**Authorization**:
- Environment-based access control
- Table-level permissions
- Row-level security for sensitive data

**SQL Injection Prevention**:
- Parameterized queries
- Input validation
- Query sanitization

See security best practices in `.claude/context/conventions.md`.

## Related Documentation

- **Code Conventions**: `.claude/context/conventions.md`

---

**Note**: This is a high-level overview. For detailed implementation patterns, refer to the codebase directly and use Claude Code to explore specific areas.
