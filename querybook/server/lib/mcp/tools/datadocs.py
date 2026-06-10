from typing import Annotated, Literal

from fastmcp import FastMCP
from fastmcp.server.auth import AccessToken
from fastmcp.server.dependencies import CurrentAccessToken
from pydantic import BaseModel, Field

from app.db import DBSession
from lib.mcp.lib.datadocs import (
    serialize_datadoc,
    serialize_datadoc_cell,
    serialize_datadoc_editor,
    get_datadoc_data,
    validate_query_cell_engine,
    validate_query_cells_engines,
)
from lib.mcp.utils import (
    READ_ONLY_ANNOTATIONS,
    WRITE_ANNOTATIONS,
    CREATE_ANNOTATIONS,
    DELETE_ANNOTATIONS,
    build_querybook_url,
)
from logic.datadoc import (
    create_data_doc,
    get_data_doc_by_id,
    update_data_doc,
    favorite_data_doc,
    unfavorite_data_doc,
    create_data_cell,
    get_data_cell_by_id,
    insert_data_doc_cell,
    update_data_cell,
    delete_data_doc_cell,
    create_data_doc_editor,
    get_data_doc_editor_by_id,
    update_data_doc_editor,
    delete_data_doc_editor,
)
from logic.datadoc_permission import (
    DocDoesNotExist,
    user_can_read,
    user_can_write,
)
from models.datadoc import DataDocDataCell
from models.environment import Environment


class DataDocCell(BaseModel):
    cell_type: str = Field(
        description=(
            "Cell type: query, text, chart, or python. See "
            "querybook://reference/chart-cells for chart cells and "
            "querybook://reference/rich-text for text cells."
        )
    )
    context: str = Field(
        default="",
        description=(
            "Cell SQL, code, or HTML rich text. Text cells use HTML fragments; "
            "see querybook://reference/rich-text. Chart cells use an empty "
            "context string."
        ),
    )
    meta: dict = Field(
        default_factory=dict,
        description=(
            "Additional cell metadata. Chart cell schema is documented at "
            "querybook://reference/chart-cells."
        ),
    )


class DataDocData(BaseModel):
    cells: list[DataDocCell] = Field(default_factory=list)
    environment_id: int | None = None
    meta: dict | None = None
    public: bool | None = None
    title: str | None = None


class DataDocInput(BaseModel):
    data: DataDocData


VALID_VARIABLE_TYPES = {"string", "number", "boolean"}
VARIABLE_TYPE_CHECKS = {
    "string": lambda v: isinstance(v, str),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
}


def validate_variables(variables: list[dict]) -> None:
    """Validate template variables before passing to the data layer."""
    seen_names = set()
    for i, var in enumerate(variables):
        name = var.get("name")
        var_type = var.get("type")

        if not name or not name.strip():
            raise ValueError(f"Variable at index {i} has an empty or missing name.")

        if var_type not in VALID_VARIABLE_TYPES:
            raise ValueError(
                f"Variable '{name}' has invalid type '{var_type}'. "
                f"Must be one of: {', '.join(sorted(VALID_VARIABLE_TYPES))}."
            )

        if not VARIABLE_TYPE_CHECKS[var_type](var.get("value")):
            raise ValueError(
                f"Variable '{name}' has type '{var_type}' but value is not a {var_type}."
            )

        if name in seen_names:
            raise ValueError(f"Duplicate variable name '{name}'.")
        seen_names.add(name)


