"""Tests for per-credential failure-burst anomaly detection."""

import pytest

from env import QuerybookSettings
from lib.mcp.audit import anomaly as anomaly_module
from lib.mcp.audit import router as audit_router
from lib.mcp.audit.router import emit_audit_event
from lib.stats_logger import MCP_ANOMALY


class _EventLogCapture:
    def __init__(self):
        self.calls = []

    def log_mcp_event(self, uid, event_data):
        self.calls.append({"uid": uid, "event_data": event_data})

    def events_of_type(self, event_type):
        return [
            c["event_data"]
            for c in self.calls
            if c["event_data"].get("event_type") == event_type
        ]


class _StatsCapture:
    def __init__(self):
        self.calls = []

    def incr(self, key, tags=None):
        self.calls.append((key, tags))

    def keys(self):
        return [key for key, _ in self.calls]


class _BoomRedis:
    def eval(self, *args, **kwargs):
        raise RuntimeError("redis is down")


def _ctx(session_id="cred-a"):
    return {
        "request_id": "req-1",
        "subject": 7,
        "client_id": "client-1",
        "auth_method": "access_token",
        "session_id": session_id,
        "session_kind": "access_token",
        "environment": "test",
    }


@pytest.fixture(autouse=True)
def _patch_env(monkeypatch):
    monkeypatch.setattr(QuerybookSettings, "ENVIRONMENT", "test", raising=False)
    monkeypatch.setattr(QuerybookSettings, "EVENT_LOGGER_NAME", "db", raising=False)
    monkeypatch.setattr(QuerybookSettings, "LANGSMITH_TRACING", False, raising=False)
    monkeypatch.setattr(
        QuerybookSettings, "MCP_ANOMALY_FAILURE_THRESHOLD", 3, raising=False
    )
    monkeypatch.setattr(
        QuerybookSettings, "MCP_ANOMALY_WINDOW_SECONDS", 300, raising=False
    )


@pytest.fixture
def fake_logger(monkeypatch):
    capture = _EventLogCapture()
    monkeypatch.setattr(audit_router, "event_logger", capture)
    return capture


@pytest.fixture
def fake_stats(monkeypatch):
    capture = _StatsCapture()
    monkeypatch.setattr(audit_router, "stats_logger", capture)
    return capture


@pytest.fixture
def fake_redis(monkeypatch):
    fakeredis = pytest.importorskip("fakeredis")
    client = fakeredis.FakeRedis()
    monkeypatch.setattr(anomaly_module, "_get_redis_client", lambda: client)
    return client


def _deny(ctx=None):
    """Emit one authz-deny failure signal through the audit funnel."""
    emit_audit_event("authz", {"tool": "execute_ad_hoc_query"}, ctx or _ctx())


# -- Core burst behavior ------------------------------------------------------


def test_no_anomaly_below_threshold(fake_redis, fake_logger, fake_stats):
    for _ in range(3):  # threshold == 3
        _deny()
    assert fake_logger.events_of_type("anomaly") == []
    assert MCP_ANOMALY not in fake_stats.keys()


def test_anomaly_emitted_once_on_crossing(fake_redis, fake_logger, fake_stats):
    for _ in range(4):  # crosses on the 4th (count == threshold + 1)
        _deny()

    anomalies = fake_logger.events_of_type("anomaly")
    assert len(anomalies) == 1
    payload = anomalies[0]
    assert payload["reason"] == "failure_burst"
    assert payload["failure_count"] == 4
    assert payload["window_seconds"] == 300
    assert payload["trigger_event_type"] == "authz"
    assert payload["session_id"] == "cred-a"
    assert MCP_ANOMALY in fake_stats.keys()


def test_anomaly_not_re_emitted_after_crossing(fake_redis, fake_logger, fake_stats):
    for _ in range(7):  # stays over threshold for the rest of the window
        _deny()
    # Debounced: still exactly one anomaly event / one mcp.anomaly increment.
    assert len(fake_logger.events_of_type("anomaly")) == 1
    assert fake_stats.keys().count(MCP_ANOMALY) == 1


def test_anomaly_metric_carries_reason_and_environment_tags(
    fake_redis, fake_logger, fake_stats
):
    for _ in range(4):
        _deny()
    tags = next(t for k, t in fake_stats.calls if k == MCP_ANOMALY)
    assert tags == {"reason": "failure_burst", "environment": "test"}


# -- Isolation & event selection ----------------------------------------------


def test_separate_credentials_have_independent_buckets(
    fake_redis, fake_logger, fake_stats
):
    for _ in range(3):
        _deny(_ctx("cred-a"))
    for _ in range(3):
        _deny(_ctx("cred-b"))
    # Neither credential crossed on its own; the counts must not commingle.
    assert fake_logger.events_of_type("anomaly") == []


def test_successful_tool_calls_are_not_counted(fake_redis, fake_logger, fake_stats):
    for _ in range(5):
        emit_audit_event("tool_invocation", {"tool": "get_datadoc"}, _ctx())
    assert fake_logger.events_of_type("anomaly") == []


def test_tool_execution_errors_are_not_counted(fake_redis, fake_logger, fake_stats):
    for _ in range(5):
        emit_audit_event(
            "tool_invocation", {"tool": "get_datadoc", "status": "error"}, _ctx()
        )
    assert fake_logger.events_of_type("anomaly") == []


def test_auth_success_is_not_counted(fake_redis, fake_logger, fake_stats):
    for _ in range(5):
        emit_audit_event("auth", {"result": "success"}, _ctx())
    assert fake_logger.events_of_type("anomaly") == []


def test_rejected_and_auth_failures_are_counted(fake_redis, fake_logger, fake_stats):
    emit_audit_event("auth", {"result": "failure"}, _ctx())
    emit_audit_event("rejected_invocation", {"reason": "oversized"}, _ctx())
    emit_audit_event("rejected_invocation", {"reason": "rate_limited"}, _ctx())
    _deny()  # 4th failure across mixed types -> crosses
    assert len(fake_logger.events_of_type("anomaly")) == 1


# -- Disable / safety guards --------------------------------------------------


def test_disabled_when_threshold_zero(monkeypatch, fake_redis, fake_logger, fake_stats):
    monkeypatch.setattr(
        QuerybookSettings, "MCP_ANOMALY_FAILURE_THRESHOLD", 0, raising=False
    )
    for _ in range(10):
        _deny()
    assert fake_logger.events_of_type("anomaly") == []


def test_no_session_id_is_not_counted(fake_redis, fake_logger, fake_stats):
    for _ in range(10):
        _deny(_ctx(session_id=None))
    assert fake_logger.events_of_type("anomaly") == []


def test_redis_error_fails_soft_without_suppressing_the_event(
    monkeypatch, fake_logger, fake_stats
):
    monkeypatch.setattr(anomaly_module, "_get_redis_client", lambda: _BoomRedis())
    # Must not raise, and the triggering authz event must still be recorded.
    for _ in range(5):
        _deny()
    assert len(fake_logger.events_of_type("authz")) == 5
    assert fake_logger.events_of_type("anomaly") == []
