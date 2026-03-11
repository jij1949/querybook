"""Query engine utility functions for MCP tools."""

from logic import admin as admin_logic


def serialize_query_engine(engine, with_environments: bool = False) -> dict:
    """Serialize query engine model with resource_uri.

    Args:
        engine: QueryEngine model object
        with_environments: If True, include list of environments with resource URIs

    Returns:
        Dict with all query engine fields and resource_uri
    """
    engine_dict = engine.to_dict()
    engine_dict["resource_uri"] = f"querybook://query-engine/{engine.id}"

    if with_environments and hasattr(engine, "environments"):
        # Late import to avoid circular dependency with environments.py
        from lib.mcp.lib.environments import serialize_environment

        engine_dict["environments"] = [
            serialize_environment(env) for env in engine.environments
        ]

    return engine_dict


def get_query_engine_data(engine_id: int, uid: int, session) -> dict:
    """Get query engine data with permission checking.

    Args:
        engine_id: Query engine ID
        uid: User ID for permission checking
        session: Database session

    Returns:
        Serialized query engine dict

    Raises:
        ValueError: If engine not found or user lacks permission
    """
    engine = admin_logic.get_query_engine_by_id(engine_id, session=session)
    if not engine:
        raise ValueError(f"Query engine {engine_id} not found.")

    # Check if user has access to this engine
    accessible_engine_ids = admin_logic.get_all_accessible_query_engine_ids_by_uid(
        uid, session=session
    )
    if engine.id not in accessible_engine_ids:
        raise ValueError("You do not have access to this query engine.")

    return serialize_query_engine(engine, with_environments=True)
