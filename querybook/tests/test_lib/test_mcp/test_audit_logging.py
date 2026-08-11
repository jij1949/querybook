"""Tests for MCP audit logging: envelope structure, log routing,
and the RequestIdMiddleware."""

import asyncio
import hashlib
import json
import logging
from unittest.mock import MagicMock

import pytest

from fastmcp.exceptions import ToolError

from env import QuerybookSettings
from lib.mcp.audit import context as audit_context
from lib.mcp.audit import langsmith as audit_langsmith
from lib.mcp.audit import router as audit_router
from lib.mcp.audit import (
    LOG,
    RequestAuditMiddleware,
    _auth_outcome_var,
    _request_id_var,
    build_config_snapshot,
    get_recorded_auth_reason,
    log_config_snapshot,
    log_mcp_event,
    record_auth_failure,
    record_auth_success,
    record_token_issuance,
)
from lib.mcp.exceptions import AuthorizationError
from lib.mcp.middleware import (
    MCPEventLoggingMiddleware,
    PayloadSizeGuardMiddleware,
    _freetext_bytes_over_limit,
    wrap_mcp_resources,
)

ENVELOPE_KEYS = {
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


class _FakeToken:
    token = "raw-bearer-value"
    claims = {"creator_uid": 42, "client_id": "claude", "auth_method": "oauth"}


class _EventLogCapture:
    def __init__(self):
        self.calls = []

    def log_mcp_event(self, uid, event_data):
        self.calls.append({"uid": uid, "event_data": event_data})


@pytest.fixture(autouse=True)
def _patch_env(monkeypatch):
    monkeypatch.setattr(QuerybookSettings, "EVENT_LOGGER_NAME", "db", raising=False)
    monkeypatch.setattr(QuerybookSettings, "ENVIRONMENT", "test", raising=False)


@pytest.fixture(autouse=True)
def _enable_audit_log_propagation():
    # get_logger() sets propagate=False to avoid duplicate lines under Celery's
    # root-logger hijack. pytest's caplog captures via the root logger, so
    # re-enable propagation for this module's logger during these tests.
    original = LOG.propagate
    LOG.propagate = True
    yield
    LOG.propagate = original


@pytest.fixture
def fake_logger(monkeypatch):
    capture = _EventLogCapture()
    monkeypatch.setattr(audit_router, "event_logger", capture)
    return capture


class _StatsCapture:
    def __init__(self):
        self.calls = []

    def incr(self, key, tags=None):
        self.calls.append((key, tags))


@pytest.fixture
def fake_stats(monkeypatch):
    capture = _StatsCapture()
    monkeypatch.setattr(audit_router, "stats_logger", capture)
    return capture


class _LangSmithCapture:
    """Records langsmith.trace() calls and the outputs handed to run.end()."""

    def __init__(self):
        self.runs = []

    def trace(self, **kwargs):
        record = {"kwargs": kwargs, "outputs": None}
        self.runs.append(record)

        class _Run:
            def end(_self, outputs=None):
                record["outputs"] = outputs

        class _CM:
            def __enter__(_self):
                return _Run()

            def __exit__(_self, *exc):
                return False

        return _CM()


@pytest.fixture
def fake_langsmith(monkeypatch):
    """Capture LangSmith runs with tracing enabled."""
    capture = _LangSmithCapture()
    monkeypatch.setattr(audit_langsmith, "langsmith", capture)
    monkeypatch.setattr(QuerybookSettings, "LANGSMITH_TRACING", True, raising=False)
    return capture


@pytest.fixture
def with_token(monkeypatch):
    monkeypatch.setattr(audit_context, "get_access_token_safe", lambda: _FakeToken())


@pytest.fixture
def without_token(monkeypatch):
    monkeypatch.setattr(audit_context, "get_access_token_safe", lambda: None)


def _info_lines(caplog):
    return [r.message for r in caplog.records if r.levelno == logging.INFO]


# -- Envelope structure (via EventLog) --------------------------------------


def test_envelope_has_all_keys(fake_logger, with_token):
    log_mcp_event("tool_invocation", {"tool": "x", "status": "success"})
    envelope = fake_logger.calls[0]["event_data"]
    assert ENVELOPE_KEYS.issubset(envelope.keys())
    assert envelope["subject"] == 42
    assert envelope["client_id"] == "claude"
    assert envelope["auth_method"] == "oauth"
    assert envelope["environment"] == "test"


def test_envelope_with_no_token(fake_logger, without_token):
    log_mcp_event("tool_invocation", {"status": "success"})
    envelope = fake_logger.calls[0]["event_data"]
    assert envelope["subject"] == 0
    assert envelope["session_id"] is None
    assert envelope["session_kind"] is None
    assert envelope["auth_method"] == "unknown"


def test_session_id_is_sha256_of_token(fake_logger, with_token):
    log_mcp_event("tool_invocation", {"status": "success"})
    envelope = fake_logger.calls[0]["event_data"]
    expected = hashlib.sha256(b"raw-bearer-value").hexdigest()
    assert envelope["session_id"] == expected
    assert envelope["session_kind"] == "access_token"


def test_session_id_prefers_claim_value(fake_logger, monkeypatch):
    class _TokenWithSession:
        token = "raw-upstream-value"
        claims = {
            "creator_uid": 42,
            "auth_method": "oauth",
            "session_id": "fastmcp-session-hash",
        }

    monkeypatch.setattr(
        audit_context, "get_access_token_safe", lambda: _TokenWithSession()
    )
    log_mcp_event("tool_invocation", {"status": "success"})
    envelope = fake_logger.calls[0]["event_data"]
    assert envelope["session_id"] == "fastmcp-session-hash"
    assert envelope["session_kind"] == "access_token"


def test_payload_merges_into_envelope(fake_logger, without_token):
    log_mcp_event(
        "tool_invocation", {"tool": "x", "status": "success", "duration_ms": 42.0}
    )
    envelope = fake_logger.calls[0]["event_data"]
    assert envelope["tool"] == "x"
    assert envelope["duration_ms"] == 42.0


def test_eventlog_receives_uid(fake_logger, with_token):
    log_mcp_event("tool_invocation", {"status": "success"})
    assert fake_logger.calls[0]["uid"] == 42


# -- Log routing (security/error events -> LOG.info) ------------------------


@pytest.mark.parametrize(
    "event_type,status,expect_log",
    [
        ("authz", None, True),
        ("rejected_invocation", None, True),
        ("anomaly", None, True),
        ("tool_invocation", "error", True),
        ("resource_read", "error", True),
        ("tool_invocation", "success", False),
        ("resource_read", "success", False),
    ],
)
def test_routing_table(
    event_type, status, expect_log, caplog, fake_logger, without_token
):
    payload = {} if status is None else {"status": status}
    with caplog.at_level(logging.INFO, logger=LOG.name):
        log_mcp_event(event_type, payload)

    assert (len(_info_lines(caplog)) == 1) is expect_log
    assert len(fake_logger.calls) == 1


def test_log_line_is_human_readable(caplog, fake_logger, with_token):
    with caplog.at_level(logging.INFO, logger=LOG.name):
        log_mcp_event("tool_invocation", {"tool": "run_query", "status": "error"})
    line = _info_lines(caplog)[0]
    assert "MCP tool_invocation" in line
    assert "subject=42" in line
    assert "tool=run_query" in line
    assert "status=error" in line


def test_eventlog_disabled_still_emits_log(
    caplog, fake_logger, without_token, monkeypatch
):
    monkeypatch.setattr(QuerybookSettings, "EVENT_LOGGER_NAME", "null", raising=False)
    with caplog.at_level(logging.INFO, logger=LOG.name):
        log_mcp_event("anomaly", {"detail": "x"})
    assert len(_info_lines(caplog)) == 1
    assert fake_logger.calls == []


# -- Request correlation ----------------------------------------------------


def test_request_id_appears_in_envelope(fake_logger, without_token):
    tok = _request_id_var.set("abc123")
    try:
        log_mcp_event("tool_invocation", {"status": "success"})
    finally:
        _request_id_var.reset(tok)
    assert fake_logger.calls[0]["event_data"]["request_id"] == "abc123"


def test_request_id_defaults_to_unknown(fake_logger, without_token):
    log_mcp_event("tool_invocation", {"status": "success"})
    assert fake_logger.calls[0]["event_data"]["request_id"] == "unknown"


def test_request_id_middleware_sets_and_resets():
    captured = {}

    async def app(scope, receive, send):
        captured["request_id"] = _request_id_var.get()

    middleware = RequestAuditMiddleware(app)
    asyncio.run(middleware({"type": "http"}, None, None))

    assert captured["request_id"] is not None
    assert len(captured["request_id"]) == 32
    assert _request_id_var.get() is None


def test_request_id_middleware_passthrough_non_http():
    captured = {"called": False}

    async def app(scope, receive, send):
        captured["called"] = True
        assert _request_id_var.get() is None

    middleware = RequestAuditMiddleware(app)
    asyncio.run(middleware({"type": "lifespan"}, None, None))
    assert captured["called"]


# -- Token safety -----------------------------------------------------------


def test_raw_token_never_in_log(caplog, fake_logger, with_token):
    with caplog.at_level(logging.INFO, logger=LOG.name):
        log_mcp_event("tool_invocation", {"status": "error"})
    for line in _info_lines(caplog):
        assert "raw-bearer-value" not in line


def test_raw_token_never_in_eventlog(fake_logger, with_token):
    log_mcp_event("tool_invocation", {"status": "success"})
    serialized = json.dumps(fake_logger.calls[0]["event_data"], default=str)
    assert "raw-bearer-value" not in serialized


# -- Defensive wrapping -----------------------------------------------------


def test_audit_failure_does_not_raise(monkeypatch, without_token):
    """An exception inside log_mcp_event must not propagate to the caller."""

    class _BrokenLogger:
        def log_mcp_event(self, **kwargs):
            raise RuntimeError("boom")

    monkeypatch.setattr(audit_router, "event_logger", _BrokenLogger())
    log_mcp_event("tool_invocation", {"status": "success"})


# -- Config snapshot (audit 8.4) --------------------------------------------


class _Named:
    def __init__(self, value):
        self.name = value
        self.uri = value


class _FakeMCP:
    """Stub exposing FastMCP's async list_tools / list_resources surface."""

    def __init__(self, tools, resources):
        self._tools = tools
        self._resources = resources

    async def list_tools(self, *, run_middleware=True):
        return [_Named(t) for t in self._tools]

    async def list_resources(self, *, run_middleware=True):
        return [_Named(r) for r in self._resources]


def test_build_config_snapshot_enumerates_sorted_surface():
    snapshot = build_config_snapshot(_FakeMCP(["b_tool", "a_tool"], ["z://x", "a://y"]))
    assert snapshot["tools"] == ["a_tool", "b_tool"]
    assert snapshot["resources"] == ["a://y", "z://x"]


def test_build_config_snapshot_emits_secrets_as_booleans(monkeypatch):
    monkeypatch.setattr(QuerybookSettings, "OAUTH_CLIENT_ID", "id", raising=False)
    monkeypatch.setattr(QuerybookSettings, "OAUTH_CLIENT_SECRET", "shh", raising=False)
    monkeypatch.setattr(QuerybookSettings, "MCP_AUTH_SECRET", "shh", raising=False)
    monkeypatch.setattr(
        QuerybookSettings, "MCP_OAUTH_BASE_URL", "https://x", raising=False
    )
    monkeypatch.setattr(
        QuerybookSettings, "MCP_OIDC_CONFIG_URL", "https://x/.well-known", raising=False
    )

    snapshot = build_config_snapshot(_FakeMCP([], []))

    assert snapshot["oauth_configured"] is True
    assert snapshot["oidc_configured"] is True
    # No secret value should appear anywhere in the payload.
    serialized = json.dumps(snapshot, default=str)
    assert "shh" not in serialized


def test_build_config_snapshot_oauth_not_configured(monkeypatch):
    monkeypatch.setattr(QuerybookSettings, "OAUTH_CLIENT_ID", None, raising=False)
    snapshot = build_config_snapshot(_FakeMCP([], []))
    assert snapshot["oauth_configured"] is False


def test_enumerate_surface_degrades_to_empty_on_error():
    class _BrokenMCP:
        async def list_tools(self, *, run_middleware=True):
            raise RuntimeError("boom")

        async def list_resources(self, *, run_middleware=True):
            return []

    snapshot = build_config_snapshot(_BrokenMCP())
    assert snapshot["tools"] == []
    assert snapshot["resources"] == []


def test_log_config_snapshot_uses_system_context(caplog, fake_logger):
    with caplog.at_level(logging.INFO, logger=LOG.name):
        log_config_snapshot(_FakeMCP(["a_tool"], []))

    envelope = fake_logger.calls[0]["event_data"]
    assert envelope["event_type"] == "config_snapshot"
    assert envelope["subject"] == 0
    assert envelope["auth_method"] == "system"
    assert envelope["request_id"] == "startup"
    assert envelope["session_id"] is None
    assert envelope["session_kind"] is None
    assert envelope["environment"] == "test"
    # config_snapshot is a security event -> always hits the LOG.info signal.
    assert len(_info_lines(caplog)) == 1


def test_log_config_snapshot_does_not_read_request_token(monkeypatch, fake_logger):
    """The snapshot must not reach for an access token it has no request for."""

    def _boom():
        raise AssertionError("get_access_token_safe must not be called at startup")

    monkeypatch.setattr(audit_context, "get_access_token_safe", _boom)
    log_config_snapshot(_FakeMCP([], []))
    assert fake_logger.calls[0]["event_data"]["auth_method"] == "system"


# -- LangSmith routing (lightweight runs for non-execution events) ----------


def test_config_snapshot_emits_langsmith_run(fake_logger, fake_langsmith):
    log_config_snapshot(_FakeMCP(["a_tool"], []))

    assert len(fake_langsmith.runs) == 1
    run = fake_langsmith.runs[0]
    assert run["kwargs"]["name"] == "mcp.config_snapshot"
    assert run["kwargs"]["metadata"]["operation_type"] == "audit"
    assert run["kwargs"]["metadata"]["event_type"] == "config_snapshot"
    assert run["kwargs"]["metadata"]["auth_method"] == "system"
    assert run["kwargs"]["metadata"]["tool_count"] == 1
    assert run["kwargs"]["metadata"]["resource_count"] == 0
    assert "tools" not in run["kwargs"]["metadata"]
    assert run["outputs"]["auth_mode"] == QuerybookSettings.MCP_AUTH_MODE
    assert "oauth_configured" in run["outputs"]
    assert "event_logger_name" in run["outputs"]
    assert run["outputs"]["tools"] == ["a_tool"]
    assert run["outputs"]["resources"] == []
    assert "query_result_limits" in run["outputs"]
    # EventLog still receives it too — LangSmith is additive, not a replacement.
    assert len(fake_logger.calls) == 1


def test_no_langsmith_run_when_tracing_disabled(fake_logger, monkeypatch):
    capture = _LangSmithCapture()
    monkeypatch.setattr(audit_langsmith, "langsmith", capture)
    monkeypatch.setattr(QuerybookSettings, "LANGSMITH_TRACING", False, raising=False)

    log_config_snapshot(_FakeMCP([], []))
    assert capture.runs == []
    assert len(fake_logger.calls) == 1


def test_rich_trace_events_get_no_lightweight_run(
    fake_logger, fake_langsmith, without_token
):
    """tool_invocation / resource_read are traced in middleware; the router must
    not emit a second (lightweight) LangSmith record for them."""
    log_mcp_event("tool_invocation", {"tool": "x", "status": "success"})
    log_mcp_event("resource_read", {"resource_uri": "q://x", "status": "success"})
    assert fake_langsmith.runs == []
    assert len(fake_logger.calls) == 2


# -- Middleware integration: redaction is wired into the audit path ---------


def test_event_logging_middleware_redacts_and_caps_params(fake_logger, without_token):
    """A secret-keyed arg and an inline email must be scrubbed in the emitted
    event; benign scalars pass through. Proves redact() is wired at the sink."""
    mw = MCPEventLoggingMiddleware()
    ctx = MagicMock()
    ctx.message.name = "execute_ad_hoc_query"
    ctx.message.arguments = {
        "query": "SELECT * FROM t WHERE email = 'jane@x.com'",
        "api_key": "sk-live-secret",
        "limit": 10,
    }

    async def call_next(_ctx):
        result = MagicMock()
        result.structured_content = {"status": "ok"}
        return result

    asyncio.run(mw.on_call_tool(ctx, call_next))

    params = fake_logger.calls[0]["event_data"]["parameters"]
    assert params["api_key"] == "[REDACTED:secret]"
    assert "jane@x.com" not in params["query"]
    assert "[REDACTED:email]" in params["query"]
    assert params["limit"] == 10


def test_langsmith_failure_does_not_break_other_sinks(fake_logger, monkeypatch):
    """A LangSmith error must not abort EventLog or propagate to the caller."""

    class _BrokenLangSmith:
        def trace(self, **kwargs):
            raise RuntimeError("langsmith down")

    monkeypatch.setattr(audit_langsmith, "langsmith", _BrokenLangSmith())
    monkeypatch.setattr(QuerybookSettings, "LANGSMITH_TRACING", True, raising=False)

    log_config_snapshot(_FakeMCP([], []))
    # EventLog still got the row despite LangSmith blowing up.
    assert len(fake_logger.calls) == 1


# -- Auth events (8.2): recorders + request-boundary flush ------------------


@pytest.fixture(autouse=True)
def _clear_auth_outcome():
    # ContextVars are not isolated between pytest tests; clear so a recorded
    # outcome never leaks into the next test.
    _auth_outcome_var.set(None)
    yield
    _auth_outcome_var.set(None)


def _run_boundary(record=None, status_code=None, headers=None):
    """Drive RequestAuditMiddleware with an app that optionally records an auth
    outcome and sends a response with the given status code. ``headers`` are the
    ASGI request headers (list of byte tuples) used to detect a presented bearer.
    The flush's effect is observed via the patched sinks (fake_logger/caplog)."""

    async def app(scope, receive, send):
        if record is not None:
            record()
        if status_code is not None:
            await send(
                {"type": "http.response.start", "status": status_code, "headers": []}
            )
            await send({"type": "http.response.body", "body": b""})

    async def send(message):
        pass

    scope = {"type": "http", "headers": headers or []}
    asyncio.run(RequestAuditMiddleware(app)(scope, None, send))


def test_record_auth_failure_emits_standalone_auth_event(caplog, fake_logger):
    with caplog.at_level(logging.INFO, logger=LOG.name):
        _run_boundary(
            record=lambda: record_auth_failure("invalid_api_token", "api_token"),
            status_code=401,
        )
    assert len(fake_logger.calls) == 1
    env = fake_logger.calls[0]["event_data"]
    assert env["event_type"] == "auth"
    assert env["result"] == "failure"
    assert env["auth_reason"] == "invalid_api_token"
    assert env["auth_method"] == "api_token"
    assert env["subject"] == 0
    # A failure is security signal -> one LOG.info line.
    assert len(_info_lines(caplog)) == 1


def test_recorded_auth_event_flushed_when_app_raises(caplog, fake_logger):
    """A recorded auth outcome is emitted even if the downstream app raises,
    so an error during e.g. a /token exchange never drops its audit signal."""

    async def app(scope, receive, send):
        record_auth_failure("invalid_api_token", "api_token")
        raise RuntimeError("boom during token exchange")

    async def send(message):
        pass

    scope = {"type": "http", "headers": []}
    with caplog.at_level(logging.INFO, logger=LOG.name):
        with pytest.raises(RuntimeError, match="boom during token exchange"):
            asyncio.run(RequestAuditMiddleware(app)(scope, None, send))

    assert len(fake_logger.calls) == 1
    env = fake_logger.calls[0]["event_data"]
    assert env["event_type"] == "auth"
    assert env["result"] == "failure"
    assert env["auth_reason"] == "invalid_api_token"
    # ContextVar is still cleared by the finally block.
    assert _auth_outcome_var.get() is None


def test_record_auth_success_rides_on_tool_event(caplog, fake_logger):
    with caplog.at_level(logging.INFO, logger=LOG.name):
        _run_boundary(
            record=lambda: record_auth_success("valid_api_token", "api_token"),
            status_code=200,
        )
    # Success emits nothing at the boundary — it rides on the tool event.
    assert fake_logger.calls == []
    assert _info_lines(caplog) == []


def test_no_token_probe_is_eventlog_only(caplog, fake_logger):
    with caplog.at_level(logging.INFO, logger=LOG.name):
        _run_boundary(record=None, status_code=401)
    assert len(fake_logger.calls) == 1
    assert fake_logger.calls[0]["event_data"]["event_type"] == "no_token"
    # Routine discovery probe is not a security signal.
    assert _info_lines(caplog) == []


def test_successful_non_auth_request_emits_nothing(fake_logger):
    # 200 with nothing recorded (e.g. a /.well-known route) -> no auth event.
    _run_boundary(record=None, status_code=200)
    assert fake_logger.calls == []


def test_auth_outcome_cleared_between_sequential_requests(fake_logger):
    """Same-loop sequential requests must not reuse a prior auth outcome.

    ASGI servers usually isolate requests in separate tasks, but the boundary
    should still leave the ContextVar empty after flushing so tests and any
    same-context dispatch path cannot duplicate stale auth events.
    """

    async def send(message):
        pass

    async def first_app(scope, receive, send):
        record_auth_failure("invalid_api_token", "api_token")
        await send({"type": "http.response.start", "status": 401, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    async def second_app(scope, receive, send):
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    async def run():
        scope = {"type": "http", "headers": []}
        await RequestAuditMiddleware(first_app)(scope, None, send)
        await RequestAuditMiddleware(second_app)(scope, None, send)

    asyncio.run(run())

    assert len(fake_logger.calls) == 1
    assert fake_logger.calls[0]["event_data"]["auth_reason"] == "invalid_api_token"
    assert _auth_outcome_var.get() is None


def test_get_recorded_auth_reason_returns_recorded():
    assert get_recorded_auth_reason() is None
    record_auth_success("valid_oauth_token", "oauth")
    assert get_recorded_auth_reason() == "valid_oauth_token"


def test_auth_failure_emits_langsmith_run(fake_logger, fake_langsmith):
    _run_boundary(
        record=lambda: record_auth_failure("invalid_api_token", "api_token"),
        status_code=401,
    )
    assert len(fake_langsmith.runs) == 1
    run = fake_langsmith.runs[0]
    assert run["kwargs"]["name"] == "mcp.auth.invalid_api_token"
    assert run["kwargs"]["metadata"]["operation_type"] == "audit"
    assert run["kwargs"]["metadata"]["event_type"] == "auth"
    assert run["kwargs"]["metadata"]["auth_reason"] == "invalid_api_token"
    assert run["outputs"] == {
        "result": "failure",
        "auth_reason": "invalid_api_token",
    }


def test_no_token_probe_emits_no_langsmith_run(fake_logger, fake_langsmith):
    _run_boundary(record=None, status_code=401)
    # no_token is EventLog-only — no forensic LangSmith run.
    assert fake_langsmith.runs == []


_BEARER_HEADERS = [(b"authorization", b"Bearer some.jwt.value")]


def test_bearer_present_but_unrecorded_is_not_no_token(caplog, fake_logger):
    """Regression: a presented-but-rejected bearer that no verifier classified
    must NOT be mislabeled `no_token` (that means *no credential*). This is the
    exact gap that let an expired OAuth token surface as no_token — the original
    no_token test used record=None, which conflated 'no token' with 'token
    failed, unrecorded', baking the bug into the test."""
    with caplog.at_level(logging.INFO, logger=LOG.name):
        _run_boundary(record=None, status_code=401, headers=_BEARER_HEADERS)
    assert len(fake_logger.calls) == 1
    env = fake_logger.calls[0]["event_data"]
    assert env["event_type"] == "auth"
    assert env["result"] == "failure"
    assert env["auth_reason"] == "unclassified_token_rejection"
    # An unclassified rejected credential defaults to security signal.
    assert len(_info_lines(caplog)) == 1


def test_no_token_only_when_bearer_absent(fake_logger):
    # The complement of the regression: a 401 with no Authorization header is the
    # genuine no-token probe.
    _run_boundary(record=None, status_code=401, headers=[])
    assert fake_logger.calls[0]["event_data"]["event_type"] == "no_token"


# -- Token issuance / refresh (8.2): standalone lifecycle auth events -------


def test_token_issuance_success_is_eventlog_and_langsmith_not_signal(
    caplog, fake_logger, fake_langsmith
):
    """An OAuth token issuance success has no tool to ride on, so it is a
    standalone `auth` event: retained in EventLog + a lightweight LangSmith run,
    but NOT routed to the LOG.info security signal (it is not a failure)."""
    with caplog.at_level(logging.INFO, logger=LOG.name):
        _run_boundary(
            record=lambda: record_token_issuance(
                "token_issued",
                "oauth",
                success=True,
                subject=42,
                client_id="claude",
                session_id="hashed-session",
            ),
            status_code=200,
        )
    assert len(fake_logger.calls) == 1
    env = fake_logger.calls[0]["event_data"]
    assert env["event_type"] == "auth"
    assert env["result"] == "success"
    assert env["auth_reason"] == "token_issued"
    assert env["subject"] == 42
    assert env["client_id"] == "claude"
    assert env["session_id"] == "hashed-session"
    assert env["session_kind"] == "access_token"
    # Credential lifecycle is forensically valuable -> retained in LangSmith ...
    assert len(fake_langsmith.runs) == 1
    run = fake_langsmith.runs[0]
    assert run["kwargs"]["name"] == "mcp.auth.token_issued"
    assert run["kwargs"]["metadata"]["subject"] == 42
    assert run["outputs"] == {
        "result": "success",
        "auth_reason": "token_issued",
    }
    # ... but a success is not security signal.
    assert _info_lines(caplog) == []


def test_token_refresh_failure_is_security_signal(caplog, fake_logger):
    with caplog.at_level(logging.INFO, logger=LOG.name):
        _run_boundary(
            record=lambda: record_token_issuance(
                "token_refresh_failed", "oauth", success=False
            ),
            status_code=400,
        )
    env = fake_logger.calls[0]["event_data"]
    assert env["event_type"] == "auth"
    assert env["result"] == "failure"
    # A failed credential exchange IS security signal.
    assert len(_info_lines(caplog)) == 1


# -- Authorization deny events (8.3): emitted centrally from AuthorizationError --
#
# After the exception-mapping refactor the user_can_* gates raise a typed
# AuthorizationError carrying action/resource. MCPEventLoggingMiddleware detects
# it in the failed call's exception chain and emits the request's single `authz`
# deny — no per-call-site recorder. An *allow* has no record of its own: a
# successful tool_invocation is implicitly the allow (the allow-summary fields
# from the original 8.3 spec were intentionally dropped, see mcp-security.md).


def _make_tool_ctx(tool_name="get_datadoc"):
    ctx = MagicMock()
    ctx.message.name = tool_name
    ctx.message.arguments = {"datadoc_id": 5}
    return ctx


def test_tool_authz_deny_emits_authz_not_tool_invocation(
    caplog, fake_logger, fake_langsmith, without_token
):
    """A handler that raises AuthorizationError makes the request's single record
    the `authz` deny — no tool_invocation — and suppresses the lightweight
    LangSmith run (the tracing middleware records the one trace for this
    request)."""

    async def call_next(_ctx):
        raise AuthorizationError(action="write", resource="datadoc:5")

    mw = MCPEventLoggingMiddleware()
    with caplog.at_level(logging.INFO, logger=LOG.name):
        with pytest.raises(AuthorizationError):
            asyncio.run(mw.on_call_tool(_make_tool_ctx("update_datadoc"), call_next))

    assert len(fake_logger.calls) == 1
    env = fake_logger.calls[0]["event_data"]
    assert env["event_type"] == "authz"
    assert env["result"] == "deny"
    assert env["authz_denied_resource"] == "datadoc:5"
    assert env["authz_denied_action"] == "write"
    assert env["authz_reason"] == "no_write_permission"
    assert env["tool"] == "update_datadoc"
    # authz is a security signal -> LOG.info; but no duplicate LangSmith run.
    assert len(_info_lines(caplog)) == 1
    assert fake_langsmith.runs == []


def test_tool_authz_deny_detected_through_fastmcp_wrapper(fake_logger, without_token):
    """Production path: FastMCP wraps the handler's exception in a generic
    ToolError (and ExceptionMappingMiddleware re-raises a mapped ToolError) before
    MCPEventLoggingMiddleware sees it, so the deny is found via the __cause__
    chain — not just when the raw error reaches the middleware."""

    async def call_next(_ctx):
        try:
            raise AuthorizationError(action="read", resource="datadoc:9")
        except AuthorizationError as e:
            raise ToolError("You do not have permission to read this resource.") from e

    mw = MCPEventLoggingMiddleware()
    with pytest.raises(ToolError):
        asyncio.run(mw.on_call_tool(_make_tool_ctx(), call_next))

    env = fake_logger.calls[0]["event_data"]
    assert env["event_type"] == "authz"
    assert env["authz_denied_action"] == "read"
    assert env["authz_denied_resource"] == "datadoc:9"


def test_tool_non_authz_error_still_emits_tool_invocation(fake_logger, without_token):
    """A genuine (non-authz) failure stays a tool_invocation error."""

    async def call_next(_ctx):
        raise RuntimeError("engine timeout")

    mw = MCPEventLoggingMiddleware()
    with pytest.raises(RuntimeError):
        asyncio.run(mw.on_call_tool(_make_tool_ctx(), call_next))

    env = fake_logger.calls[0]["event_data"]
    assert env["event_type"] == "tool_invocation"
    assert env["status"] == "error"


def test_tool_success_emits_plain_tool_invocation(fake_logger, without_token):
    """Allow is implicit: a successful tool emits a normal tool_invocation with no
    authz_* fields. The allow summary was intentionally dropped in favor of full
    centralization — the deny is the only authorization-specific record."""

    async def call_next(_ctx):
        result = MagicMock()
        result.structured_content = {"status": "ok"}
        return result

    mw = MCPEventLoggingMiddleware()
    asyncio.run(mw.on_call_tool(_make_tool_ctx(), call_next))

    env = fake_logger.calls[0]["event_data"]
    assert env["event_type"] == "tool_invocation"
    assert env["status"] == "success"
    assert "authz_result" not in env
    assert "authz_denied_action" not in env


# -- Datadog metrics (7a): single emitter inside emit_audit_event -----------


def _keys(stats_calls):
    return [key for key, _tags in stats_calls]


def test_tool_invocation_success_emits_tool_call_only(
    fake_logger, fake_stats, with_token
):
    log_mcp_event("tool_invocation", {"tool": "run_query", "status": "success"})
    assert _keys(fake_stats.calls) == ["mcp.tool.call"]
    key, tags = fake_stats.calls[0]
    assert tags["surface"] == "tool"
    assert tags["tool"] == "run_query"
    assert tags["environment"] == "test"


def test_tool_invocation_error_emits_call_and_error(
    fake_logger, fake_stats, with_token
):
    log_mcp_event("tool_invocation", {"tool": "run_query", "status": "error"})
    assert _keys(fake_stats.calls) == ["mcp.tool.call", "mcp.tool.error"]


def test_resource_read_success_uses_resource_template_tag(
    fake_logger, fake_stats, with_token
):
    """The resolved ID in resource_uri must not leak into the tag value --
    that would make it an unbounded Datadog dimension. The middleware-supplied
    resource_template (the registered URI template) is the bounded tag."""
    log_mcp_event(
        "resource_read",
        {
            "resource_uri": "querybook://datadoc/123",
            "resource_template": "querybook://datadoc/{datadoc_id}",
            "status": "success",
        },
    )
    assert _keys(fake_stats.calls) == ["mcp.tool.call"]
    key, tags = fake_stats.calls[0]
    assert tags["surface"] == "resource"
    assert tags["tool"] == "querybook://datadoc/{datadoc_id}"
    assert "123" not in tags["tool"]


def test_resource_read_without_template_emits_no_tool_tag(
    fake_logger, fake_stats, with_token
):
    """resource_template is always supplied by wrap_mcp_resources (see the
    end-to-end test below); if a payload ever lacked it, the tag is simply
    omitted rather than falling back to the unbounded resource_uri."""
    log_mcp_event(
        "resource_read",
        {"resource_uri": "querybook://datadoc/123", "status": "success"},
    )
    _key, tags = fake_stats.calls[0]
    assert "tool" not in tags


def test_wrap_mcp_resources_supplies_resource_template_to_metric(
    fake_logger, fake_stats, without_token
):
    """End-to-end through the real wrap_mcp_resources wrapper (not a hand-built
    payload): confirms the middleware actually passes resource_template
    through to the metric, not just that the router can consume one."""

    class _FakeResourceMCP:
        def resource(self, *args, **kwargs):
            def decorator(func):
                return func

            return decorator

    mcp = wrap_mcp_resources(_FakeResourceMCP())
    wrapped_decorator = mcp.resource(uri="querybook://datadoc/{datadoc_id}")

    def get_datadoc(datadoc_id):
        return {"id": datadoc_id}

    get_datadoc.__module__ = "test"
    get_datadoc.__name__ = "get_datadoc"
    wrapped_func = wrapped_decorator(get_datadoc)

    wrapped_func(datadoc_id=123)

    _key, tags = fake_stats.calls[0]
    assert tags["tool"] == "querybook://datadoc/{datadoc_id}"
    assert "123" not in tags["tool"]


def test_resource_read_error_emits_call_and_error(fake_logger, fake_stats, with_token):
    log_mcp_event(
        "resource_read", {"resource_uri": "querybook://datadoc/123", "status": "error"}
    )
    assert _keys(fake_stats.calls) == ["mcp.tool.call", "mcp.tool.error"]


def test_auth_failure_emits_auth_failure_metric(fake_logger, fake_stats):
    _run_boundary(
        record=lambda: record_auth_failure("invalid_api_token", "api_token"),
        status_code=401,
    )
    assert _keys(fake_stats.calls) == ["mcp.auth.failure"]


def test_auth_success_emits_no_metric(fake_logger, fake_stats):
    _run_boundary(
        record=lambda: record_auth_success("valid_api_token", "api_token"),
        status_code=200,
    )
    assert fake_stats.calls == []


def test_authz_deny_emits_authz_metric(fake_logger, fake_stats, without_token):
    async def call_next(_ctx):
        raise AuthorizationError(action="write", resource="datadoc:5")

    mw = MCPEventLoggingMiddleware()
    with pytest.raises(AuthorizationError):
        asyncio.run(mw.on_call_tool(_make_tool_ctx("update_datadoc"), call_next))

    assert _keys(fake_stats.calls) == ["mcp.authz.deny"]
    _key, tags = fake_stats.calls[0]
    assert tags["tool"] == "update_datadoc"


def test_resource_authz_deny_uses_resource_template_tag(
    fake_logger, fake_stats, without_token
):
    """Resource authz denials carry resource_uri/resource_template, not tool
    -- the same bounded-tag convention must apply here too, so this path
    isn't left with only the environment tag."""
    log_mcp_event(
        "authz",
        {
            "resource_uri": "querybook://datadoc/123",
            "resource_template": "querybook://datadoc/{datadoc_id}",
            "result": "deny",
        },
    )
    assert _keys(fake_stats.calls) == ["mcp.authz.deny"]
    _key, tags = fake_stats.calls[0]
    assert tags["tool"] == "querybook://datadoc/{datadoc_id}"
    assert "123" not in tags["tool"]


def test_rejected_invocation_oversized_emits_rejected_only(
    fake_logger, fake_stats, without_token
):
    log_mcp_event("rejected_invocation", {"reason": "oversized"})
    assert _keys(fake_stats.calls) == ["mcp.rejected"]
    _key, tags = fake_stats.calls[0]
    assert tags["reason"] == "oversized"


def test_rejected_invocation_rate_limited_emits_both(
    fake_logger, fake_stats, without_token
):
    log_mcp_event("rejected_invocation", {"reason": "rate_limited"})
    assert _keys(fake_stats.calls) == ["mcp.rejected", "mcp.rate_limit"]


def test_config_snapshot_emits_no_metric(fake_logger, fake_stats):
    log_config_snapshot(_FakeMCP([], []))
    assert fake_stats.calls == []


def test_no_token_probe_emits_no_metric(fake_logger, fake_stats):
    _run_boundary(record=None, status_code=401, headers=[])
    assert fake_stats.calls == []


def test_environment_tag_present_on_every_emitted_counter(
    fake_logger, fake_stats, with_token
):
    log_mcp_event("tool_invocation", {"tool": "run_query", "status": "error"})
    log_mcp_event("auth", {"result": "failure"})
    log_mcp_event("rejected_invocation", {"reason": "rate_limited"})
    assert fake_stats.calls
    for _key, tags in fake_stats.calls:
        assert tags["environment"] == "test"


def test_stats_failure_does_not_break_other_sinks(
    fake_logger, monkeypatch, without_token
):
    """A stats-backend error must not suppress EventLog or propagate."""

    class _BrokenStats:
        def incr(self, key, tags=None):
            raise RuntimeError("datadog down")

    monkeypatch.setattr(audit_router, "stats_logger", _BrokenStats())
    log_mcp_event("tool_invocation", {"tool": "run_query", "status": "success"})
    assert len(fake_logger.calls) == 1


# -- 6a: oversized free-text argument guard ---------------------------------


def _make_validation_error():
    """A real pydantic ValidationError, as arg coercion would raise below the
    middleware. Kept local to avoid a cross-module test import."""
    from pydantic import BaseModel, ValidationError

    class _Model(BaseModel):
        n: int

    try:
        _Model(n="not-an-int")
    except ValidationError as e:
        return e


def _guard_ctx(name, arguments):
    ctx = MagicMock()
    ctx.message.name = name
    ctx.message.arguments = arguments
    return ctx


def _set_freetext_limit(monkeypatch, limit):
    monkeypatch.setattr(
        QuerybookSettings, "MCP_MAX_FREETEXT_INPUT_BYTES", limit, raising=False
    )


def test_oversized_args_rejected_before_tool_runs(
    fake_logger, fake_stats, without_token, monkeypatch
):
    _set_freetext_limit(monkeypatch, 10)
    called = []

    async def call_next(_ctx):
        called.append(True)
        return MagicMock()

    ctx = _guard_ctx("execute_ad_hoc_query", {"query": "x" * 100})
    with pytest.raises(ToolError) as exc_info:
        asyncio.run(PayloadSizeGuardMiddleware().on_call_tool(ctx, call_next))

    # Generic message: no payload echoed back.
    assert "maximum allowed size of 10 bytes" in str(exc_info.value)
    assert "xxxx" not in str(exc_info.value)
    # Tool body never ran.
    assert called == []
    # One rejected_invocation{oversized} event + one mcp.rejected counter.
    assert len(fake_logger.calls) == 1
    payload = fake_logger.calls[0]["event_data"]
    assert payload["event_type"] == "rejected_invocation"
    assert payload["reason"] == "oversized"
    assert payload["tool"] == "execute_ad_hoc_query"
    assert payload["limit_bytes"] == 10
    assert payload["size_bytes"] > 10
    assert _keys(fake_stats.calls) == ["mcp.rejected"]
    assert fake_stats.calls[0][1]["reason"] == "oversized"


def test_within_limit_passes_through(
    fake_logger, fake_stats, without_token, monkeypatch
):
    _set_freetext_limit(monkeypatch, 1000)
    called = []

    async def call_next(_ctx):
        called.append(True)
        result = MagicMock()
        result.structured_content = {"status": "ok"}
        return result

    ctx = _guard_ctx("execute_ad_hoc_query", {"query": "SELECT 1"})
    asyncio.run(PayloadSizeGuardMiddleware().on_call_tool(ctx, call_next))
    assert called == [True]
    # No rejection event or counter.
    assert fake_logger.calls == []
    assert fake_stats.calls == []


def test_zero_limit_disables_guard(fake_logger, fake_stats, without_token, monkeypatch):
    _set_freetext_limit(monkeypatch, 0)
    called = []

    async def call_next(_ctx):
        called.append(True)
        return MagicMock()

    ctx = _guard_ctx("execute_ad_hoc_query", {"query": "x" * 10_000})
    asyncio.run(PayloadSizeGuardMiddleware().on_call_tool(ctx, call_next))
    assert called == [True]
    assert fake_logger.calls == []


# -- 6a: _freetext_bytes_over_limit unit edges ------------------------------


def test_freetext_boundary_exact_and_off_by_one():
    # limit exactly hit is within budget (strict >), limit+1 is over.
    assert _freetext_bytes_over_limit({"a": "xxx"}, 4) is None  # key 'a' + 'xxx' = 4
    over = _freetext_bytes_over_limit({"a": "xxxx"}, 4)  # 1 + 4 = 5
    assert over == 5


def test_freetext_counts_utf8_bytes_not_chars():
    # '€' is 3 UTF-8 bytes; three of them = 9 bytes, over a 5-byte limit.
    assert _freetext_bytes_over_limit({"x": "€€€"}, 100) is None
    over = _freetext_bytes_over_limit(["€€€"], 5)
    assert over is not None and over >= 9


def test_freetext_counts_dict_keys():
    # No string values, only a large key — must still be counted.
    assert _freetext_bytes_over_limit({"k" * 50: 123}, 10) == 50


def test_freetext_ignores_non_string_scalars():
    assert _freetext_bytes_over_limit({"a": 1, "b": True, "c": None}, 10) is None


def test_freetext_deep_nesting_no_recursion_error():
    # Build a deeply nested structure that would blow a recursive walk's stack.
    node = "leaf"
    for _ in range(20_000):
        node = [node]
    # Within a huge limit -> walks fully without RecursionError, returns None.
    assert _freetext_bytes_over_limit(node, 10_000_000) is None
    # Over a tiny limit -> the 4-byte leaf pushes past it (no RecursionError).
    assert _freetext_bytes_over_limit(node, 1) == 4


# -- 6b: rejected_invocation on malformed params ----------------------------


def _run_event_mw(call_next):
    mw = MCPEventLoggingMiddleware()
    ctx = _guard_ctx("execute_ad_hoc_query", {"query": "SELECT 1"})
    return asyncio.run(mw.on_call_tool(ctx, call_next))


def test_validation_error_emits_malformed_params(
    fake_logger, fake_stats, without_token
):
    err = _make_validation_error()

    async def call_next(_ctx):
        raise err

    with pytest.raises(Exception):
        _run_event_mw(call_next)

    assert len(fake_logger.calls) == 1
    payload = fake_logger.calls[0]["event_data"]
    assert payload["event_type"] == "rejected_invocation"
    assert payload["reason"] == "malformed_params"
    assert payload["tool"] == "execute_ad_hoc_query"
    assert "duration_ms" in payload
    assert _keys(fake_stats.calls) == ["mcp.rejected"]
    assert fake_stats.calls[0][1]["reason"] == "malformed_params"


def test_validation_error_wrapped_by_fastmcp_emits_malformed_params(
    fake_logger, fake_stats, without_token
):
    async def call_next(_ctx):
        try:
            raise _make_validation_error()
        except Exception as e:
            raise ToolError("Error calling tool 'execute_ad_hoc_query': ") from e

    with pytest.raises(ToolError):
        _run_event_mw(call_next)

    payload = fake_logger.calls[0]["event_data"]
    assert payload["event_type"] == "rejected_invocation"
    assert payload["reason"] == "malformed_params"
    # The audit error must come from the underlying ValidationError, not the
    # generic ToolError wrapper message -- otherwise the field-level detail
    # (which arg, what was wrong) is lost.
    assert "n" in payload["error"]
    assert "Error calling tool" not in payload["error"]


def test_validation_error_emits_no_lightweight_langsmith_run(
    fake_logger, fake_langsmith, without_token
):
    """emit_langsmith=False: the outer tracing middleware already ended this
    request's rich trace with the error, so no duplicate lightweight run."""

    async def call_next(_ctx):
        raise _make_validation_error()

    with pytest.raises(Exception):
        _run_event_mw(call_next)
    assert fake_langsmith.runs == []


def test_non_validation_error_still_emits_generic_tool_error(
    fake_logger, fake_stats, without_token
):
    """Regression guard: a non-validation error keeps the generic
    tool_invocation{status=error} path (not malformed_params)."""

    async def call_next(_ctx):
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        _run_event_mw(call_next)

    payload = fake_logger.calls[0]["event_data"]
    assert payload["event_type"] == "tool_invocation"
    assert payload["status"] == "error"
    assert _keys(fake_stats.calls) == ["mcp.tool.call", "mcp.tool.error"]
