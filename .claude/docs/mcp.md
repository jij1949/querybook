# MCP Server

The MCP server exposes Querybook functionality over the Model Context Protocol. It runs as a standalone HTTP service (`run_mcp.py`) using FastMCP with stateless HTTP transport for horizontal scaling.

> Security posture — authentication modes, authorization, audit logging, rate
> limiting, redaction, and MCP Security Standard alignment — is documented in
> [`mcp-security.md`](./mcp-security.md).

## General Design Principles

-   Tools should be designed similarly to the corresponding REST API endpoints.
-   Not all API endpoints need to be exposed as tools -- focus on those that are most useful for external integrations and automations, which would make sense for an AI agent to call directly.
-   Where necessary, tools can add additional parameters or combine multiple API calls for convenience, but should avoid unnecessary abstraction or complexity.
-   Use similar parameter names and structures in tools/resources as in the Querybook UI and API for consistency.
-   Tools should return `resource_uri` fields pointing to resources that clients can read for full content. This keeps tools focused on actions/operations and resources focused on data retrieval.
-   CRUD operations should return the updated content directly, to avoid forcing clients to make an additional read call after every mutation.

## Tool vs Resource Decision Framework

### Use Tools For:

1. **Actions/Mutations** - Create, update, delete operations

    - Examples: `create_datadoc`, `update_list`, `delete_schedule`

2. **Discovery/Search** - Finding entities through filters, keywords, or lists

    - Examples: `list_environments`, `search_datadocs`, `list_query_engines`

3. **Operations with Side Effects** - Executing queries, triggering schedules

    - Examples: `run_datadoc_cell`, `run_datadoc`

4. **Batch/Convenience Operations** - Getting multiple entities efficiently

    - Examples: `get_users([id1, id2])`, `get_current_user()`

5. **User-Visible IDs** - When users naturally have IDs from URLs (RARE EXCEPTION)
    - Examples: `get_list(123)`, `get_datadoc(456)` - IDs are visible in UI URLs

### Use Resources For:

1. **Read-only Retrieval by ID** - Getting a single entity's complete content

    - Examples: `querybook://datadoc/{id}`, `querybook://list/{id}`

2. **Nested/Hierarchical Data** - Sub-collections under parent entities

    - Examples: `querybook://schedule/{id}/runs`, `querybook://datadoc-cell/{id}/comments`

3. **Entities Discovered Through Tools** - Tools return `resource_uri`, clients read via resource
    - Pattern: `list_*()` → returns items with `resource_uri` → client reads resource
    - Examples: After `list_environments()` returns `resource_uri`, clients read `querybook://environment/{id}`

### Anti-Pattern: Avoid Redundant Tool + Resource

❌ Having both `get_foo(id)` tool AND `querybook://foo/{id}` resource for same "get by ID" operation

✓ Have `list_foos()` or `search_foos()` tool return `resource_uri` fields

✓ Clients read `querybook://foo/{id}` resource for full content

## Code Organization Pattern

**For primary entities that are directly discoverable:**

-   **Discovery Tools** (e.g., `list_datadocs`, `search_lists`) - Return lists with `resource_uri` fields
-   **Resource** (e.g., `querybook://datadoc/{id}`) - Full content retrieval
-   **Shared Logic** (e.g., `lib/mcp/lib/datadocs.py::get_datadoc_data()`) - Used by resource and any tools that need the data
-   **No get\_\* tool** - Clients use resource after discovering via lists/search

**For secondary entities discovered through parent entities:**

-   **Nested Resource** (e.g., `querybook://datadoc-cell/{id}/comments`)
-   **No separate tool** - Discovered via parent's resource_uri fields

**Entities with BOTH tool AND resource** (user-visible IDs - rare exception):

-   `querybook://datadoc/{id}` - Has `get_datadoc()` tool (ID in UI URL)
-   `querybook://list/{id}` - Has `get_list()` tool (ID in UI URL)
-   **Rationale**: Users naturally have these IDs from the UI and AI agents have difficulty discovering resource URLs without tools

**Resource-Only Entities** (IDs not user-visible - standard pattern):

-   `querybook://environment/{id}` - Discovered via `list_environments`
-   `querybook://query-engine/{id}` - Discovered via `list_query_engines`
-   `querybook://schedule/{id}` - Discovered via `list_datadoc_schedules`
-   `querybook://comment/{id}` - Discovered via cell comments or datadoc
-   `querybook://datadoc-cell/{id}` - Discovered via datadoc cells array, includes `latest_execution` for query cells
-   `querybook://datadoc-cell/{id}/comments` - Nested resource for cell comments
-   `querybook://datadoc-cell/{id}/executions{?limit,offset}` - Nested resource for cell execution history with pagination (query cells only)
-   `querybook://schedule/{id}/runs` - Nested resource for schedule runs
-   `querybook://statement-execution/{id}/results{?limit}` - Nested resource for query result data

