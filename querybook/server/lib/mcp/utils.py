"""Shared utilities for MCP tools and resources."""

from env import QuerybookSettings


def build_querybook_url(environment_name: str, path: str) -> str | None:
    """Build a Querybook web UI URL.

    Args:
        environment_name: Environment name for the URL path
        path: Resource path, e.g. "datadoc/123" or "list/456"

    Returns:
        Full URL string, or None if PUBLIC_URL is not configured
    """
    if not QuerybookSettings.PUBLIC_URL:
        return None
    return f"{QuerybookSettings.PUBLIC_URL}/{environment_name}/{path}/"


# Annotation constants for MCP tools and resources
READ_ONLY_ANNOTATIONS = {
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": False,
    "readOnlyHint": True,
}

WRITE_ANNOTATIONS = {
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": False,
    "readOnlyHint": False,
}

CREATE_ANNOTATIONS = {
    "destructiveHint": False,
    "idempotentHint": False,
    "openWorldHint": False,
    "readOnlyHint": False,
}

DELETE_ANNOTATIONS = {
    "destructiveHint": True,
    "idempotentHint": True,
    "openWorldHint": False,
    "readOnlyHint": False,
}

RESOURCE_ANNOTATIONS = {
    "readOnlyHint": True,
    "idempotentHint": True,
}
