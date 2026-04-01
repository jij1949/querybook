# Querybook Code Conventions & Patterns

## Python Code Style

### PEP 8 Standards
- Follow PEP 8 style guide
- Line length: 88 characters (Black formatter default)
- Use 4 spaces for indentation
- Two blank lines between top-level definitions

### Type Hints
**Always use type hints** for function parameters and return types:

```python
# Good
def get_table_by_id(table_id: int) -> DataTable:
    return DataTable.query.get(table_id)

# Bad
def get_table_by_id(table_id):
    return DataTable.query.get(table_id)
```

**Use Optional for nullable values:**
```python
from typing import Optional

def get_schema_catalog(schema_id: int) -> Optional[str]:
    schema = DataSchema.query.get(schema_id)
    return schema.catalog if schema else None
```

**Use List, Dict, Tuple from typing:**
```python
from typing import List, Dict, Tuple

def get_table_names(schema_id: int) -> List[str]:
    return [table.name for table in DataTable.query.filter_by(schema_id=schema_id).all()]
```

### Formatting & Linting

Pre-commit hooks enforce code standards:
- **Black**: Auto-format Python code (spacing, line length)
- **Flake8**: Lint Python code (report issues)
- **Prettier**: Format TypeScript/JavaScript

See the /lint skill for running linters locally.

### Imports Organization
```python
# 1. Standard library imports
import os
from typing import List, Optional

# 2. Third-party imports
from flask import request, jsonify
from sqlalchemy import and_, or_

# 3. Local application imports
from models.data_table import DataTable
from lib.metastore.base_metastore_loader import BaseMetastoreLoader
```

### Docstrings
Use Google-style docstrings for complex functions:

```python
def sync_table(table_id: int, metastore_id: int) -> bool:
    """Sync table metadata from metastore.

    Args:
        table_id: The ID of the table to sync
        metastore_id: The ID of the metastore to sync from

    Returns:
        True if sync was successful, False otherwise

    Raises:
        MetastoreException: If metastore connection fails
    """
    pass
```

## TypeScript/React Code Style

### ESLint + Prettier
- Follow ESLint rules
- Prettier for auto-formatting
- Line length: 100 characters

### TypeScript Patterns

**Use explicit types for function parameters:**
```typescript
// Good
function getTableDisplayName(schema: string, table: string, catalog?: string): string {
    return catalog ? `${catalog}.${schema}.${table}` : `${schema}.${table}`;
}

// Bad
function getTableDisplayName(schema, table, catalog) {
    return catalog ? `${catalog}.${schema}.${table}` : `${schema}.${table}`;
}
```

**Use interfaces for object shapes:**
```typescript
interface TableIdentifier {
    schema: string;
    table: string;
    catalog?: string;
}

function parseTableName(fullName: string): TableIdentifier {
    // Implementation
}
```

**Prefer readonly for immutable data:**
```typescript
interface TableMetadata {
    readonly id: number;
    readonly name: string;
    readonly schema: string;
}
```

### React Component Patterns

**Functional components with hooks:**
```typescript
import React, { useState, useEffect } from 'react';

interface TableViewProps {
    tableId: number;
}

export const TableView: React.FC<TableViewProps> = ({ tableId }) => {
    const [table, setTable] = useState<IDataTable | null>(null);

    useEffect(() => {
        // Fetch table data
    }, [tableId]);

    return <div>{table?.name}</div>;
};
```

**Custom hooks for reusable logic:**
```typescript
function useTable(tableId: number) {
    const [table, setTable] = useState<IDataTable | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        TableResource.get(tableId).then(setTable).finally(() => setLoading(false));
    }, [tableId]);

    return { table, loading };
}
```

### Redux Patterns

**Action creators:**
```typescript
export const fetchTable = (tableId: number) => async (dispatch) => {
    dispatch({ type: 'FETCH_TABLE_REQUEST', payload: tableId });
    try {
        const table = await TableResource.get(tableId);
        dispatch({ type: 'FETCH_TABLE_SUCCESS', payload: table });
    } catch (error) {
        dispatch({ type: 'FETCH_TABLE_FAILURE', payload: error });
    }
};
```

**Selectors for derived data:**
```typescript
export const selectTableById = (state: IStoreState, tableId: number) =>
    state.tables.byId[tableId];

export const selectTableDisplayName = (state: IStoreState, tableId: number) => {
    const table = selectTableById(state, tableId);
    return table ? getTableDisplayName(table.schema, table.name, table.catalog) : null;
};
```

