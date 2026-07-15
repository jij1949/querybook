"""MCP request-boundary authentication audit recording."""

import uuid
from contextvars import ContextVar

from env import QuerybookSettings
from lib.mcp.audit.context import _request_id_var
from lib.mcp.audit.router import emit_audit_event

# Request-scoped authentication outcome. Token verifiers and OAuth exchange
# methods record what happened here; the request-boundary middleware decides
# which standalone auth event, if any, should be emitted.
_auth_outcome_var: ContextVar = ContextVar("mcp_auth_outcome", default=None)


class RequestAuditMiddleware:
    """Pure-ASGI request boundary for correlation ids and auth event flushing."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        status = {}

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status["code"] = message["status"]
            await send(message)

        had_bearer = _request_has_bearer(scope)
        tok = _request_id_var.set(uuid.uuid4().hex)
        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            # Flush in finally so a recorded auth outcome (e.g. an invalid-token
            # failure during a /token exchange) is still emitted when the
            # downstream app raises, rather than being silently dropped.
            _flush_auth_event(status.get("code"), had_bearer)
            _auth_outcome_var.set(None)
            _request_id_var.reset(tok)


def record_auth_success(reason: str, auth_method: str) -> None:
    """Record a successful authentication that rides on the next tool event."""
    _auth_outcome_var.set(
        {
            "result": "success",
            "standalone": False,
            "auth_reason": reason,
            "auth_method": auth_method,
        }
    )


def record_auth_failure(reason: str, auth_method: str) -> None:
    """Record a genuinely invalid authentication for standalone emission."""
    _auth_outcome_var.set(
        {
            "result": "failure",
            "standalone": True,
            "auth_reason": reason,
            "auth_method": auth_method,
        }
    )


def record_token_issuance(
    reason: str,
    auth_method: str,
    success: bool,
    subject: int = 0,
    client_id: str = None,
    session_id: str = None,
) -> None:
    """Record an OAuth token issuance / refresh outcome for boundary emission."""
    _auth_outcome_var.set(
        {
            "result": "success" if success else "failure",
            "standalone": True,
            "auth_reason": reason,
            "auth_method": auth_method,
            "subject": subject,
            "client_id": client_id,
            "session_id": session_id,
        }
    )


def get_recorded_auth_reason():
    """Return the request's recorded auth_reason, if any."""
    outcome = _auth_outcome_var.get()
    return outcome.get("auth_reason") if outcome else None


def _request_has_bearer(scope) -> bool:
    """True if the ASGI request carried an Authorization: Bearer header."""
    for name, value in scope.get("headers", []):
        if name == b"authorization":
            return value[:7].lower() == b"bearer "
    return False


def _auth_event_context(
    subject: int = 0,
    auth_method: str = "unknown",
    client_id: str = None,
    session_id: str = None,
) -> dict:
    """Correlation context for standalone auth events."""
    return {
        "request_id": _request_id_var.get() or "unknown",
        "subject": subject,
        "client_id": client_id,
        "auth_method": auth_method,
        "session_id": session_id,
        "session_kind": "access_token" if session_id else None,
        "environment": QuerybookSettings.ENVIRONMENT,
    }


def _flush_auth_event(status_code, had_bearer: bool = False) -> None:
    """Emit any standalone auth event recorded for this request."""
    outcome = _auth_outcome_var.get()
    if outcome is not None:
        if not outcome.get("standalone"):
            return
        payload = {
            "result": outcome.get("result"),
            "auth_reason": outcome.get("auth_reason"),
        }
        emit_audit_event(
            "auth",
            payload,
            _auth_event_context(
                subject=outcome.get("subject", 0),
                auth_method=outcome.get("auth_method", "unknown"),
                client_id=outcome.get("client_id"),
                session_id=outcome.get("session_id"),
            ),
        )
    elif status_code == 401:
        if had_bearer:
            emit_audit_event(
                "auth",
                {
                    "result": "failure",
                    "auth_reason": "unclassified_token_rejection",
                },
                _auth_event_context(),
            )
        else:
            emit_audit_event(
                "no_token",
                {"result": "no_token"},
                _auth_event_context(),
            )
