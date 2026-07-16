"""Tests for the Redis-backed per-credential MCP rate limiter."""

import asyncio
import hashlib

import pytest

from env import QuerybookSettings
from lib.mcp.audit import rate_limit as rate_limit_module
from lib.mcp.audit import router as audit_router
from lib.mcp.audit.rate_limit import RateLimitMiddleware
from lib.stats_logger import MCP_RATE_LIMIT_BACKEND_ERROR


def _headers(token="some.jwt.value"):
    if token is None:
        return []
    return [(b"authorization", f"Bearer {token}".encode())]


class _AuthenticatedUser:
    is_authenticated = True


class _UnauthenticatedUser:
    is_authenticated = False


class _RecordingApp:
    def __init__(self):
        self.calls = 0

    async def __call__(self, scope, receive, send):
        self.calls += 1


class _ResponseCapture:
    def __init__(self):
        self.messages = []

    async def __call__(self, message):
        self.messages.append(message)

    @property
    def status(self):
        for m in self.messages:
            if m["type"] == "http.response.start":
                return m["status"]
        return None

    @property
    def headers(self):
        for m in self.messages:
            if m["type"] == "http.response.start":
                return dict(m["headers"])
        return {}


class _EventLogCapture:
    def __init__(self):
        self.calls = []

    def log_mcp_event(self, uid, event_data):
        self.calls.append({"uid": uid, "event_data": event_data})


class _StatsCapture:
    def __init__(self):
        self.calls = []

    def incr(self, key, tags=None):
        self.calls.append((key, tags))


