from typing import Annotated

from fastmcp import FastMCP
from fastmcp.server.auth import AccessToken
from fastmcp.server.dependencies import CurrentAccessToken

from app.db import DBSession
from const.query_execution import QueryExecutionStatus, QueryExecutionType
from lib.mcp.lib.query_executions import serialize_query_execution
from lib.mcp.utils import CREATE_ANNOTATIONS
from logic import admin as admin_logic
from logic import query_execution as logic
from logic import datadoc as datadoc_logic
from logic.datadoc_permission import user_can_execute, DocDoesNotExist


def register(mcp: FastMCP) -> None:
    """Register query execution tools on the given MCP server."""

    @mcp.tool(
        title="Run DataDoc Cell",
        annotations=CREATE_ANNOTATIONS,
    )
    def run_datadoc_cell(
        cell_id: Annotated[int, "Cell ID from get_datadoc"],
        token: AccessToken = CurrentAccessToken(),
    ) -> dict:
        """Execute a query cell from a DataDoc. Returns the query execution ID."""
        uid = token.claims["creator_uid"]

        with DBSession() as session:
            # Get the cell and verify it's a query cell
            cell = datadoc_logic.get_data_cell_by_id(cell_id, session=session)
            if not cell:
                raise ValueError(f"Cell {cell_id} not found.")

            if cell.cell_type.name != "query":
                raise ValueError(
                    f"Cell {cell_id} is not a query cell (type: {cell.cell_type.name})."
                )

            # Check execute permission on the parent datadoc
            data_doc = cell.doc
            try:
                if not user_can_execute(data_doc.id, uid, session=session):
                    raise ValueError(
                        "You do not have permission to execute this DataDoc."
                    )
            except DocDoesNotExist:
                raise ValueError(f"DataDoc {data_doc.id} not found.")

            # Get engine_id from cell metadata
            engine_id = cell.meta.get("engine")
            if not engine_id:
                raise ValueError("Cell does not have an engine specified.")

            # Verify engine permission (matches REST API's verify_query_engine_permission)
            accessible_engine_ids = (
                admin_logic.get_all_accessible_query_engine_ids_by_uid(
                    uid, session=session
                )
            )
            if engine_id not in accessible_engine_ids:
                raise ValueError(f"You do not have access to query engine {engine_id}.")

            # Create and run the query execution
            query_execution = logic.create_query_execution(
                query=cell.context,
                engine_id=engine_id,
                uid=uid,
                status=QueryExecutionStatus.INITIALIZED,
                session=session,
            )

            # Associate with the data cell
            datadoc_logic.append_query_executions_to_data_cell(
                cell_id, [query_execution.id], session=session
            )

            # Initiate execution (this queues it for processing)
            from datasources.query_execution import initiate_query_execution

            initiate_query_execution(
                query_execution=query_execution,
                uid=uid,
                peer_review_params=None,
                session=session,
            )

            return serialize_query_execution(query_execution)

    @mcp.tool(
        title="Run DataDoc",
        annotations=CREATE_ANNOTATIONS,
    )
    def run_datadoc(
        datadoc_id: Annotated[int, "DataDoc ID"],
        start_index: Annotated[int, "Index of first cell to execute (0-based)"] = 0,
        token: AccessToken = CurrentAccessToken(),
    ) -> dict:
        """Execute all query cells in a DataDoc starting from start_index, runs asynchronously via Celery."""
        uid = token.claims["creator_uid"]

        with DBSession() as session:
            # Check execute permission
            try:
                if not user_can_execute(datadoc_id, uid, session=session):
                    raise ValueError(
                        "You do not have permission to execute this DataDoc."
                    )
            except DocDoesNotExist:
                raise ValueError(f"DataDoc {datadoc_id} not found.")

            # Send Celery task to run the datadoc
            from app.flask_app import celery

            celery.send_task(
                "tasks.run_datadoc.run_datadoc",
                args=[],
                kwargs={
                    "doc_id": datadoc_id,
                    "start_index": start_index,
                    "user_id": uid,
                    "execution_type": QueryExecutionType.ADHOC.value,
                    "notifications": [],
                },
            )

            return {
                "datadoc_id": datadoc_id,
                "datadoc_resource_uri": f"querybook://datadoc/{datadoc_id}",
                "start_index": start_index,
                "message": "DataDoc execution queued. Use get_datadoc_cell_executions to check progress.",
            }