def register(mcp: FastMCP) -> None:
    """Register datadoc tools on the given MCP server."""

    @mcp.tool(
        title="Get DataDoc",
        annotations=READ_ONLY_ANNOTATIONS,
    )
    def get_datadoc(
        datadoc_id: Annotated[int, "DataDoc ID"],
        token: AccessToken = CurrentAccessToken(),
    ) -> dict:
        """Get a single DataDoc with its cells and editors by ID."""
        uid = token.claims["creator_uid"]
        with DBSession() as session:
            return get_datadoc_data(datadoc_id, uid, session)

    @mcp.tool(
        title="List DataDocs",
        annotations=READ_ONLY_ANNOTATIONS,
    )
    def list_datadocs(
        environment_id: Annotated[int, "Environment ID from list_environments"],
        scope: Annotated[
            Literal["mine", "favorite", "recent"],
            "Scope: 'mine' (owned by you), 'favorite' (favorited by you), 'recent' (recently viewed by you)",
        ] = "mine",
        offset: Annotated[int, "Pagination offset"] = 0,
        limit: Annotated[int, "Maximum number of results"] = 100,
        token: AccessToken = CurrentAccessToken(),
    ) -> list[dict]:
        """List DataDocs in the given environment, filtered by scope."""
        uid = token.claims["creator_uid"]
        with DBSession() as session:
            docs = []

            if scope == "mine":
                from logic.datadoc import get_data_doc_by_user

                docs = get_data_doc_by_user(
                    uid,
                    environment_id=environment_id,
                    offset=offset,
                    limit=limit,
                    session=session,
                )
            elif scope == "favorite":
                from logic.datadoc import get_user_favorite_data_docs

                all_docs = get_user_favorite_data_docs(
                    uid, environment_id=environment_id, session=session
                )
                docs = all_docs[offset : offset + limit]
            elif scope == "recent":
                from logic.datadoc import get_user_recent_data_docs

                all_docs = get_user_recent_data_docs(
                    uid, environment_id=environment_id, session=session
                )
                docs = all_docs[offset : offset + limit]

            return [serialize_datadoc(doc, session, uid=uid) for doc in docs]

    @mcp.tool(
        title="Search DataDocs",
        annotations=READ_ONLY_ANNOTATIONS,
    )
    def search_datadocs(
        environment_id: Annotated[int, "Environment ID from list_environments"],
        keywords: Annotated[str, "Search keywords"],
        filters: Annotated[
            list[list] | None, "Filters as list of [field, value] pairs"
        ] = None,
        limit: Annotated[int, "Maximum number of results"] = 100,
        offset: Annotated[int, "Pagination offset"] = 0,
        token: AccessToken = CurrentAccessToken(),
    ) -> dict:
        """Search DataDocs using keywords and filters."""
        if limit > 100:
            raise ValueError("Limit cannot exceed 100")

        uid = token.claims["creator_uid"]

        from lib.elasticsearch.search_datadoc import construct_datadoc_query
        from lib.elasticsearch.search_utils import get_matching_objects, ES_CONFIG

        with DBSession() as session:
            # Add environment filter
            filters_with_env = (filters or []) + [["environment_id", environment_id]]

            query = construct_datadoc_query(
                uid=uid,
                keywords=keywords.strip(),
                filters=filters_with_env,
                fields=[],
                limit=limit,
                offset=offset,
                sort_key=None,
                sort_order=None,
            )

            results, count = get_matching_objects(
                query, ES_CONFIG["datadocs"]["index_name"], True
            )

            # Add resource URIs and URLs to search results
            environment = session.query(Environment).get(environment_id)
            for result in results:
                doc_id = result.get("_source", {}).get("id") or result.get("id")
                if doc_id:
                    result["resource_uri"] = f"querybook://datadoc/{doc_id}"
                    if environment:
                        url = build_querybook_url(environment.name, f"datadoc/{doc_id}")
                        if url:
                            result["url"] = url

            return {"count": count, "results": results}

    @mcp.tool(
        title="Create DataDoc",
        annotations=CREATE_ANNOTATIONS,
    )
    def create_datadoc(
        environment_id: Annotated[int, "Environment ID from list_environments"],
        title: Annotated[str, "DataDoc title"] = "Untitled",
        public: Annotated[bool, "Whether the DataDoc is public"] = False,
        favorite: Annotated[
            bool, "Whether to favorite this DataDoc immediately"
        ] = False,
        variables: Annotated[
            list[dict] | None,
            "Template variables as list of {name, type, value} objects. "
            "type must be 'string', 'number', or 'boolean'. "
            "value must match the declared type.",
        ] = None,
        token: AccessToken = CurrentAccessToken(),
    ) -> dict:
        """Create a new empty DataDoc."""
        owner_uid = token.claims["creator_uid"]
        if variables is not None:
            validate_variables(variables)
        meta = {"variables": variables} if variables else {}

        with DBSession() as session:
            data_doc = create_data_doc(
                environment_id=environment_id,
                owner_uid=owner_uid,
                cells=[],
                title=title,
                meta=meta,
                public=public,
                archived=False,
                session=session,
            )

            # Favorite if requested
            if favorite:
                favorite_data_doc(
                    data_doc_id=data_doc.id, uid=owner_uid, session=session
                )

            return serialize_datadoc(data_doc, session, uid=owner_uid, with_cells=True)

    @mcp.tool(
        title="Update DataDoc",
        annotations=WRITE_ANNOTATIONS,
    )
    def update_datadoc(
        datadoc_id: Annotated[int, "DataDoc ID"],
        title: Annotated[str | None, "New title for the DataDoc"] = None,
        public: Annotated[bool | None, "Whether the DataDoc is public"] = None,
        archived: Annotated[bool | None, "Whether the DataDoc is archived"] = None,
        environment_id: Annotated[int | None, "Move to different environment"] = None,
        favorite: Annotated[
            bool | None, "Favorite (true) or unfavorite (false) this DataDoc"
        ] = None,
        variables: Annotated[
            list[dict] | None,
            "Template variables as list of {name, type, value} objects. "
            "type must be 'string', 'number', or 'boolean'. "
            "value must match the declared type. Replaces all existing variables.",
        ] = None,
        token: AccessToken = CurrentAccessToken(),
    ) -> dict:
        """Update DataDoc properties. Only non-null fields are updated."""
        if variables is not None:
            validate_variables(variables)
        uid = token.claims["creator_uid"]
        with DBSession() as session:
            try:
                if not user_can_write(datadoc_id, uid, session=session):
                    raise ValueError("You do not have permission to edit this DataDoc.")
            except DocDoesNotExist:
                raise ValueError(f"DataDoc {datadoc_id} not found.")

            # Build fields dict with only non-null values
            fields = {}
            if title is not None:
                fields["title"] = title
            if public is not None:
                fields["public"] = public
            if archived is not None:
                fields["archived"] = archived
            if environment_id is not None:
                fields["environment_id"] = environment_id
            if variables is not None:
                fields["meta"] = {"variables": variables}

            update_data_doc(id=datadoc_id, commit=True, session=session, **fields)

            # Update favorite status if specified
            if favorite is not None:
                if favorite:
                    favorite_data_doc(data_doc_id=datadoc_id, uid=uid, session=session)
                else:
                    unfavorite_data_doc(
                        data_doc_id=datadoc_id, uid=uid, session=session
                    )

            # Return updated doc
            doc = get_data_doc_by_id(datadoc_id, session=session)
            return serialize_datadoc(doc, session, uid=uid, with_cells=True)

    @mcp.tool(
        title="Delete DataDoc",
        annotations=DELETE_ANNOTATIONS,
    )
    def delete_datadoc(
        datadoc_id: Annotated[int, "DataDoc ID"],
        token: AccessToken = CurrentAccessToken(),
    ) -> dict:
        """Delete (archive) a DataDoc. This is a soft delete - the DataDoc is archived, not permanently deleted."""
        uid = token.claims["creator_uid"]
        with DBSession() as session:
            try:
                if not user_can_write(datadoc_id, uid, session=session):
                    raise ValueError(
                        "You do not have permission to delete this DataDoc."
                    )
            except DocDoesNotExist:
                raise ValueError(f"DataDoc {datadoc_id} not found.")

            update_data_doc(id=datadoc_id, archived=True, commit=True, session=session)
            return {"deleted": datadoc_id, "archived": True}

    @mcp.tool(
        title="Add DataDoc Cell",
        annotations=CREATE_ANNOTATIONS,
    )
    def add_datadoc_cell(
        datadoc_id: Annotated[int, "DataDoc ID"],
        cell_type: Annotated[
            Literal["query", "text", "chart", "python"],
            "Type of cell: 'query', 'text', 'chart', or 'python'. "
            "For chart cells, see querybook://reference/chart-cells. "
            "For text cells, see querybook://reference/rich-text.",
        ],
        context: Annotated[
            str,
            "Cell SQL, code, or rich text content. Text cells expect HTML "
            "fragments; see querybook://reference/rich-text. Chart cells "
            "should use an empty context string.",
        ] = "",
        title: Annotated[str | None, "Cell title"] = None,
        engine_id: Annotated[
            int | None,
            "Query engine ID from list_query_engines (required for query cells)",
        ] = None,
        meta: Annotated[
            dict | None,
            "Additional cell metadata. Chart cells require a chart/data schema; "
            "see querybook://reference/chart-cells.",
        ] = None,
        index: Annotated[int | None, "Position to insert cell (default: end)"] = None,
        token: AccessToken = CurrentAccessToken(),
    ) -> dict:
        """Add a cell to a DataDoc."""
        uid = token.claims["creator_uid"]

        with DBSession() as session:
            try:
                if not user_can_write(datadoc_id, uid, session=session):
                    raise ValueError("You do not have permission to edit this DataDoc.")
            except DocDoesNotExist:
                raise ValueError(f"DataDoc {datadoc_id} not found.")

            doc = get_data_doc_by_id(datadoc_id, session=session)
            if index is None:
                index = len(doc.cells)

            # Build meta dict with top-level fields
            cell_meta = {**(meta or {})}
            if title is not None:
                cell_meta["title"] = title
            if engine_id is not None:
                cell_meta["engine"] = engine_id

            validate_query_cell_engine(
                cell_type,
                cell_meta,
                uid,
                session,
                doc.environment_id,
            )

            data_cell = create_data_cell(
                cell_type=cell_type,
                context=context,
                meta=cell_meta,
                commit=False,
                session=session,
            )

            insert_data_doc_cell(
                data_doc_id=datadoc_id,
                cell_id=data_cell.id,
                index=index,
                commit=True,
                session=session,
            )

            return serialize_datadoc_cell(
                data_cell.to_dict(), session, datadoc_id=datadoc_id
            )

    @mcp.tool(
        title="Update DataDoc Cell",
        annotations=WRITE_ANNOTATIONS,
    )
    def update_datadoc_cell(
        cell_id: Annotated[int, "Cell ID not the cell's index"],
        context: Annotated[
            str | None,
            "Cell content/code. Text cells expect HTML fragments; see "
            "querybook://reference/rich-text. Chart cells should use an empty "
            "context string.",
        ] = None,
        title: Annotated[str | None, "Cell title"] = None,
        engine_id: Annotated[
            int | None, "Query engine ID from list_query_engines (for query cells)"
        ] = None,
        meta: Annotated[
            dict | None,
            "Additional cell metadata. Chart cells require a chart/data schema; "
            "see querybook://reference/chart-cells.",
        ] = None,
        token: AccessToken = CurrentAccessToken(),
    ) -> dict:
        """Update a DataDoc cell's context or metadata. Only updates non-null fields."""
        uid = token.claims["creator_uid"]

        with DBSession() as session:
            # Load the cell first to validate it exists
            cell = get_data_cell_by_id(cell_id, session=session)
            if not cell:
                raise ValueError(f"DataDoc cell {cell_id} not found.")

            # Get datadoc_id from cell's data_doc_cells relationship
            doc_cell = (
                session.query(DataDocDataCell)
                .filter(DataDocDataCell.data_cell_id == cell_id)
                .first()
            )
            if not doc_cell:
                raise ValueError(
                    f"DataDoc cell {cell_id} is not associated with a DataDoc."
                )
            datadoc_id = doc_cell.data_doc_id

            # Check permission against the actual parent DataDoc
            try:
                if not user_can_write(datadoc_id, uid, session=session):
                    raise ValueError("You do not have permission to edit this DataDoc.")
            except DocDoesNotExist:
                raise ValueError(f"DataDoc {datadoc_id} not found.")

            fields = {}
            if context is not None:
                fields["context"] = context

            # Build updated meta if any top-level fields or meta provided
            if title is not None or engine_id is not None or meta is not None:
                # Merge with existing meta
                cell_meta = {**(cell.meta or {})}

                # Merge provided meta
                if meta is not None:
                    cell_meta.update(meta)

                # Override with top-level fields
                if title is not None:
                    cell_meta["title"] = title
                if engine_id is not None:
                    cell_meta["engine"] = engine_id

                doc = get_data_doc_by_id(datadoc_id, session=session)
                validate_query_cell_engine(
                    cell.cell_type.name,
                    cell_meta,
                    uid,
                    session,
                    doc.environment_id,
                    cell_id=cell_id,
                )

                fields["meta"] = cell_meta

            update_data_cell(cell_id, session=session, **fields)

            session.refresh(cell)
            return serialize_datadoc_cell(
                cell.to_dict(),
                session,
                with_latest_execution=True,
                datadoc_id=datadoc_id,
            )

    @mcp.tool(
        title="Delete DataDoc Cell",
        annotations=DELETE_ANNOTATIONS,
    )
    def delete_datadoc_cell(
        cell_id: Annotated[int, "Cell ID not the cell's index"],
        token: AccessToken = CurrentAccessToken(),
    ) -> dict:
        """Delete a cell from a DataDoc."""
        uid = token.claims["creator_uid"]

        with DBSession() as session:
            # Load the cell first to validate it exists
            cell = get_data_cell_by_id(cell_id, session=session)
            if not cell:
                raise ValueError(f"DataDoc cell {cell_id} not found.")

            # Get datadoc_id from cell's data_doc_cells relationship
            doc_cell = (
                session.query(DataDocDataCell)
                .filter(DataDocDataCell.data_cell_id == cell_id)
                .first()
            )
            if not doc_cell:
                raise ValueError(
                    f"DataDoc cell {cell_id} is not associated with a DataDoc."
                )
            datadoc_id = doc_cell.data_doc_id

            # Check permission against the actual parent DataDoc
            try:
                if not user_can_write(datadoc_id, uid, session=session):
                    raise ValueError("You do not have permission to edit this DataDoc.")
            except DocDoesNotExist:
                raise ValueError(f"DataDoc {datadoc_id} not found.")

            delete_data_doc_cell(
                data_doc_id=datadoc_id, data_cell_id=cell_id, session=session
            )

            return {
                "deleted": cell_id,
                "datadoc_id": datadoc_id,
                "datadoc_resource_uri": f"querybook://datadoc/{datadoc_id}",
            }

    @mcp.tool(
        title="Add DataDoc Editor",
        annotations=WRITE_ANNOTATIONS,
    )
    def add_datadoc_editor(
        datadoc_id: Annotated[int, "DataDoc ID"],
        user_id: Annotated[int, "User ID to add as editor, from search_users"],
        read: Annotated[bool, "Grant read permission"] = False,
        write: Annotated[bool, "Grant write permission"] = False,
        execute: Annotated[bool, "Grant execute permission"] = False,
        token: AccessToken = CurrentAccessToken(),
    ) -> dict:
        """Add an editor to a DataDoc with specified permissions."""
        caller_uid = token.claims["creator_uid"]

        with DBSession() as session:
            try:
                if not user_can_write(datadoc_id, caller_uid, session=session):
                    raise ValueError("You do not have permission to edit this DataDoc.")
            except DocDoesNotExist:
                raise ValueError(f"DataDoc {datadoc_id} not found.")

            editor = create_data_doc_editor(
                data_doc_id=datadoc_id,
                uid=user_id,
                read=read,
                write=write,
                execute=execute,
                session=session,
            )

            return serialize_datadoc_editor(editor)

    @mcp.tool(
        title="Update DataDoc Editor",
        annotations=WRITE_ANNOTATIONS,
    )
    def update_datadoc_editor(
        editor_id: Annotated[int, "Editor ID not the user_id"],
        read: Annotated[bool | None, "New read permission (null = no change)"] = None,
        write: Annotated[bool | None, "New write permission (null = no change)"] = None,
        execute: Annotated[
            bool | None, "New execute permission (null = no change)"
        ] = None,
        token: AccessToken = CurrentAccessToken(),
    ) -> dict:
        """Update permissions for an editor on a DataDoc."""
        uid = token.claims["creator_uid"]

        with DBSession() as session:
            editor = get_data_doc_editor_by_id(editor_id, session=session)
            if not editor:
                raise ValueError(f"Editor {editor_id} not found.")

            try:
                if not user_can_write(editor.data_doc_id, uid, session=session):
                    raise ValueError("You do not have permission to edit this DataDoc.")
            except DocDoesNotExist:
                raise ValueError(f"DataDoc {editor.data_doc_id} not found.")

            updated_editor = update_data_doc_editor(
                id=editor_id,
                read=read,
                write=write,
                execute=execute,
                session=session,
            )

            return serialize_datadoc_editor(updated_editor) if updated_editor else {}

    @mcp.tool(
        title="Remove DataDoc Editor",
        annotations=DELETE_ANNOTATIONS,
    )
    def remove_datadoc_editor(
        editor_id: Annotated[int, "Editor ID not the user_id"],
        token: AccessToken = CurrentAccessToken(),
    ) -> dict:
        """Remove an editor from a DataDoc."""
        uid = token.claims["creator_uid"]

        with DBSession() as session:
            editor = get_data_doc_editor_by_id(editor_id, session=session)
            if not editor:
                raise ValueError(f"Editor {editor_id} not found.")

            doc_id = editor.data_doc_id

            try:
                if not user_can_write(doc_id, uid, session=session):
                    raise ValueError("You do not have permission to edit this DataDoc.")
            except DocDoesNotExist:
                raise ValueError(f"DataDoc {doc_id} not found.")

            delete_data_doc_editor(
                id=editor_id,
                doc_id=doc_id,
                session=session,
            )

            return {"removed": editor_id}

    @mcp.tool(
        title="Export DataDoc",
        annotations=READ_ONLY_ANNOTATIONS,
    )
    def export_datadoc(
        datadoc_id: Annotated[int, "DataDoc ID"],
        token: AccessToken = CurrentAccessToken(),
    ) -> dict:
        """Export a DataDoc in portable format without IDs. Suitable for upload_datadoc or UI upload."""
        uid = token.claims["creator_uid"]
        with DBSession() as session:
            try:
                if not user_can_read(datadoc_id, uid, session=session):
                    raise ValueError("You do not have access to this DataDoc.")
            except DocDoesNotExist:
                raise ValueError(f"DataDoc {datadoc_id} not found.")

            doc = get_data_doc_by_id(id=datadoc_id, session=session)

            # Convert to export format (matches upload_datadoc input)
            return {
                "data": {
                    "environment_id": doc.environment_id,
                    "title": doc.title,
                    "public": doc.public,
                    "meta": doc.meta,
                    "cells": [
                        {
                            "cell_type": cell.cell_type.name,
                            "context": cell.context,
                            "meta": cell.meta,
                        }
                        for cell in doc.cells
                    ],
                }
            }

    @mcp.tool(
        title="Upload DataDoc",
        annotations=CREATE_ANNOTATIONS,
    )
    def upload_datadoc(
        datadoc: Annotated[
            DataDocInput,
            "DataDoc in Querybook export format, use export_datadoc to generate. "
            "For text/chart cell formats, see querybook://reference/rich-text "
            "and querybook://reference/chart-cells.",
        ],
        environment_id: Annotated[
            int | None,
            "Target environment ID from list_environments (overrides datadoc.environment_id if provided)",
        ] = None,
        token: AccessToken = CurrentAccessToken(),
    ) -> dict:
        """Import/upload a DataDoc from export format."""
        owner_uid = token.claims["creator_uid"]

        doc = datadoc.data
        cells = [cell.model_dump() for cell in doc.cells]
        environment_id = environment_id or doc.environment_id
        # Default to an empty dict; DataDoc.meta's setter rejects None
        meta = doc.meta or {}
        public = doc.public
        title = doc.title

        # Validation
        if environment_id is None:
            raise ValueError(
                "environment_id is required either as a parameter or in the datadoc meta"
            )
        if not cells:
            raise ValueError("At least one cell is required in the datadoc")
        if any(not cell.get("cell_type") for cell in cells):
            raise ValueError("Each cell must have a cell_type")

        with DBSession() as session:
            validate_query_cells_engines(cells, owner_uid, environment_id, session)

            data_doc = create_data_doc(
                environment_id=environment_id,
                owner_uid=owner_uid,
                cells=cells,
                title=title,
                meta=meta,
                public=public,
                session=session,
            )

            return serialize_datadoc(data_doc, session, uid=owner_uid, with_cells=True)
