"""Query execution utility functions for MCP tools."""

from const.query_execution import QueryExecutionStatus, StatementExecutionStatus


def serialize_query_execution(execution) -> dict:
    """Serialize query execution model with human-readable status names and resource URIs.

    This function converts a QueryExecution model to a dictionary with human-readable
    status names and resource URIs, while removing internal implementation details.

    Adds:
    - status_name for QueryExecutionStatus (e.g., "DONE", "ERROR")
    - status_name for each StatementExecutionStatus
    - results_resource_uri for each statement execution

    Removes:
    - result_path (internal field)
    - log_path (internal field)

    Args:
        execution: QueryExecution model object

    Returns:
        Serialized execution dict with status_name fields, resource URIs,
        and internal fields removed
    """
    # Convert model to dict with statements
    execution_dict = execution.to_dict(with_statement=True)

    # Add query execution status name
    if "status" in execution_dict:
        try:
            status_enum = QueryExecutionStatus(execution_dict["status"])
            execution_dict["status_name"] = status_enum.name
        except (ValueError, KeyError):
            pass

    # Add statement execution status names and resource URIs
    if "statement_executions" in execution_dict:
        for stmt in execution_dict["statement_executions"]:
            if "status" in stmt:
                try:
                    status_enum = StatementExecutionStatus(stmt["status"])
                    stmt["status_name"] = status_enum.name
                except (ValueError, KeyError):
                    pass

            # Remove internal result_path and log_path fields
            stmt.pop("result_path", None)
            stmt.pop("log_path", None)

            # Add resource URI for results
            if "id" in stmt:
                stmt["results_resource_uri"] = (
                    f"querybook://statement-execution/{stmt['id']}/results"
                )

    return execution_dict
