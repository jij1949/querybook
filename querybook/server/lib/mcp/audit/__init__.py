"""Public MCP audit API."""

from lib.mcp.audit.auth import (
    RequestAuditMiddleware,
    _auth_outcome_var,
    get_recorded_auth_reason,
    record_auth_failure,
    record_auth_success,
    record_token_issuance,
)
from lib.mcp.audit.config_snapshot import build_config_snapshot, log_config_snapshot
from lib.mcp.audit.context import (
    _request_id_var,
    get_access_token_safe,
    get_request_context,
)
from lib.mcp.audit.router import LOG, emit_audit_event, log_mcp_event

__all__ = [
    "LOG",
    "RequestAuditMiddleware",
    "_auth_outcome_var",
    "_request_id_var",
    "build_config_snapshot",
    "emit_audit_event",
    "get_access_token_safe",
    "get_recorded_auth_reason",
    "get_request_context",
    "log_config_snapshot",
    "log_mcp_event",
    "record_auth_failure",
    "record_auth_success",
    "record_token_issuance",
]