## Naming Conventions

### Python

**Variables and functions**: `snake_case`
```python
table_id = 123
def get_table_by_id(table_id: int) -> DataTable:
    pass
```

**Classes**: `PascalCase`
```python
class DataTable(Base):
    pass

class HMSMetastoreLoader(BaseMetastoreLoader):
    pass
```

**Constants**: `UPPER_SNAKE_CASE`
```python
MAX_TABLE_NAME_LENGTH = 255
DEFAULT_SCHEMA_NAME = "default"
```

**Private methods/attributes**: Prefix with `_`
```python
def _internal_helper(self):
    pass

self._cache = {}
```

### TypeScript

**Variables and functions**: `camelCase`
```typescript
const tableId = 123;
function getTableById(tableId: number): IDataTable {
    // ...
}
```

**Classes and interfaces**: `PascalCase`
```typescript
class TableResource {
    // ...
}

interface IDataTable {
    // ...
}
```

**Constants**: `UPPER_SNAKE_CASE`
```typescript
const MAX_TABLE_NAME_LENGTH = 255;
const DEFAULT_SCHEMA_NAME = 'default';
```

**Private methods/properties**: Prefix with `_` or use `private` keyword
```typescript
class TableCache {
    private _cache: Map<number, IDataTable> = new Map();

    private _getFromCache(id: number): IDataTable | undefined {
        return this._cache.get(id);
    }
}
```

### File Naming

**Python**: `snake_case.py`
```
base_metastore_loader.py
data_table.py
sync_table_logic.py
```

**TypeScript**: `kebab-case.ts` or `PascalCase.tsx` for React components
```
table-identifier.ts
query-result-export.ts
TableView.tsx
DataDocCell.tsx
```

## Table Identifier Patterns

### Consistent Display Name Functions

**Backend** (`server/lib/metastore/base_metastore_loader.py`):
```python
def get_table_display_name(self, schema_name: str, table_name: str) -> str:
    """Get the display name for a table.

    Override this method in subclasses to support catalog-aware naming.
    Default implementation returns 2-level name: schema.table
    """
    return f"{schema_name}.{table_name}"
```

**Frontend** (`webapp/lib/utils/table-identifier.ts`):
```typescript
export function getTableDisplayName(schema: string, table: string, catalog?: string): string {
    return catalog ? `${catalog}.${schema}.${table}` : `${schema}.${table}`;
}
```

**Usage**: Always use these utility functions instead of manually constructing table names.

### Parsing Table Identifiers

**Backend**:
```python
def parse_table_identifier(full_name: str) -> Tuple[Optional[str], str, str]:
    """Parse a full table name into (catalog, schema, table).

    Returns:
        (catalog, schema, table) tuple where catalog may be None
    """
    parts = full_name.split('.')
    if len(parts) == 3:
        return parts[0], parts[1], parts[2]
    elif len(parts) == 2:
        return None, parts[0], parts[1]
    else:
        raise ValueError(f"Invalid table identifier: {full_name}")
```

**Frontend**:
```typescript
export function parseTableIdentifier(fullName: string): TableIdentifier {
    const parts = fullName.split('.');
    if (parts.length === 3) {
        return { catalog: parts[0], schema: parts[1], table: parts[2] };
    } else if (parts.length === 2) {
        return { schema: parts[0], table: parts[1] };
    } else {
        throw new Error(`Invalid table identifier: ${fullName}`);
    }
}
```

See `.claude/docs/references/DISPLAY_NAME_TECHNICAL_REFERENCE.md` for complete reference.

## Database Query Patterns

### SQLAlchemy Best Practices

**Avoid N+1 queries with eager loading:**
```python
# Bad - N+1 query problem
tables = DataTable.query.filter_by(schema_id=schema_id).all()
for table in tables:
    print(table.schema.name)  # Triggers separate query for each table

# Good - Eager load relationships
from sqlalchemy.orm import joinedload

tables = DataTable.query.options(
    joinedload(DataTable.schema)
).filter_by(schema_id=schema_id).all()
for table in tables:
    print(table.schema.name)  # No additional query
```

**Use exists() for existence checks:**
```python
# Bad
if DataTable.query.filter_by(name=table_name).first():
    # ...

# Good
from sqlalchemy import exists

if db.session.query(exists().where(DataTable.name == table_name)).scalar():
    # ...
```

