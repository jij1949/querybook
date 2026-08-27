"""MCP audit envelope construction and sink routing."""

from datetime import datetime, timezone

from env import QuerybookSettings
from lib.event_logger import event_logger
from lib.logger import get_logger
from lib.mcp.audit.anomaly import check_failure_burst
from lib.mcp.audit.context import get_request_context
from lib.mcp.audit.langsmith import emit_langsmith_run
from lib.stats_logger import (
    MCP_ANOMALY,
    MCP_AUTH_FAILURE,
    MCP_AUTHZ_DENY,
    MCP_RATE_LIMIT,
    MCP_REJECTED,
    MCP_TOOL_CALL,
    MCP_TOOL_ERROR,
    stats_logger,
)

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
            # Subject 0 means no authenticated user; store NULL so the
            # event_log.uid foreign key is satisfied.
            uid = None if subject == 0 else subject
            event_logger.log_mcp_event(uid=uid, event_data=envelope)

        is_routine_auth = event_type == "no_token"
        if (
            QuerybookSettings.LANGSMITH_TRACING
            and event_type not in _RICH_TRACE_EVENTS
            and not is_routine_auth
            and emit_langsmith
        ):
            emit_langsmith_run(event_type, envelope)

        try:
            _emit_metric(event_type, payload, ctx)
        except Exception as e:
            LOG.error(f"Failed to emit MCP audit metric: {e}", exc_info=True)

        # Per-credential failure-burst detection. The counter runs here so
        # every security signal funnels through one place; the resulting
        # `anomaly` event (if any) is emitted from the router, not the
        # detector, to avoid a back-import. The nested call re-enters this
        # function harmlessly -- `anomaly` is not itself a counted failure.
        anomaly = check_failure_burst(event_type, payload, ctx)
        if anomaly is not None:
            emit_audit_event("anomaly", anomaly, ctx)
    except Exception as e:
        LOG.error(f"Failed to emit MCP audit event: {e}", exc_info=True)


def _tags(**kwargs) -> dict:
    return {k: v for k, v in kwargs.items() if v is not None}


def _operation_tag(payload: dict) -> str:
    """Bounded operation dimension for a tool/resource event: the tool name,
    or the resource's registered URI template (never the resolved
    resource_uri, which carries an unbounded identifier)."""
    return payload.get("tool") or payload.get("resource_template")


def _emit_metric(event_type: str, payload: dict, ctx: dict) -> None:
    """Single source of truth for MCP audit -> Datadog counters.

    Call sites must not increment these counters themselves, or metrics
    will be double-counted.
    """
    environment = ctx.get("environment")
    status = payload.get("status")
    result = payload.get("result")

    if event_type in ("tool_invocation", "resource_read"):
        surface = "tool" if event_type == "tool_invocation" else "resource"
        tags = _tags(
            surface=surface, tool=_operation_tag(payload), environment=environment
        )
        stats_logger.incr(MCP_TOOL_CALL, tags=tags)
        if status == "error":
            stats_logger.incr(MCP_TOOL_ERROR, tags=tags)
    elif event_type == "auth" and result == "failure":
        stats_logger.incr(MCP_AUTH_FAILURE, tags=_tags(environment=environment))
    elif event_type == "authz":
        tags = _tags(tool=_operation_tag(payload), environment=environment)
        stats_logger.incr(MCP_AUTHZ_DENY, tags=tags)
    elif event_type == "rejected_invocation":
        reason = payload.get("reason")
        tags = _tags(reason=reason, environment=environment)
        stats_logger.incr(MCP_REJECTED, tags=tags)
        if reason == "rate_limited":
            stats_logger.incr(MCP_RATE_LIMIT, tags=_tags(environment=environment))
    elif event_type == "anomaly":
        tags = _tags(reason=payload.get("reason"), environment=environment)
        stats_logger.incr(MCP_ANOMALY, tags=tags)


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
