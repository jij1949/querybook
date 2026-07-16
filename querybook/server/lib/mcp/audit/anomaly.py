"""Per-credential failure-burst anomaly detection for the MCP server.

A single credential producing an abnormal burst of *failure* signals --
auth failures, authz denials, or rejected invocations (oversized /
malformed / rate-limited) -- is a probing/abuse signature distinct from the
blanket request-rate limiter (which counts *all* requests and enforces a
429). This detector only counts failures and only *emits a signal*; it never
blocks, so it can never lock out a legitimate credential.

It hooks the single audit funnel (`emit_audit_event`), keying a fixed-window
Redis counter off the `session_id` (token hash) already present on every
envelope -- so it needs no client IP. When a credential crosses the
configured failure threshold within a window this returns the payload for
exactly one `anomaly` audit event (debounced to the crossing request); the
router emits it, so it routes to LOG.info + EventLog + LangSmith and drives
the `mcp.anomaly` counter via the router's single metric emitter. Returning
the payload (rather than emitting here) keeps this module free of a
back-import on the router.

Unlike the rate limiter (async, on every request), this runs synchronously
inside `emit_audit_event` and thus briefly blocks the event loop -- but only
on failure events, which are rare, and always fail-soft under a tight Redis
timeout. Enabling requires a positive `MCP_ANOMALY_FAILURE_THRESHOLD`
(0/unset disables it).
"""

import time
from typing import Optional

import redis

from env import QuerybookSettings
from lib.logger import get_logger

LOG = get_logger(__file__)

_REDIS_TIMEOUT_SECONDS = 0.25

# Atomic fixed-window counter: INCR, set the window PEXPIRE only on the key's
# creation (count == 1) so a live window's TTL is never extended, and return
# the running count in one round-trip.
_ANOMALY_LUA = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then
    redis.call('PEXPIRE', KEYS[1], ARGV[1])
end
return count
"""

_redis_client = None


def _get_redis_client():
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis.from_url(
            QuerybookSettings.REDIS_URL,
            socket_timeout=_REDIS_TIMEOUT_SECONDS,
            socket_connect_timeout=_REDIS_TIMEOUT_SECONDS,
        )
    return _redis_client


def _is_failure_signal(event_type: str, payload: dict) -> bool:
    """True for the security-failure events this detector counts.

    Deliberately excludes `tool_invocation` execution errors (a bad query is
    expected input, not a security signal) and the `anomaly` event itself (so
    the emission below can never re-trigger counting)."""
    if event_type == "authz" or event_type == "rejected_invocation":
        return True
    if event_type == "auth" and payload.get("result") == "failure":
        return True
    return False


def check_failure_burst(event_type: str, payload: dict, ctx: dict) -> Optional[dict]:
    """Count a failure event per-credential; return an `anomaly` payload on breach.

    Returns the payload for the router to emit on the request that *crosses*
    the threshold (once per window per credential), else ``None``. Fully
    fail-soft: any backend fault is logged and swallowed (returning ``None``)
    so anomaly detection never suppresses the underlying audit record -- the
    compliance artifact."""
    try:
        threshold = QuerybookSettings.MCP_ANOMALY_FAILURE_THRESHOLD
        if threshold <= 0 or not _is_failure_signal(event_type, payload):
            return None

        session_id = ctx.get("session_id")
        if not session_id:
            return None

        window_seconds = QuerybookSettings.MCP_ANOMALY_WINDOW_SECONDS
        window_ms = window_seconds * 1000
        now_ms = int(time.time() * 1000)
        window_epoch = now_ms // window_ms
        ttl_ms = max(1, window_ms - (now_ms % window_ms))
        key = f"mcp:anomaly:{session_id}:{window_epoch}"

        count = int(_get_redis_client().eval(_ANOMALY_LUA, 1, key, ttl_ms))

        # Fire exactly once per window per credential, on the crossing request.
        if count == threshold + 1:
            return {
                "reason": "failure_burst",
                "failure_count": count,
                "window_seconds": window_seconds,
                "trigger_event_type": event_type,
            }
        return None
    except Exception as e:
        LOG.info(f"MCP anomaly detection backend error: {e}")
        return None
