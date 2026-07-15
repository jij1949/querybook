"""LangSmith sink adapter for MCP audit events."""

import langsmith

from lib.logger import get_logger

LOG = get_logger(__file__)


def emit_langsmith_run(event_type: str, envelope: dict) -> None:
    """Emit a lightweight, point-in-time LangSmith run for a non-execution event.

    Tool/resource invocations get a rich trace wrapping live execution in
    middleware.py; everything else has no execution to wrap, so it gets one
    metadata-only run here. Fail-soft: a LangSmith hiccup must never break the
    audited operation or the other sinks.
    """
    try:
        with langsmith.trace(
            name=_event_name(event_type, envelope),
            run_type="chain",
            inputs={},
            metadata=_metadata(envelope),
            tags=["mcp", "querybook", event_type],
        ) as run:
            run.end(outputs=_outputs(envelope))
    except Exception as e:
        LOG.error(f"Failed to emit MCP LangSmith run: {e}", exc_info=True)


def _event_name(event_type: str, envelope: dict) -> str:
    """Return a compact, typed LangSmith run name for non-execution events."""
    if event_type == "auth":
        reason = envelope.get("auth_reason") or envelope.get("result") or "event"
        return f"mcp.auth.{reason}"
    if event_type == "authz":
        return f"mcp.authz.{envelope.get('result') or 'event'}"
    if event_type == "config_snapshot":
        return "mcp.config_snapshot"
    return f"mcp.{event_type}"


def _metadata(envelope: dict) -> dict:
    """Return filterable LangSmith metadata for a synthetic audit run."""
    metadata = {
        "operation_type": "audit",
        "event_type": envelope.get("event_type"),
        "timestamp": envelope.get("timestamp"),
        "request_id": envelope.get("request_id"),
        "subject": envelope.get("subject"),
        "client_id": envelope.get("client_id"),
        "auth_method": envelope.get("auth_method"),
        "session_id": envelope.get("session_id"),
        "session_kind": envelope.get("session_kind"),
        "environment": envelope.get("environment"),
    }

    event_type = envelope.get("event_type")
    if event_type == "auth":
        metadata.update(
            result=envelope.get("result"),
            auth_reason=envelope.get("auth_reason"),
        )
    elif event_type == "config_snapshot":
        metadata.update(
            auth_mode=envelope.get("auth_mode"),
            oauth_configured=envelope.get("oauth_configured"),
            oidc_configured=envelope.get("oidc_configured"),
            allowed_redirect_uri_count=envelope.get("allowed_redirect_uri_count"),
            rate_limit_enabled=envelope.get("rate_limit_enabled"),
            event_logger_name=envelope.get("event_logger_name"),
            stats_logger_name=envelope.get("stats_logger_name"),
            langsmith_tracing=envelope.get("langsmith_tracing"),
            tool_count=len(envelope.get("tools") or []),
            resource_count=len(envelope.get("resources") or []),
        )

    return metadata


def _outputs(envelope: dict) -> dict:
    """Return the non-filter payload shown on the synthetic LangSmith run."""
    if envelope.get("event_type") == "auth":
        return {
            "result": envelope.get("result"),
            "auth_reason": envelope.get("auth_reason"),
        }

    return {
        key: value
        for key, value in envelope.items()
        if key
        not in {
            "event_type",
            "timestamp",
            "request_id",
            "subject",
            "client_id",
            "auth_method",
            "session_id",
            "session_kind",
            "environment",
        }
    }
