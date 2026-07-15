"""MCP audit envelope construction and sink routing."""

from datetime import datetime, timezone

from env import QuerybookSettings
from lib.event_logger import event_logger
from lib.logger import get_logger
from lib.mcp.audit.context import get_request_context
from lib.mcp.audit.langsmith import emit_langsmith_run

LOG = get_logger(__file__)

_ALWAYS_LOG = {"authz", "rejected_invocation", "anomaly", "config_snapshot"}

# Tool/resource invocations carry their own rich LangSmith trace, opened around
# live execution in middleware.py. Every other non-execution event gets a
# lightweight, point-in-time run from this router instead.
_RICH_TRACE_EVENTS = {"tool_invocation", "resource_read"}


def emit_audit_event(
    event_type: str,
    payload: dict,
    ctx: dict,
    emit_langsmith: bool = True,
) -> None:
    """Build a structured audit envelope from ctx + payload and route it.

    EventLog receives the full envelope. LOG.info receives security signals.
    LangSmith receives a sink-specific projection of the same envelope.
    """
    try:
        subject = ctx.get("subject", 0)
        envelope = {
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **ctx,
            **payload,
        }

        result = payload.get("result")
        is_auth_signal = event_type == "auth" and result == "failure"
        if (
            event_type in _ALWAYS_LOG
            or payload.get("status") == "error"
            or is_auth_signal
        ):
            detail = " ".join(f"{k}={v}" for k, v in payload.items() if v is not None)
            LOG.info("MCP %s subject=%s %s", event_type, subject, detail)

        if QuerybookSettings.EVENT_LOGGER_NAME != "null":
            event_logger.log_mcp_event(uid=subject, event_data=envelope)

        is_routine_auth = event_type == "no_token"
        if (
            QuerybookSettings.LANGSMITH_TRACING
            and event_type not in _RICH_TRACE_EVENTS
            and not is_routine_auth
            and emit_langsmith
        ):
            emit_langsmith_run(event_type, envelope)
    except Exception as e:
        LOG.error(f"Failed to emit MCP audit event: {e}", exc_info=True)


def log_mcp_event(
    event_type: str,
    payload: dict,
    emit_langsmith: bool = True,
) -> None:
    """Emit a request-scoped audit event, deriving correlation from the request."""
    emit_audit_event(
        event_type,
        payload,
        get_request_context(),
        emit_langsmith=emit_langsmith,
    )