**Bulk operations for performance:**
```python
# Bad - One query per insert
for table_data in tables:
    table = DataTable(**table_data)
    db.session.add(table)
    db.session.commit()

# Good - Bulk insert
tables = [DataTable(**data) for data in tables_data]
db.session.bulk_save_objects(tables)
db.session.commit()
```

## Testing Patterns

### Backend Testing (pytest)

**Test organization:**
```
tests/
├── test_models/
│   └── test_data_table.py
├── test_logic/
│   └── test_table_logic.py
├── test_lib/
│   └── test_metastore/
│       └── test_hms_loader.py
└── conftest.py  # Shared fixtures
```

**Test naming:**
```python
def test_get_table_display_name_with_catalog():
    """Test that display name includes catalog when present."""
    pass

def test_get_table_display_name_without_catalog():
    """Test that display name excludes catalog when absent."""
    pass
```

**Fixtures for common test data:**
```python
import pytest

@pytest.fixture
def sample_table():
    return DataTable(
        name="test_table",
        schema_id=1,
        type="table"
    )

def test_table_creation(sample_table):
    assert sample_table.name == "test_table"
```

### Frontend Testing (Jest)

**Test organization:**
```
webapp/__tests__/
├── components/
│   └── TableView.test.tsx
├── lib/
│   └── table-identifier.test.ts
└── redux/
    └── table-actions.test.ts
```

**Component testing with React Testing Library:**
```typescript
import { render, screen } from '@testing-library/react';
import { TableView } from 'components/TableView';

describe('TableView', () => {
    it('displays table name with catalog', () => {
        render(<TableView tableId={1} />);
        expect(screen.getByText(/catalog\.schema\.table/)).toBeInTheDocument();
    });
});
```

**Utility function testing:**
```typescript
import { getTableDisplayName } from 'lib/utils/table-identifier';

describe('getTableDisplayName', () => {
    it('returns 3-level name when catalog is provided', () => {
        expect(getTableDisplayName('schema', 'table', 'catalog')).toBe('catalog.schema.table');
    });

    it('returns 2-level name when catalog is omitted', () => {
        expect(getTableDisplayName('schema', 'table')).toBe('schema.table');
    });
});
```

## Run tests inside the Docker container

### Requirements
1. Bash into the web docker container: `docker exec -it querybook_web bash`
2. Install the Python requirements: `pip install -r requirements/test.txt`
3. Set the env variables:
```
export AI_ASSISTANT_PROVIDER=
export PUBLIC_URL=
```
4. Install Pytest Watch: `pip install pytest-watch`

### Python tests
Run for Python unit tests: `PYTHONPATH=querybook/server:plugins ./querybook/scripts/run_test --python`
Run for Python unit tests with pytest watch: `PYTHONPATH=querybook/server:plugins ptw`

### Typescript:
Run for TypeScript tests: `NODE_ENV=test ./node_modules/.bin/jest --watch`


## Git Workflow

### Branch Naming
- Feature branches: `feature/catalog-support`
- Bug fixes: `fix/table-refresh-bug`
- Refactoring: `refactor/display-name-utilities`

### Commit Messages
Follow conventional commits:

```
feat: add catalog support to table identifiers

- Add optional catalog field to DataSchema model
- Update table identifier parsing to support 3-level names
- Add utility functions for consistent display name formatting
```

```
fix: resolve table refresh bug when catalog is present

The table refresh flow was not handling 3-level table names correctly.
Updated sync_table logic to parse catalog from full_name before lookup.

Fixes #123
```

```
refactor: extract display name logic to utilities

Consolidate table display name formatting into reusable utility functions.
This ensures consistent naming across backend and frontend.
```

### PR Workflow

1. **Create feature branch** from `master`
2. **Implement changes** with tests
3. **Run tests locally**: `pytest` and `npm test`
4. **Format code**: `black`, `isort`, `prettier`
5. **Type check**: `mypy` and `npm run type-check`
6. **Create PR** with descriptive title and summary
7. **Address review feedback**
8. **Merge** after approval

### PR Template

```markdown
## Description
Brief description of changes

## Motivation
Why these changes are needed

## Changes
- Bullet list of key changes

## Testing
How changes were tested

## Screenshots (if UI changes)
Before/after screenshots

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Type hints added (Python)
- [ ] Type checking passes
- [ ] Code formatted (Black/Prettier)
```

## API Design Patterns

### REST Endpoint Conventions