**Special Cases:**

-   `querybook://user/{id}` - Use `get_users([id])` batch tool or `get_current_user()`

## Nested Resources

Nested resources use path-based URIs (e.g., `querybook://schedule/{schedule_id}/runs{?limit,offset}`) to represent sub-resources. This pattern is useful for:

-   **Read-only data** that is conceptually "under" a parent resource
-   **List operations** with pagination/filtering via RFC 6570 query parameters
-   **Discoverability** - the parent resource includes a `*_resource_uri` field pointing to the nested resource

Resources support optional query parameters using the `{?param1,param2}` syntax in the URI template. These parameters must have default values in the function signature. FastMCP automatically coerces query parameter values to the correct types based on type hints.

Example:

-   URI template: `querybook://schedule/{schedule_id}/runs{?limit,offset,hide_successful}`
-   Function: `def get_schedule_runs_resource(schedule_id: int, limit: int = 20, offset: int = 0, hide_successful: bool = False)`
-   Requests:
    -   `querybook://schedule/1/runs` → uses defaults (limit=20, offset=0, hide_successful=False)
    -   `querybook://schedule/1/runs?limit=5&offset=10` → overrides limit and offset
    -   `querybook://schedule/1/runs?hide_successful=true` → filters to failures only

The parent resource advertises the nested resource URI for discoverability: `get_schedule` returns `{"id": 1, "resource_uri": "querybook://schedule/1", "runs_resource_uri": "querybook://schedule/1/runs", ...}`

## Architecture

```
querybook/server/
  run_mcp.py                        # Entrypoint: creates server, registers tools & resources, starts HTTP
  lib/mcp/
    __init__.py
    auth.py                         # QuerybookTokenVerifier (API key auth)
    utils.py                        # Shared utilities (annotation constants for tools/resources)
    lib/
      lists.py                      # List serialization and data retrieval logic
      comments.py                   # Comment serialization and data retrieval logic
      datadocs.py                   # DataDoc serialization and data retrieval logic
      environments.py               # Environment serialization and data retrieval logic
      query_engines.py              # Query engine utilities (augment, data retrieval)
      schedules.py                  # Schedule serialization and data retrieval logic
      users.py                      # User serialization and data retrieval logic
    tools/
      lists.py                      # list tools (create, update, delete, list, search, add/update/remove items)
      comments.py                   # comment tools (add, list, update, delete comments; add/remove reactions)
      datadocs.py                   # datadoc tools (create, update, delete, list, search, etc.)
      environments.py               # list_environments tool
      query_engines.py              # query engine tools
      query_executions.py           # query execution tools
      schedules.py                  # schedule tools (create, update, delete, list schedules)
      users.py                      # user tools (current user, batch retrieval, search)
    resources/
      lists.py                      # querybook://list/{id} [has get_list tool]
      comments.py                   # querybook://comment/{id} [resource-only]
                                    # querybook://datadoc-cell/{id}/comments [nested resource]
      datadocs.py                   # querybook://datadoc/{id} [has get_datadoc tool]
                                    # querybook://datadoc-cell/{id} [resource-only]
                                    # querybook://datadoc-cell/{id}/executions{?limit,offset} [nested resource]
      environments.py               # querybook://environment/{id} [resource-only]
      query_engines.py              # querybook://query-engine/{id} [resource-only]
      schedules.py                  # querybook://schedule/{id} [resource-only]
                                    # querybook://schedule/{id}/runs [nested resource]
      statement_executions.py       # querybook://statement-execution/{id}/results [nested resource]
      users.py                      # querybook://user/{id} [resource-only, use batch tool]
```

-   **`run_mcp.py`** -- Creates the `FastMCP` instance, imports each tool and resource module, calls `register(mcp)`, and runs the server.
-   **`lib/mcp/auth.py`** -- `QuerybookTokenVerifier` validates `Authorization: Bearer <api-key>` headers by SHA-512 hashing the token and looking it up in the `api_access_token` table. The authenticated user's `creator_uid` is available in tool and resource functions via `CurrentAccessToken()`.
-   **`lib/mcp/utils.py`** -- Constants for tool/resource annotations (`READ_ONLY_ANNOTATIONS`, `WRITE_ANNOTATIONS`, `CREATE_ANNOTATIONS`, `DELETE_ANNOTATIONS`, `RESOURCE_ANNOTATIONS`).
-   **`lib/mcp/lib/`** -- Shared business logic for serialization, data retrieval, and permission checking used by both tools and resources.
-   **`lib/mcp/tools/`** -- Each file contains a `register(mcp)` function that defines one or more tools using `@mcp.tool`.
-   **`lib/mcp/resources/`** -- Each file contains a `register(mcp)` function that defines one or more resources using `@mcp.resource`.