@pytest.fixture(autouse=True)
def _patch_env(monkeypatch):
    monkeypatch.setattr(QuerybookSettings, "ENVIRONMENT", "test", raising=False)
    monkeypatch.setattr(QuerybookSettings, "EVENT_LOGGER_NAME", "db", raising=False)
    monkeypatch.setattr(
        QuerybookSettings, "MCP_RATE_LIMIT_MAX_REQUESTS", 3, raising=False
    )
    monkeypatch.setattr(
        QuerybookSettings, "MCP_RATE_LIMIT_WINDOW_SECONDS", 60, raising=False
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
    monkeypatch.setattr(rate_limit_module, "stats_logger", capture)
    return capture


@pytest.fixture
def fake_redis(monkeypatch):
    fakeredis_aioredis = pytest.importorskip("fakeredis.aioredis")
    client = fakeredis_aioredis.FakeRedis()
    monkeypatch.setattr(rate_limit_module, "_get_redis_client", lambda: client)
    return client


def _run(scope, app):
    send = _ResponseCapture()
    asyncio.run(RateLimitMiddleware(app)(scope, None, send))
    return send


def _http_scope(token="some.jwt.value", authenticated=True):
    scope = {"type": "http", "headers": _headers(token)}
    if token is not None:
        scope["user"] = (
            _AuthenticatedUser() if authenticated else _UnauthenticatedUser()
        )
    return scope


# -- Core throttling behavior -------------------------------------------------


def test_requests_under_limit_pass_through(fake_redis, fake_logger, fake_stats):
    app = _RecordingApp()
    for _ in range(3):
        send = _run(_http_scope(), app)
        assert send.status is None  # app never sent a response itself
    assert app.calls == 3


def test_request_over_limit_returns_429_with_retry_after(
    fake_redis, fake_logger, fake_stats
):
    app = _RecordingApp()
    for _ in range(3):
        _run(_http_scope(), app)
    send = _run(_http_scope(), app)

    assert send.status == 429
    assert b"retry-after" in send.headers
    assert app.calls == 3  # downstream app never ran for the rejected request


def test_over_limit_emits_rejected_invocation_and_metric(
    fake_redis, fake_logger, fake_stats
):
    app = _RecordingApp()
    for _ in range(4):
        _run(_http_scope(), app)

    assert len(fake_logger.calls) == 1
    envelope = fake_logger.calls[0]["event_data"]
    assert envelope["event_type"] == "rejected_invocation"
    assert envelope["reason"] == "rate_limited"
    assert "retry_after_seconds" in envelope
    assert envelope["session_id"] == hashlib.sha256(b"some.jwt.value").hexdigest()

    keys = [key for key, _tags in fake_stats.calls]
    assert "mcp.rejected" in keys
    assert "mcp.rate_limit" in keys


def test_different_bearer_gets_independent_bucket(fake_redis, fake_logger, fake_stats):
    app = _RecordingApp()
    for _ in range(3):
        _run(_http_scope("token-a"), app)
    send = _run(_http_scope("token-b"), app)

    assert send.status is None
    assert app.calls == 4


def test_window_rollover_resets_counter(
    fake_redis, fake_logger, fake_stats, monkeypatch
):
    app = _RecordingApp()
    monkeypatch.setattr(rate_limit_module.time, "time", lambda: 0)
    for _ in range(3):
        _run(_http_scope(), app)
    send = _run(_http_scope(), app)
    assert send.status == 429

    monkeypatch.setattr(rate_limit_module.time, "time", lambda: 60)
    send = _run(_http_scope(), app)
    assert send.status is None
    assert app.calls == 4


def test_retry_after_reflects_window_boundary_not_full_window(
    fake_redis, fake_logger, fake_stats, monkeypatch
):
    """A key created late in its window must carry a TTL (and thus a
    Retry-After) that expires at the window's actual boundary -- not a fresh
    full window measured from creation. Otherwise a compliant client honoring
    Retry-After waits far longer than the real reset."""
    app = _RecordingApp()
    # All four requests land in the same 60s window ([0, 60)), but the first
    # (which creates the key) arrives with only ~1s left in that window.
    monkeypatch.setattr(rate_limit_module.time, "time", lambda: 59.0)
    for _ in range(3):
        _run(_http_scope(), app)
    monkeypatch.setattr(rate_limit_module.time, "time", lambda: 59.9)
    send = _run(_http_scope(), app)

    assert send.status == 429
    retry_after = int(dict(send.headers)[b"retry-after"])
    # Only ~100ms remains until the window's real boundary at t=60 -- not 60s.
    assert retry_after <= 2


def test_concurrent_requests_share_one_boundary(fake_redis, fake_logger, fake_stats):
    app = _RecordingApp()

    async def run_all():
        sends = [_ResponseCapture() for _ in range(6)]
        await asyncio.gather(
            *[RateLimitMiddleware(app)(_http_scope(), None, send) for send in sends]
        )
        return sends

    sends = asyncio.run(run_all())
    statuses = [s.status for s in sends]
    assert statuses.count(429) == 3
    assert statuses.count(None) == 3
    assert app.calls == 3


# -- Redis fault handling -----------------------------------------------------


class _BrokenRedis:
    async def eval(self, *args, **kwargs):
        raise ConnectionError("redis unreachable")


def test_redis_error_fails_open_and_increments_backend_error_metric(
    monkeypatch, fake_logger, fake_stats
):
    monkeypatch.setattr(rate_limit_module, "_get_redis_client", lambda: _BrokenRedis())
    app = _RecordingApp()
    send = _run(_http_scope(), app)

    assert send.status is None
    assert app.calls == 1
    keys = [key for key, _tags in fake_stats.calls]
    assert MCP_RATE_LIMIT_BACKEND_ERROR in keys


class _BrokenStats:
    def incr(self, key, tags=None):
        raise RuntimeError("stats down")


def test_redis_error_fails_open_even_when_stats_backend_also_fails(
    monkeypatch, fake_logger
):
    """Metric emission on a Redis fault must be best-effort: a broken stats
    backend must not prevent the request from failing open."""
    monkeypatch.setattr(rate_limit_module, "stats_logger", _BrokenStats())
    monkeypatch.setattr(rate_limit_module, "_get_redis_client", lambda: _BrokenRedis())
    app = _RecordingApp()
    send = _run(_http_scope(), app)

    assert send.status is None
    assert app.calls == 1


def test_backend_error_metric_carries_environment_tag(monkeypatch, fake_logger):
    capture = _StatsCapture()
    monkeypatch.setattr(rate_limit_module, "stats_logger", capture)
    monkeypatch.setattr(rate_limit_module, "_get_redis_client", lambda: _BrokenRedis())
    app = _RecordingApp()
    _run(_http_scope(), app)

    tags_by_key = dict(capture.calls)
    assert tags_by_key[MCP_RATE_LIMIT_BACKEND_ERROR] == {"environment": "test"}


# -- Disabled / pass-through ---------------------------------------------------


def test_disabled_limiter_is_pure_passthrough(monkeypatch, fake_logger, fake_stats):
    monkeypatch.setattr(
        QuerybookSettings, "MCP_RATE_LIMIT_MAX_REQUESTS", 0, raising=False
    )

    def _boom():
        raise AssertionError("Redis must not be touched when the limiter is disabled")

    monkeypatch.setattr(rate_limit_module, "_get_redis_client", _boom)
    app = _RecordingApp()

    for _ in range(5):
        send = _run(_http_scope(), app)
        assert send.status is None
    assert app.calls == 5
    assert fake_stats.calls == []


def test_non_http_scope_passes_through(monkeypatch, fake_logger, fake_stats):
    def _boom():
        raise AssertionError("Redis must not be touched for non-http scopes")

    monkeypatch.setattr(rate_limit_module, "_get_redis_client", _boom)
    app = _RecordingApp()
    asyncio.run(RateLimitMiddleware(app)({"type": "lifespan"}, None, None))
    assert app.calls == 1


def test_missing_bearer_passes_through_without_redis_call(
    monkeypatch, fake_logger, fake_stats
):
    def _boom():
        raise AssertionError("Redis must not be touched when no bearer is presented")

    monkeypatch.setattr(rate_limit_module, "_get_redis_client", _boom)
    app = _RecordingApp()
    send = _run(_http_scope(token=None), app)
    assert send.status is None
    assert app.calls == 1


def test_unauthenticated_scope_passes_through_without_redis_call(
    monkeypatch, fake_logger, fake_stats
):
    """FastMCP's own AuthenticationMiddleware always runs ahead of this
    middleware and sets scope["user"]; a request whose bearer failed that
    upstream verification must not consume a Redis round-trip here -- it's
    rejected downstream (401) exactly as it would be without this middleware."""

    def _boom():
        raise AssertionError(
            "Redis must not be touched for a request FastMCP didn't authenticate"
        )

    monkeypatch.setattr(rate_limit_module, "_get_redis_client", _boom)
    app = _RecordingApp()
    send = _run(_http_scope(authenticated=False), app)
    assert send.status is None
    assert app.calls == 1


def test_missing_user_key_passes_through_without_redis_call(
    monkeypatch, fake_logger, fake_stats
):
    """Defensive: if scope["user"] is absent entirely (e.g. no AuthProvider
    configured), treat as unauthenticated rather than erroring."""

    def _boom():
        raise AssertionError("Redis must not be touched with no scope['user']")

    monkeypatch.setattr(rate_limit_module, "_get_redis_client", _boom)
    app = _RecordingApp()
    scope = {"type": "http", "headers": _headers("some.jwt.value")}
    send = _run(scope, app)
    assert send.status is None
    assert app.calls == 1


# -- Integration: real FastMCP middleware ordering ---------------------------
#
# The unit tests above drive RateLimitMiddleware directly and can't see how it
# actually composes with FastMCP's own middleware stack. FastMCP 3.0.2
# unconditionally prepends its AuthenticationMiddleware ahead of anything
# passed via middleware=[...], so token verification always runs first --
# these tests build a real FastMCP ASGI app (mcp.http_app) with a
# call-counting verifier to prove that ordering and the resulting behavior.


def test_rate_limit_runs_after_real_fastmcp_auth_middleware(
    fake_redis, fake_logger, fake_stats, monkeypatch
):
    httpx = pytest.importorskip("httpx")
    from starlette.middleware import Middleware
    from fastmcp import FastMCP
    from fastmcp.server.auth import AccessToken, TokenVerifier

    from lib.mcp.audit import RequestAuditMiddleware

    monkeypatch.setattr(
        QuerybookSettings, "MCP_RATE_LIMIT_MAX_REQUESTS", 3, raising=False
    )

    class _CountingVerifier(TokenVerifier):
        def __init__(self):
            super().__init__()
            self.calls = 0

        async def verify_token(self, token):
            self.calls += 1
            return AccessToken(
                token=token, client_id="probe", scopes=[], expires_at=None
            )

    verifier = _CountingVerifier()
    mcp = FastMCP(name="test-rate-limit")
    mcp.auth = verifier
    app = mcp.http_app(
        middleware=[
            Middleware(RateLimitMiddleware),
            Middleware(RequestAuditMiddleware),
        ],
        stateless_http=True,
    )

    async def run():
        async with app.router.lifespan_context(app):
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                headers = {
                    "Authorization": "Bearer some-verified-token",
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                }
                body = {"jsonrpc": "2.0", "id": 1, "method": "ping"}
                statuses = []
                for _ in range(5):
                    resp = await client.post(
                        "/mcp", json=body, headers=headers, follow_redirects=True
                    )
                    statuses.append(resp.status_code)
                return statuses

    statuses = asyncio.run(run())

    # Every request -- including the ones the limiter rejects -- reached
    # FastMCP's auth backend: verification is not skipped for throttled
    # requests, proving RateLimitMiddleware runs after (not before) auth.
    assert verifier.calls == 5
    assert statuses[:3] == [200, 200, 200]
    assert statuses[3:] == [429, 429]
