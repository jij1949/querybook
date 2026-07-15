"""Startup MCP security configuration snapshot audit event."""

import asyncio

from env import QuerybookSettings
from lib.logger import get_logger
from lib.mcp.audit.router import emit_audit_event

LOG = get_logger(__file__)

_SYSTEM_CONTEXT = {
    "request_id": "startup",
    "subject": 0,
    "client_id": None,
    "auth_method": "system",
    "session_id": None,
    "session_kind": None,
}


async def _list_surface(mcp) -> tuple[list, list]:
    """Return (sorted tool names, sorted resource URIs) from the FastMCP server."""
    tools = await mcp.list_tools(run_middleware=False)
    resources = await mcp.list_resources(run_middleware=False)
    return (
        sorted(t.name for t in tools),
        sorted(str(r.uri) for r in resources),
    )


def _enumerate_surface(mcp) -> tuple[list, list]:
    """Synchronously enumerate the tool/resource surface for the snapshot."""
    try:
        return asyncio.run(_list_surface(mcp))
    except Exception as e:
        LOG.error(f"Failed to enumerate MCP tool/resource surface: {e}", exc_info=True)
        return [], []


def build_config_snapshot(mcp) -> dict:
    """Build the security config snapshot payload without secret values."""
    tools, resources = _enumerate_surface(mcp)

    oauth_configured = bool(
        QuerybookSettings.OAUTH_CLIENT_ID
        and QuerybookSettings.OAUTH_CLIENT_SECRET
        and QuerybookSettings.MCP_AUTH_SECRET
        and QuerybookSettings.MCP_OAUTH_BASE_URL
    )
    oidc_configured = bool(QuerybookSettings.MCP_OIDC_CONFIG_URL)
    allowed_redirect_uri_count = len(
        QuerybookSettings.MCP_OAUTH_ALLOWED_REDIRECT_URIS or []
    )

    return {
        "auth_mode": QuerybookSettings.MCP_AUTH_MODE,
        "oauth_configured": oauth_configured,
        "oidc_configured": oidc_configured,
        "allowed_redirect_uri_count": allowed_redirect_uri_count,
        "rate_limit_enabled": False,
        "tools": tools,
        "resources": resources,
        "event_logger_name": QuerybookSettings.EVENT_LOGGER_NAME,
        "stats_logger_name": QuerybookSettings.STATS_LOGGER_NAME,
        "langsmith_tracing": QuerybookSettings.LANGSMITH_TRACING,
        "query_result_limits": {
            "db_max_upload_size": QuerybookSettings.DB_MAX_UPLOAD_SIZE,
            "store_max_read_size": QuerybookSettings.STORE_MAX_READ_SIZE,
            "table_max_upload_rows": QuerybookSettings.TABLE_MAX_UPLOAD_ROWS,
        },
    }


def log_config_snapshot(mcp) -> None:
    """Emit the startup security config snapshot."""
    snapshot = build_config_snapshot(mcp)
    emit_audit_event(
        "config_snapshot",
        snapshot,
        {**_SYSTEM_CONTEXT, "environment": QuerybookSettings.ENVIRONMENT},
    )
