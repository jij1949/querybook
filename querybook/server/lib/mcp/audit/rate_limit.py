"""Per-credential Redis fixed-window rate limiting for the MCP server.

Pure-ASGI middleware enforced ahead of every tool/resource handler, so a
breach yields a real HTTP 429 + Retry-After instead of a FastMCP ToolError
(which the pinned FastMCP 3.0.2 would return as HTTP 200
CallToolResult{isError: true}).

Note: under FastMCP 3.0.2, the SDK unconditionally prepends its own auth
middleware (AuthenticationMiddleware + AuthContextMiddleware, from
AuthProvider.get_middleware()) ahead of anything passed via mcp.run(...,
middleware=[...]) -- so this middleware cannot run before token
verification. It instead gates on the already-verified scope["user"] set by
that upstream AuthenticationMiddleware, and only rate-limits authenticated
requests. An unauthenticated/invalid bearer is passed straight through with
no Redis call -- it is rejected downstream (401) exactly as it would be
without this middleware. This still fully covers the threat model this
phase targets (a valid credential-holder flooding the server); throttling
floods of invalid/rotating credentials is a separate, smaller concern.
"""

import asyncio
import hashlib
import time
import uuid

from redis.asyncio import Redis
from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send

from env import QuerybookSettings
from lib.logger import get_logger
from lib.mcp.audit.router import emit_audit_event
from lib.stats_logger import MCP_RATE_LIMIT_BACKEND_ERROR, stats_logger

LOG = get_logger(__file__)

_REDIS_TIMEOUT_SECONDS = 0.25

# Atomic fixed-window counter: INCR, set the window's PEXPIRE only on the
# key's creation (count == 1) so a live window's TTL is never extended by
# subsequent requests, and return {count, pttl} in one round-trip.
_RATE_LIMIT_LUA = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then
    redis.call('PEXPIRE', KEYS[1], ARGV[1])
end
local pttl = redis.call('PTTL', KEYS[1])
return {count, pttl}
"""

_redis_client: Redis | None = None


def _get_redis_client() -> Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(
            QuerybookSettings.REDIS_URL,
            socket_timeout=_REDIS_TIMEOUT_SECONDS,
            socket_connect_timeout=_REDIS_TIMEOUT_SECONDS,
        )
    return _redis_client


def _extract_bearer(scope: Scope) -> str | None:
    """Return the raw bearer token from the ASGI scope, or None."""
    for name, value in scope.get("headers", []):
        if name == b"authorization" and value[:7].lower() == b"bearer ":
            return value[7:].decode("latin-1")
    return None


def _is_authenticated(scope: Scope) -> bool:
    """True if FastMCP's upstream AuthenticationMiddleware verified a token
    for this request (sets scope["user"] before this middleware runs)."""
    user = scope.get("user")
    return bool(user is not None and getattr(user, "is_authenticated", False))


def _rate_limit_context(token_hash: str) -> dict:
    return {
        "request_id": uuid.uuid4().hex,
        "subject": 0,
        "client_id": None,
        "auth_method": "unknown",
        "session_id": token_hash,
        "session_kind": "access_token",
        "environment": QuerybookSettings.ENVIRONMENT,
    }


def _emit_rate_limited(token_hash: str, retry_after_seconds: int) -> None:
    emit_audit_event(
        "rejected_invocation",
        {"reason": "rate_limited", "retry_after_seconds": retry_after_seconds},
        _rate_limit_context(token_hash),
    )


async def _send_429(
    scope: Scope, receive: Receive, send: Send, retry_after_seconds: int
) -> None:
    response = Response(
        status_code=429,
        headers={"Retry-After": str(retry_after_seconds)},
    )
    await response(scope, receive, send)


class RateLimitMiddleware:
    """Pure-ASGI per-credential fixed-window rate limiter.

    Registered ahead of RequestAuditMiddleware in the user-supplied
    middleware list so a rejected request never reaches RequestAuditMiddleware
    and gets mis-emitted as an auth/no_token event. It still runs after
    FastMCP's own AuthenticationMiddleware (the SDK always puts that first),
    so it only rate-limits requests that already carry a verified credential
    -- see the module docstring.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        max_requests = QuerybookSettings.MCP_RATE_LIMIT_MAX_REQUESTS
        if max_requests <= 0:
            await self.app(scope, receive, send)
            return

        if not _is_authenticated(scope):
            await self.app(scope, receive, send)
            return

        token = _extract_bearer(scope)
        if token is None:
            await self.app(scope, receive, send)
            return

        token_hash = hashlib.sha256(token.encode()).hexdigest()
        window_seconds = QuerybookSettings.MCP_RATE_LIMIT_WINDOW_SECONDS
        window_ms = window_seconds * 1000
        now_ms = int(time.time() * 1000)
        window_epoch = now_ms // window_ms
        # TTL to the window's boundary, not a fresh full window from creation --
        # otherwise a key created late in its window would carry a TTL (and
        # thus a Retry-After) that outlives the window's actual reset, telling
        # a compliant client to wait far longer than necessary.
        ttl_ms = max(1, window_ms - (now_ms % window_ms))
        key = f"mcp:ratelimit:{token_hash}:{window_epoch}"

        try:
            client = _get_redis_client()
            count, pttl = await asyncio.wait_for(
                client.eval(_RATE_LIMIT_LUA, 1, key, ttl_ms),
                timeout=_REDIS_TIMEOUT_SECONDS,
            )
        except Exception as e:
            LOG.info(f"MCP rate limit backend error, key={key}: {e}")
            try:
                stats_logger.incr(
                    MCP_RATE_LIMIT_BACKEND_ERROR,
                    tags={"environment": QuerybookSettings.ENVIRONMENT},
                )
            except Exception:
                LOG.error(
                    "Failed to emit MCP rate limit backend error metric", exc_info=True
                )
            await self.app(scope, receive, send)
            return

        if count <= max_requests:
            await self.app(scope, receive, send)
            return

        retry_after_seconds = max(1, -(-int(pttl) // 1000))  # ceil(pttl / 1000)
        _emit_rate_limited(token_hash, retry_after_seconds)
        await _send_429(scope, receive, send, retry_after_seconds)
