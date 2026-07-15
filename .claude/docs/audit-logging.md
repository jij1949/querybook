# MCP Audit Logging & Security Monitoring

Tracking issue: [EGANP-5970](https://expediagroup.atlassian.net/browse/EGANP-5970).
This document describes the Querybook MCP server's audit logging: how it satisfies
the **16.02 MCP Security Standard (MCPSS-8.1–8.6)**, the sinks it writes to, and the
work that remains. See [`mcp.md`](./mcp.md) for the MCP server's overall design.

> **Where things live.** The Querybook MCP server is Python/FastMCP
> (`querybook/server/run_mcp.py`, `querybook/server/lib/mcp/`). The audit
> implementation lives in the `lib/mcp/audit/` package and `lib/mcp/middleware.py`.
> This repo is the EG fork (`egdp-querybook`); the RCP/Vault deploy manifests and
> Datadog monitor definitions live in a **separate EG-internal infra repo**, not here.

## Overview

The MCP server emits one curated audit record per request across three sinks:

- **EventLog** (MySQL) — every event, at the event grain. In-app operational mirror,
  gated on `EVENT_LOGGER_NAME != "null"`.
- **LangSmith** — the long-lived forensic trail: a rich trace for tool/resource
  execution, or a lightweight metadata-only run for a non-tool security event. Gated
  on `LANGSMITH_TRACING`.
- **Application log (`LOG.info`)** — the security-signal subset (errors, authz
  denies, auth failures, rejections, anomalies, config snapshot) in human-readable
  `key=value` form. Unconditional; this is the stream a log shipper forwards to
  Splunk.

Redaction runs before **every** sink: a precision-biased regex redactor
(`lib/mcp/redact.py`) scrubs PII/secrets from tool inputs, outputs, and error strings.

Implemented: the structured envelope + routing (8.1), redaction (8.3), the startup
config snapshot (8.4), and auth/authz events (8.2/8.3). Not yet implemented: the
oversized-payload guard and schema-rejection event (Phase 6), and Datadog metrics,
rate limiting, and anomaly detection (Phase 7). See [Remaining work](#remaining-work).

Two properties shape the routing:

- **Only the security-relevant subset reaches the Splunk-bound log stream**, not every
  tool call, to control ingest cost. The full per-call trail lives in LangSmith.
- **Splunk delivery is a log-shipping concern**, not a dedicated in-app stdout JSON
  writer: security signals go to the app logger (`LOG.info`), and forwarding
  container output to Splunk is handled at the infra layer.

## Core invariant

**One audited request → at most one `EventLog` row and at most one LangSmith
record.** The LangSmith record is either a **rich trace** (tool/resource execution,
full inputs/outputs) or a **lightweight run** (a non-tool security event) — never
both, never several. A request either runs a tool/resource (→ one `tool_invocation`
/ `resource_read` event + one rich trace, with auth success riding on it), **or** it
is an auth-only / rejected request (→ one lightweight event + one lightweight run),
**or** it is discarded protocol chatter (→ nothing at all).

The `event_type` vocabulary (`tool_invocation`, `auth`, `authz`, …) is a
**classification of that single per-request record** — it is **not** a license to emit
multiple records per request. An authz denial during a tool call is the *same* record
marked
`result=deny`, not a second row.

### What we audit vs discard

We do **not** log every protocol request. We curate:

- **Audited** (one record each): tool/resource invocations, auth **failures**,
  token issuance / refresh, authz denials, and (future) rejected/oversized
  invocations and anomalies.
- **Discarded** (no record): high-frequency, security-irrelevant protocol chatter —
  `ping`, health/liveness probes, and capability discovery (`tools/list`,
  `initialize`) that carries no auth outcome. These produce neither a row nor a
  trace.

The principle is **security value, not completeness for its own sake**. If the
standard owners read MCPSS-8.2 as "log *every* successful authentication" (including
on tool-less requests), we add a deduped/sampled lightweight `auth` record for them
rather than blanket-logging the discard set — see the
[documented residual](#auth-outcome-model).

## Architecture: the sinks

| Sink | Responsibility | How data gets there |
|------|----------------|---------------------|
| **LangSmith** | **Forensic audit trail** — the full, long-lived record of tool invocations and security events, sufficient to reconstruct an agent's actions. Authoritative long-term store. | `LangSmithTracingMiddleware` (tools) and the `wrap_mcp_resources` wrapper (resources) open a rich trace per execution; the router emits a lightweight run for non-execution events (see [LangSmith tracing model](#langsmith-tracing-model)). Project retention set to **400 days** per environment (infra config). |
| **EventLog** (MySQL) | **In-app operational mirror** — one row per event, at the event grain. Convenient for in-product views; **not** the compliance store (local, 7-day retention). | `event_logger.log_mcp_event(uid, event_data)` when `EVENT_LOGGER_NAME != "null"`. |
| **Application log** (`LOG.info`) → Splunk | **Security signal** — the security-relevant subset (errors, authz denies, auth failures, rejections, anomalies, config snapshot) for SecOps search and alerting. **Not** every successful tool call. | The router writes a human-readable `key=value` line via the app logger; the platform forwards container output to Splunk (infra layer). |
| **Datadog** | **Metrics & alerting** — counters/rates and the monitors that page on anomalies. *(Not yet emitting MCP metrics — Phase 7.)* | The existing DogStatsD stats logger; monitors defined as code in the EG infra repo. |

Why LangSmith for the forensic trail and not Splunk: Splunk retention is tuned for
operational search, not multi-quarter forensic retention. LangSmith projects are
configured for 400-day retention with no user-facing delete path, which provides the
external immutability MCPSS-8.5 calls for — see [Tamper resistance](#tamper-resistance-85).

> **No fail-closed on sink availability.** A LangSmith outage degrades retention but
> does not lose the record: `EventLog` captures every event (when enabled) and the
> app log carries the security subset, so an audited operation is never executed
> wholly unlogged. Combined with the startup `config_snapshot` — which records the
> sink configuration each pod started under — a misconfiguration is auditable after
> the fact. The server therefore does **not** reject or block operations when a sink
> is unavailable; availability is monitored, not enforced inline.

### Sink routing (what goes where)

Redaction is applied before all three sinks. `emit_audit_event` in
`lib/mcp/audit/router.py` builds the envelope and fans out:

- **LOG.info** — event types in `_ALWAYS_LOG` (`{authz, rejected_invocation,
  anomaly, config_snapshot}`), any event with `status == "error"`, or an `auth`
  event with `result == "failure"`. Routine auth (`no_token`, token issuance/refresh
  success) is excluded.
- **EventLog** — every event, when `EVENT_LOGGER_NAME != "null"`.
- **LangSmith** — when `LANGSMITH_TRACING` is on, a lightweight run for any event
  **not** in `_RICH_TRACE_EVENTS` (`{tool_invocation, resource_read}`) and not a
  routine `no_token` event, provided the caller did not pass `emit_langsmith=False`.
  Rich-trace events are excluded here because the middleware/resource wrapper already
  opens a full `langsmith.trace()` around live execution — preserving the
  "at most one LangSmith record per request" invariant.

| Event | LOG.info | EventLog | LangSmith |
|-------|:---:|:---:|:---:|
| `tool_invocation` success | — | ✅ | ✅ rich trace |
| `tool_invocation` error | ✅ | ✅ | ✅ rich trace |
| `resource_read` success | — | ✅ | ✅ rich trace |
| `resource_read` error | ✅ | ✅ | ✅ rich trace |
| `auth` failure (`result=failure`) | ✅ | ✅ | ✅ lightweight run |
| `auth` token issuance/refresh success † | — | ✅ | ✅ lightweight run |
| `auth` token issuance/refresh failure † | ✅ | ✅ | ✅ lightweight run |
| `no_token` (routine discovery probe, no bearer) | — | ✅ | — |
| `authz` deny ‡ | ✅ | ✅ | (rides on the rich trace) |
| `config_snapshot` | ✅ | ✅ | ✅ lightweight run |

> **†** Auth *login* success has no row of its own — it rides on the
> `tool_invocation` event as `auth_reason`. The only standalone auth-success record
> is OAuth token issuance/refresh (the `/token` flow, which runs no tool). Reasons
> distinguish the four cases: `token_issued`, `token_issuance_failed`,
> `token_refreshed`, `token_refresh_failed`.
>
> **‡** An authz deny is emitted with `emit_langsmith=False`: the deny surfaces as an
> exception *inside* the handler, below the outer tracing middleware, which has
> already opened the request's one rich trace and ended it with the error. That rich
> trace is the single LangSmith record (it carries the attempted, redacted
> arguments), so the router suppresses the duplicate lightweight run. See
> [Authorization decisions](#authorization-decisions-83).

## Event envelope (8.1)

Every audit event carries a common envelope plus event-specific payload fields.
`get_request_context()` in `lib/mcp/audit/context.py` supplies the correlation
fields; `emit_audit_event` adds `event_type` and `timestamp`.

Envelope (correlation) fields:

- `event_type`, `timestamp` (UTC ISO-8601)
- `request_id`, `subject` (uid), `client_id`, `auth_method`
- `session_id`, `session_kind`
- `environment`

Payload fields vary by event type: `tool` / `resource_uri`, `status`, `result`,
`duration_ms`, `parameters`, `error`, `auth_reason`, and for denies
`authz_denied_resource` / `authz_denied_action` / `authz_reason`. `duration_ms` is
carried on execution events (tool/resource) and the authz deny that replaces them; it
is not a universal envelope field. LangSmith's native run duration is the timing
source for the rich trace.

Correlation IDs:

- `request_id` — a UUID (`uuid.uuid4().hex`) set per request by the ASGI
  `RequestAuditMiddleware` into a `ContextVar` (`_request_id_var`).
- `session_id` — `SHA-256` of the presented bearer token (or a `session_id` claim if
  present). Under `stateless_http=True` there is no server-side session; the bearer
  token (the **Okta access token** in OAuth mode, the Querybook API token in token
  mode) is the only stable per-credential correlator, and since Okta access tokens are
  ≤60-min TTL its hash naturally approximates a session — finer-grained than
  `subject`, which is the stable user. The raw token is **never** logged.
  `session_kind` is `"access_token"` when a `session_id` was derived, else `None`.
- `subject` / `client_id` / `auth_method` — read from `AccessToken.claims`
  (`creator_uid`, `client_id`, `auth_method`).

Event types:

- `tool_invocation` — every MCP tool call
- `resource_read` — every MCP resource read (routed like `tool_invocation`)
- `auth` — authentication validation / token issuance
- `no_token` — routine unauthenticated discovery probe (no bearer presented)
- `authz` — authorization deny decisions
- `config_snapshot` — security configuration at startup
- `rejected_invocation` — *(reserved; Phase 6)* `malformed_params`, `oversized`,
  `write_blocked`, `rate_limited`
- `anomaly` — *(reserved; Phase 7)* pattern-scoped derived signal

> `rejected_invocation` and `anomaly` appear in `_ALWAYS_LOG` and `rate_limit_enabled`
> appears in the config snapshot as inert forward-declarations — they describe the
> current posture (rate limiting off, no rejection/anomaly path yet) and are not
> active code paths.

## Sensitive-field handling (8.3)

`lib/mcp/redact.py` provides `redact(value, max_len=None)` (recurses through
dict/list structures) and `redact_text(s, include_ip=False, max_len=None)`. It scrubs
PII/secrets from tool inputs and outputs before any sink, because free-text fields —
most importantly SQL added to a DataDoc query cell and the `query` arg of
`execute_ad_hoc_query` — can carry PII in literals, and user-serialization outputs
carry emails.

### Governing principle: precision over recall

**The primary design goal is avoiding false positives.** Over-redaction silently
corrupts the audit trail and renders logged SQL unreadable — worse than an occasional
miss. Every pattern is anchored, bounded, and biased toward high-confidence matches;
we **accept lower recall** and document the residual rather than scrub aggressively.

| Pattern | Approach | False-positive guard |
|---------|----------|----------------------|
| Payment card | 13–19 digit runs | **Luhn checksum gate** so long integer IDs / order numbers are not redacted |
| Email | standard `local@domain`, TLD required | low FP risk |
| JWT / bearer | `eyJ`-prefixed 3-segment base64 / `Bearer <token>` | distinctive structure → low FP |
| Key/value secrets | match only when the **key name** signals a secret (`password`, `token`, `api_key`, `client_secret`, …), segment-aware | key-name-driven, not value-shape-driven |
| SSN | `\d{3}-\d{2}-\d{4}` **with dashes only** | do **not** match bare 9-digit runs — they collide with IDs |
| Phone | formatted / `+<country>` forms only | do **not** match bare 10-digit runs — too many collide with IDs |
| IPv4/IPv6 | **off by default** (`include_ip`) | bare IPv4 collides with version strings |

Redaction replaces the match with a typed placeholder (`[REDACTED:email]`,
`[REDACTED:card]`, `[REDACTED:secret]`, …) so surrounding SQL structure stays readable.

### Test corpus (the real safeguard)

The regexes ship with a **negative + positive corpus** in `tests/test_lib/test_mcp/`:
realistic SQL with numeric IDs, big integers, UUIDs, version numbers, identifiers,
`LIMIT`/date literals that must pass through **untouched**, plus a positive set that
must be redacted. This corpus is what prevents precision regressions.

### Wiring and capping

Redaction is wired into **all** sink call sites in `middleware.py` — tool arguments,
tool/resource results, and error strings — before LangSmith, EventLog, and LOG.info.
The `max_len` cap (`MAX_STR_PARAM_LENGTH = 128`) is **opt-in per call site**, applied
*after* redaction on each string leaf so size-bounding never truncates a value
mid-pattern and leaks the tail:

- **EventLog / LOG.info** payloads pass `max_len=128`.
- **LangSmith** inputs/outputs are redacted **uncapped** — the forensic trail keeps
  full values.

**Documented residuals** (accepted under precision-over-recall): bare-digit SSN/phone,
IP addresses (off by default), free-form names/addresses, and Luhn-failing digit runs
(all noted in `redact.py`); plus resource URIs (`resource_uri`), which are identifier
paths (the resource template with placeholders substituted), not free-text payloads,
so they are not run through the redactor.

## LangSmith tracing model

**At most one LangSmith record per MCP request.** The record is either a **rich
trace** (tool/resource execution, with full redacted inputs/outputs) or a
**lightweight metadata-only run** (a non-tool security event).

- **Every auth / authz *failure* lands in LangSmith** (as a lightweight run, or on
  the rich trace for a deny during a tool call), inheriting the 400-day retention.
- **Every *success that did something* rides on its tool/resource trace** — auth
  success is trace metadata, not a separate run.
- **Routine successful auth that runs no tool is discarded** — `ping`, `tools/list`,
  `initialize`, and the no-token discovery probe produce no LangSmith record. This
  [omits valueless protocol re-auth](#what-we-audit-vs-discard) under MCPSS-9 data
  minimization.

The mechanics:

- A tool call produces **exactly one** trace. `LangSmithTracingMiddleware.on_call_tool`
  opens a single `langsmith.trace()`; success calls `run.end(outputs=...)` and failure
  calls `run.end(error=...)` on that **same** trace. Errors attach to the trace; they
  do not spawn a new one. The resource wrapper does the same for resource reads.
- **Auth outcome rides as metadata on the tool trace**, not as a separate span. A
  successful call stays at one trace, carrying `auth_reason` / `auth_method` as metadata.
- **Non-execution security events** (auth failures, token issuance/refresh,
  config snapshot) get **one lightweight, metadata-only run** from the router
  (`lib/mcp/audit/langsmith.py`, `run_type="chain"`).
- **Duration comes from the run's native start/end.** LangSmith's intrinsic run
  duration *is* the request latency for rich traces; we do not also write a redundant
  `duration_ms` into run metadata.

## Auth outcome model

**Auth-event emission is unified at the request boundary.** Token verifiers and the
OAuth exchange methods only **record facts** to a request-scoped `ContextVar`
(`_auth_outcome_var`); the ASGI `RequestAuditMiddleware` emits the auth-only events.
The result, by construction, is **at most one audit record and at most one LangSmith
record per request**. A successful authentication does **not** emit its own `auth`
event into any sink — it would put a redundant auth-success row in front of every
tool call and drown the real `tool_invocation` events. So auth success **rides on the
tool event** that follows it as `auth_reason`.

The request flow:

1. **Request arrives.** `RequestAuditMiddleware` assigns the `request_id` and captures
   whether a bearer was presented (`_request_has_bearer`).
2. **Verifiers record facts.** `QuerybookTokenVerifier` (`auth.py`) and
   `OktaOIDCProvider` (`okta_auth.py`) describe an outcome to the request context; they
   do **not** call a sink:
   - **login success** → `record_auth_success(reason, auth_method)` — rides on the
     tool event (`standalone: false`).
   - **login failure** → `record_auth_failure(reason, auth_method)` (`standalone: true`).
   - **token issuance / refresh** → `record_token_issuance(reason, "oauth",
     success=…)` from the `exchange_authorization_code` / `exchange_refresh_token`
     overrides (`standalone: true`).
3. **Request is handled** (only if authorized). The FastMCP tool middleware emits the
   `tool_invocation` event (attaching `auth_reason`) and opens the single LangSmith
   trace.
4. **The boundary flushes** (`_flush_auth_event`):
   - if a **standalone** outcome was recorded → emit one `auth` event with its
     `result` / `auth_reason`;
   - **elif** the response was 401 and a **bearer was presented** but nothing was
     recorded → emit an `auth` failure with `auth_reason=unclassified_token_rejection`
     (a presented-but-unrecorded bearer is a rejected credential, not a no-token probe);
   - **elif** the response was 401 with **no bearer** → emit a `no_token` event (the
     routine discovery handshake, EventLog-only);
   - a recorded **login success** emits nothing here — it already rode on the tool event.

Because verifiers run in the request task **before** the boundary flushes, the recorded
values propagate to step 4 (the same mechanism as `request_id`). Emission lives in
exactly one place per request kind — tool requests at the FastMCP tool middleware,
auth-only outcomes at the boundary middleware.

### Auth failures are not classified as "expired"

All token rejections are recorded as failures and treated as security signal. The
SDK collapses every rejection cause to a bare 401, and `OktaOIDCProvider` deliberately
does **not** decode the (unverified) JWT's `exp` to downgrade a rejection to a routine
"expired" event: a forged token can carry an old `exp` and would otherwise be
laundered from a security signal into benign churn. API tokens (`QuerybookTokenVerifier`)
do not expire — they are enabled/disabled in the DB — so there is no expiry concept
there either.

### Exceptions that stay standalone (nothing to ride on)

- **Auth failures / 401s** — no tool follows; they are the security signal.
- **Token issuance / refresh** — the OAuth `/token` request runs no tool. These are
  low-volume and forensically valuable (credential lifecycle), so **both success and
  failure get a lightweight LangSmith run + EventLog row**; failure additionally →
  LOG.info. Recorded by overriding `exchange_authorization_code` /
  `exchange_refresh_token`. (Subject / client_id are not resolved on these events,
  consistent with the other standalone auth events.)

### Per-request-kind counts

| Request kind | Audit record | LangSmith |
|--------------|:---:|:---:|
| auth-ok + tool/resource | 1 (`tool_invocation` / `resource_read`) | 1 rich trace |
| auth-ok + tool/resource error | 1 | 1 rich trace |
| auth failure | 1 (`auth`) | 1 lightweight run |
| `authz` deny | 1 (`authz`) | (rides on the rich trace) |
| token issuance / refresh | 1 (`auth`) | 1 lightweight run |
| no-token discovery 401 (routine probe) | 1 (`no_token`, EventLog only) | 0 |
| auth-ok, no tool — `ping` / `tools/list` / `initialize` | 0 (discarded) | 0 |

**Documented residual (deliberate curation).** A successful request that runs *no*
tool leaves no auth record — exactly as it leaves no LangSmith trace. This is the
[discard policy](#what-we-audit-vs-discard), not an oversight. Every auth **failure**
is still captured, and success is captured for every tool/resource operation. If
MCPSS-8.2 must be read as "log *every* successful authentication," we add a
sampled/deduped lightweight `auth` record for the discard set — confirm with the
standard owners.

## Authorization decisions (8.3)

Authorization is enforced by typed exceptions, not per-call-site audit recording.
Every permission gate raises `AuthorizationError(action=…, resource=…)`
(`lib/mcp/exceptions.py`), so a deny is a structured signal travelling up the stack;
the deny event is emitted **centrally**, with zero call-site audit code.

- **deny** → `MCPEventLoggingMiddleware` (tools) and the `wrap_mcp_resources` wrapper
  (resources) call `find_authorization_error()` on the failed call's exception and, if
  found, emit the request's **single** `authz` event (`result=deny`,
  `authz_denied_resource` / `authz_denied_action` / `authz_reason =
  no_<action>_permission`); **no** `tool_invocation` / `resource_read` is emitted for
  that request.
- **allow** → has **no record of its own**. A successful `tool_invocation` /
  `resource_read` is implicitly the allow (it already proves the caller was
  authorized; the *deny* is the security-relevant event).

`find_authorization_error()` walks the exception `__cause__` chain because FastMCP
catches the handler's exception in its innermost `call_tool` layer — below all
middleware — and re-raises it as `ToolError(...) from AuthorizationError` (and
`ExceptionMappingMiddleware` maps domain exceptions to `ToolError` innermost as well).
By the time `MCPEventLoggingMiddleware` runs, the `AuthorizationError` is a
`__cause__` of the wrapper, so the helper walks the chain to find it. The outer
tracing middleware has already opened the request's one rich trace and ended it with
the error, so the `authz` deny is emitted with `emit_langsmith=False` to suppress a
duplicate lightweight run — the rich trace is the single LangSmith record, carrying
the attempted (redacted) arguments. Resources raise the `AuthorizationError` directly
(the wrapper owns their trace), so the wrapper checks the top-level exception first and
likewise suppresses the lightweight run.

## Tamper resistance (8.5)

Querybook does **not** compute an in-process cryptographic hash chain over its own
logs. A hash chain the same process both writes and vouches for adds little real
tamper resistance. Tamper resistance for the long-term trail comes from
**LangSmith's external retention and immutability**:

- the forensic trail lives in a separate system from the server that produces it;
- LangSmith projects are configured for 400-day retention with no user-facing delete
  for recorded runs.

The standard's literal text says "cryptographic hashing **or** write-once storage"; the
write-once/external-immutability reading is the one adopted here — confirm acceptance
with the standard owners.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LANGSMITH_TRACING` | `false` | Enable LangSmith tracing / forensic trail (`env.py`) |
| `LANGSMITH_API_KEY` | _(empty)_ | LangSmith API key (secret) |
| `LANGSMITH_PROJECT` | _(empty)_ | LangSmith project name (set 400-day retention on the project) |
| `STATS_LOGGER_NAME` | `null` | Set to `datadog` to enable DogStatsD metrics |
| `EVENT_LOGGER_NAME` | `null` | Selects the `EventLog` backend (`db` / `console` / `null`) |
| `ENVIRONMENT` | `DD_ENV`, else `production`/`development` | Environment tag on every envelope (falls back to `DD_ENV`, then the `PRODUCTION` flag) |

`ENVIRONMENT` is the only env var this feature added; `session_id` uses a plain
SHA-256 of the bearer token with no additional secret to manage.

> The security-signal `LOG.info` path is **unconditional** by design — it is not gated
> by `EVENT_LOGGER_NAME`, so a `null` default cannot silence security logging.
> `EVENT_LOGGER_NAME` only selects the optional `EventLog` DB/console copy, and
> `LANGSMITH_TRACING` only gates the LangSmith trail.

## Retention

- **LangSmith** — 400-day project retention satisfies the ≥12-month forensic
  requirement. A LangSmith project setting per environment, not controlled by this repo.
- **Application log → Splunk** — operational + "readily available" copy (covers the
  3-months-readily-available expectation per platform retention).
- **`EventLog` (MySQL)** — secondary/optional; default purge is 7 days
  (`tasks/db_clean_up_jobs.py`) and does not satisfy the retention requirement on its
  own.

## Compliance status vs MCPSS-8.1–8.6

| Ctrl | Requirement | Status |
|------|-------------|--------|
| **8.1** | Tool-invocation logging → centralized | **Met (app side).** Structured envelope (`request_id`, `session_id`, `subject`, `client_id`, `auth_method`, `environment`, `status`, `duration_ms`) → EventLog + LangSmith rich trace, with errors to LOG.info. Residual: no dedicated stdout→Splunk stream (infra) and no Datadog counters (Phase 7). Schema-validation rejections not yet captured (Phase 6). |
| **8.2** | Authentication events | **Met.** Auth failures, token issuance/refresh, and no-token probes emitted at the request boundary; success rides on the tool event. |
| **8.3** | Authorization events + redaction | **Met.** Authz denies emitted centrally from `AuthorizationError`; precision-biased redaction applied before every sink. |
| **8.4** | Configuration-change logging | **Met.** Startup `config_snapshot` (auth mode, oauth/oidc configured booleans, redirect-URI count, tool/resource surface, logger flags, query result limits; secrets as booleans). No configurable tool allowlist yet (tools registered explicitly in `run_mcp.py`). |
| **8.5** | Anomaly detection + audit integrity | **Partial.** Tamper resistance via LangSmith external retention (design stance, above). Anomaly detection not implemented (Phase 7). |
| **8.6** | Rejected invocations + alerting | **Not yet.** Oversized-payload guard and distinct schema-validation rejection event (Phase 6); Datadog monitors (Phase 7). |

## Current implementation map

| Component | Location |
|-----------|----------|
| Envelope + routing | `lib/mcp/audit/router.py` (`emit_audit_event`, `log_mcp_event`) |
| Request-boundary middleware + recorders | `lib/mcp/audit/auth.py` (`RequestAuditMiddleware`, `record_auth_success` / `record_auth_failure` / `record_token_issuance`) |
| Correlation context | `lib/mcp/audit/context.py` (`get_request_context`, `_request_id_var`) |
| LangSmith lightweight-run adapter | `lib/mcp/audit/langsmith.py` (`emit_langsmith_run`) |
| Startup config snapshot | `lib/mcp/audit/config_snapshot.py` (`log_config_snapshot`, called from `run_mcp.py`) |
| Redaction | `lib/mcp/redact.py` (`redact`, `redact_text`) |
| Authorization errors | `lib/mcp/exceptions.py` (`AuthorizationError`, `find_authorization_error`) |
| FastMCP middleware + resource wrapper + rich traces | `lib/mcp/middleware.py` (`MCPEventLoggingMiddleware`, `LangSmithTracingMiddleware`, `ExceptionMappingMiddleware`, `wrap_mcp_resources`) |
| Token verifiers (pure recorders) | `lib/mcp/auth.py` (`QuerybookTokenVerifier`), `lib/mcp/okta_auth.py` (`OktaOIDCProvider`) |
| EventLog store | `EventLog` model + `EventType.MCP`; `EventLogger.log_mcp_event` (`lib/event_logger/__init__.py`); 7-day purge (`tasks/db_clean_up_jobs.py`) |

## Remaining work

### Phase 6 — Rejected invocations & oversized guard (8.6)
- Add an explicit **max-size guard** on free-text tool inputs (notably the `query`
  param of `execute_ad_hoc_query`); reject oversized payloads rather than executing
  them. A 1 MiB cap on free-text inputs is the proposed starting threshold.
- Capture schema-validation rejections as a distinct `rejected_invocation` event (vs.
  runtime errors, which the middleware already logs as `status="error"`). **First
  verify empirically where FastMCP's Pydantic validation error fires** — it must be
  established whether it reaches `on_call_tool`'s try/except or upstream of it; the
  hook (FastMCP `on_message` vs. ASGI exception handler) depends on the answer.

### Phase 7 — Metrics, rate limiting, anomaly (8.5 / 8.6)
- Add MCP counters via the existing Datadog stats logger: `mcp.tool.call` (counts
  *all* invocations), `mcp.tool.error`, `mcp.auth.failure`, `mcp.rejected`,
  `mcp.rate_limit`, `mcp.authz.deny`, `mcp.anomaly`, `mcp.injection_suspect`.
- Add rate limiting on the MCP server (Flask-Limiter does not cover it). The limiter's
  mechanism — enforcement layer, key, and shared counter store — is designed
  separately; what the audit layer must account for is fixed: a throttled request
  emits a **`rejected_invocation{rate_limited}` + 429** per-request record (no tool
  execution).
- Add anomaly detection following the **pattern-scoped** model below.

#### Anomalies are pattern-scoped (design for Phase 7)

The one-record-per-request invariant governs **request-scoped** records. An `anomaly`
is the deliberate exception: it is **pattern-scoped** — a *derived* signal the detector
emits when an aggregate threshold is crossed (e.g. N rate-limit rejections, or M auth
failures, from one subject inside a window). It is owned by no single request, so it
does **not** violate the invariant: the request that tripped the threshold still emits
its own one record (e.g. a `rejected_invocation{rate_limited}`), and the `anomaly` is
an *additional, separate* record keyed by subject + window that **references** the
contributing `request_id`s.

Two rules keep this honest:

- **Materialize the investigation record.** The per-request records hold the raw facts,
  but "all the data is present" ≠ "investigable" — reconstructing an incident would
  mean re-running detection with the thresholds as they were *at the time*. So the
  materialized `anomaly` record (subject, `anomaly_type`, window, count, threshold,
  action taken, contributing refs) is written to **LangSmith + EventLog** as the
  searchable forensic anchor. Datadog carries the *alert* (`mcp.anomaly` crossing a
  monitor), not the investigation record.
- **Debounce on state transition.** Emit one `anomaly` when a subject crosses *into*
  the anomalous state — **not** one per offending request thereafter (optionally a
  clear event when it subsides). Emitting per offending request would flood the exact
  sink built for signal.

Applies to `rate_limit`, `repeated_auth_failure`, and an optional `injection_suspect`
heuristic on SQL/text inputs. The Phase 7 detector derives eligibility from
`event_type` / `result` (e.g. count `auth` events with `result=failure` per subject) —
no precomputed per-event flag is carried on records.

### Deploy / infra (separate EG-internal repo + platform)
- Confirm the platform forwards container output to Splunk.
- Set LangSmith **400-day retention** on the project per environment.
- Define Datadog monitor definitions for rate, repeated-auth-fail, injection,
  rate-limit, and write-blocked signals; apply out-of-band.
- Wire `LANGSMITH_*` / audit env vars in Vault.

## Risks & open items

- **Splunk scope (8.1 interpretation)** — routing only the security subset (not every
  tool call) to Splunk is a cost-driven interpretation of 8.1; confirm with the
  standard owners.
- **Redaction false positives** — the top risk for the redactor. Patterns are
  precision-biased and guarded by a negative test corpus; any un-redacted residual is
  documented for 8.3 sign-off.
- **`stateless_http=True`** → the SHA-256 token hash is the only session proxy; it is
  stable across replicas without additional key management.
- **Pydantic rejection capture** — verify where validation errors fire relative to
  `on_call_tool` before wiring the rejection hook (Phase 6).