## Authentication

All requests require a valid Querybook API key as a Bearer token. The `owner_uid` for operations is derived from the token -- callers never pass it directly. In tool functions, inject the token with:

```python
from fastmcp.server.auth import AccessToken
from fastmcp.server.dependencies import CurrentAccessToken

def my_tool(
    ...,
    token: AccessToken = CurrentAccessToken(),
) -> ...:
    uid = token.claims["creator_uid"]
```

## Adding a New Tool

1. Create a new file in `querybook/server/lib/mcp/tools/`, e.g. `my_tool.py`.

2. Define a `register(mcp)` function containing the tool:

```python
from typing import Annotated

from fastmcp import FastMCP
from fastmcp.server.auth import AccessToken
from fastmcp.server.dependencies import CurrentAccessToken

from app.db import DBSession
from lib.mcp.utils import READ_ONLY_ANNOTATIONS, WRITE_ANNOTATIONS, CREATE_ANNOTATIONS, DELETE_ANNOTATIONS


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        title="Human-Readable Title",
        annotations=READ_ONLY_ANNOTATIONS,  # or WRITE_ANNOTATIONS, CREATE_ANNOTATIONS, DELETE_ANNOTATIONS
    )
    def my_tool(
        param: Annotated[int, "Short parameter description."],
        token: AccessToken = CurrentAccessToken(),
    ) -> dict:
        """Concise description of what the tool does."""
        uid = token.claims["creator_uid"]
        with DBSession() as session:
            # ... implementation using logic/ functions ...
            pass
```

3. Register it in `run_mcp.py`:

```python
from lib.mcp.tools import my_tool

my_tool.register(mcp)
```

## Tool Metadata Conventions

-   **`title`**: Human-readable display name for the tool. Should be an action name only (e.g., "Update DataDoc Cell"), not include behavior descriptions.
-   **`annotations`**: MCP behavioral hints that clients use for safety decisions (e.g. auto-approving read-only tools). Use the constants from `lib.mcp.utils`:
    -   `READ_ONLY_ANNOTATIONS` - for read-only operations (idempotent, non-destructive)
    -   `WRITE_ANNOTATIONS` - for update operations (idempotent, non-destructive)
    -   `CREATE_ANNOTATIONS` - for create operations (non-idempotent, non-destructive)
    -   `DELETE_ANNOTATIONS` - for delete operations (idempotent, destructive)
-   **Parameter descriptions**: Use `Annotated[type, "short description"]` for concise descriptions. Avoid parentheses; use commas for clarity. Reference related tools without parentheses (e.g., "from list_lists or search_lists").
-   **Docstring**: Keep it to one or two sentences. This becomes the tool description in the MCP schema.
-   **Pydantic models**: Use for structured input parameters. Define models in the tool file above the `register()` function.

## Adding a New Resource

1. Create a new file in `querybook/server/lib/mcp/resources/`, e.g. `my_resource.py`.

2. Define a `register(mcp)` function containing the resource:

```python
from typing import Annotated

from fastmcp import FastMCP
from fastmcp.resources import ResourceContent
from fastmcp.server.auth import AccessToken
from fastmcp.server.dependencies import CurrentAccessToken

from app.db import DBSession
from lib.mcp.utils import RESOURCE_ANNOTATIONS


def register(mcp: FastMCP) -> None:
    @mcp.resource(
        uri="querybook://resource/{resource_id}",
        name="Human-Readable Name",
        description="What this resource contains",
        mime_type="application/json",
        annotations=RESOURCE_ANNOTATIONS,
    )
    def my_resource(
        resource_id: Annotated[int, "Resource identifier"],
        token: AccessToken = CurrentAccessToken(),
    ) -> list[ResourceContent]:
        """Concise description of the resource content."""
        uid = token.claims["creator_uid"]
        with DBSession() as session:
            # ... implementation using logic/ or lib/mcp/lib/ functions ...
            result = get_resource_data(resource_id, uid, session)
            return [ResourceContent(result)]
```

3. Register it in `run_mcp.py`:

```python
from lib.mcp.resources import my_resource

my_resource.register(mcp)
```

4. Update discovery tools to return `resource_uri` fields pointing to your resource.
