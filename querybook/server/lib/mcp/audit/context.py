"""Request-scoped audit context helpers."""

import hashlib
from contextvars import ContextVar

from fastmcp.server.dependencies import get_access_token

from env import QuerybookSettings
from lib.logger import get_logger

LOG = get_logger(__file__)

_request_id_var: ContextVar = ContextVar("mcp_request_id", default=None)


def get_access_token_safe():
    """Return the current request's access token, or None on any error."""
    try:
        return get_access_token()
    except Exception as e:
        LOG.warning(f"Failed to extract access token from MCP context: {e}")
    return None


def get_request_context() -> dict:
    """Return the correlation fields shared by every audit sink."""
    token = get_access_token_safe()
    claims = token.claims if token else {}
    session_id = claims.get("session_id") or (
        hashlib.sha256(token.token.encode()).hexdigest()
        if token and getattr(token, "token", None)
        else None
    )
    return {
        "request_id": _request_id_var.get() or "unknown",
        "subject": claims.get("creator_uid", 0),
        "client_id": claims.get("client_id"),
        "auth_method": claims.get("auth_method", "unknown"),
        "session_id": session_id,
        "session_kind": "access_token" if session_id else None,
        "environment": QuerybookSettings.ENVIRONMENT,
    }