**URL structure:**
```
GET    /api/table/<table_id>                 # Get single table
GET    /api/tables/                          # List tables
POST   /api/table/                           # Create table
PUT    /api/table/<table_id>                 # Update table
DELETE /api/table/<table_id>                 # Delete table
POST   /api/table/<table_id>/refresh         # Action on resource
```

**Response format:**
```python
# Success response
return jsonify({
    'data': table_dict,
    'message': 'Table fetched successfully'
}), 200

# Error response
return jsonify({
    'error': 'Table not found',
    'code': 'TABLE_NOT_FOUND'
}), 404
```

**Request validation:**
```python
from flask import request
from lib.utils.validate import validate_request

@blueprint.route('/api/table/', methods=['POST'])
def create_table():
    validate_request({
        'name': str,
        'schema_id': int,
        'type': str
    })

    data = request.json
    table = DataTable(**data)
    db.session.add(table)
    db.session.commit()

    return jsonify({'data': table.to_dict()}), 201
```

## Error Handling

### Backend Error Handling

**Use custom exceptions:**
```python
class MetastoreException(Exception):
    """Raised when metastore operation fails."""
    pass

class TableNotFoundException(Exception):
    """Raised when table is not found."""
    pass
```

**Handle errors gracefully:**
```python
try:
    table = DataTable.query.get(table_id)
    if not table:
        raise TableNotFoundException(f"Table {table_id} not found")
    return table.to_dict()
except TableNotFoundException as e:
    return jsonify({'error': str(e)}), 404
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return jsonify({'error': 'Internal server error'}), 500
```

### Frontend Error Handling

**Try-catch for async operations:**
```typescript
async function fetchTable(tableId: number): Promise<IDataTable> {
    try {
        const table = await TableResource.get(tableId);
        return table;
    } catch (error) {
        console.error('Failed to fetch table:', error);
        throw error;
    }
}
```

**Display user-friendly error messages:**
```typescript
try {
    await TableResource.update(tableId, updates);
    showSuccessToast('Table updated successfully');
} catch (error) {
    showErrorToast('Failed to update table. Please try again.');
}
```

## Security Best Practices

### SQL Injection Prevention

**Always use parameterized queries:**
```python
# Bad - SQL injection vulnerable
table_name = request.args.get('name')
query = f"SELECT * FROM data_table WHERE name = '{table_name}'"
result = db.session.execute(query)

# Good - Parameterized query
table_name = request.args.get('name')
result = DataTable.query.filter_by(name=table_name).first()
```

### XSS Prevention

**Sanitize user input on frontend:**
```typescript
import DOMPurify from 'dompurify';

function renderUserContent(content: string) {
    const sanitized = DOMPurify.sanitize(content);
    return <div dangerouslySetInnerHTML={{ __html: sanitized }} />;
}
```

### Authentication Checks

**Backend - Require authentication:**
```python
from lib.decorators import require_auth

@blueprint.route('/api/table/<int:table_id>')
@require_auth
def get_table(table_id):
    # User is authenticated
    pass
```

**Frontend - Check user permissions:**
```typescript
if (!currentUser.canEditTable(tableId)) {
    return <div>You don't have permission to edit this table.</div>;
}
```

## Performance Best Practices

### Backend Performance

**Cache expensive operations:**
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_schema_names(metastore_id: int) -> List[str]:
    # Expensive metastore call
    pass
```

**Use async tasks for long operations:**
```python
from tasks.sync_table import sync_table_task

# Don't block the request
sync_table_task.delay(table_id)
return jsonify({'message': 'Sync started'}), 202
```

### Frontend Performance

**Debounce search inputs:**
```typescript
import { debounce } from 'lodash';

const debouncedSearch = debounce((query: string) => {
    dispatch(searchTables(query));
}, 300);
```

**Virtualize long lists:**
```typescript
import { FixedSizeList } from 'react-window';

<FixedSizeList
    height={600}
    itemCount={tables.length}
    itemSize={50}
    width="100%"
>
    {({ index, style }) => (
        <div style={style}>{tables[index].name}</div>
    )}
</FixedSizeList>
```

## Related Documentation

- **Architecture Overview**: `.claude/context/architecture.md`
- **Table Naming Reference**: `.claude/docs/references/DISPLAY_NAME_TECHNICAL_REFERENCE.md`
- **Catalog Support**: `.claude/docs/references/ENABLE_CATALOG_SUPPORT_TECHNICAL_REFERENCE.md`
- **Refactoring Examples**: `.claude/docs/refactoring/`

---

**Note**: These conventions are living guidelines. Update them as the codebase evolves and new patterns emerge.
