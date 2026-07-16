# MCP Security Standard Implementation

How the Querybook MCP server implements the EG **16.02 MCP Security Standard
(MCPSS)**. This is the single authoritative description of what exists in this
repo. Sections follow the standard's
control domains, but this is a design document, not a control-by-control
compliance matrix.

Tracking: [EGANP-5964](https://expediagroup.atlassian.net/browse/EGANP-5964)
(epic) / [EGANP-5970](https://expediagroup.atlassian.net/browse/EGANP-5970)
(audit & monitoring). See [`mcp.md`](./mcp.md) for the MCP server's functional
design (tools/resources model, how to add them).

> **Approach and sign-off.** The implementation is deliberately KISS /
> best-effort: where the standard's letter would add complexity without real
> security value, we adopt a documented pragmatic interpretation instead. Those
> interpretations are recorded in [Design decisions](#design-decisions--accepted-interpretations).

> **Where things live.** The MCP server is Python/FastMCP:
> `querybook/server/run_mcp.py` (entry point), `querybook/server/lib/mcp/`
> (implementation), with the audit layer in `lib/mcp/audit/` and
> `lib/mcp/middleware.py`. Tests: `querybook/tests/test_lib/test_mcp/`.
> This repo is the EG fork; RCP deploy manifests, Vault wiring, and Datadog
> monitor definitions live in a separate EG-internal infra repo.

## Deployment context (platform facts the design relies on)

-   Deployed on **RCP** (internal Kubernetes). Container **stdout is forwarded to
    Splunk by the platform** — guaranteed, no in-app shipper needed.
-   **Splunk retention is ~7–10 days**: an operational search window, not an
    audit store.
-   **LangSmith** is the AI observability platform; projects are configured for
    **400-day retention**, which satisfies the ≥12-month audit-retention
    requirement. Neither Splunk nor LangSmith give end users the ability to
    tamper with or delete recorded data — both are treated as write-once storage.
-   **TLS termination and ingress control** are handled by platform
    ingress/gateway, not the app.
-   **Datadog monitors are defined externally** (infra repo / Datadog directly),
    never in this repo. The app's job is to emit the metrics.

---

## Server registration & deployment (MCPSS-1)

The server runs as a container on RCP (EG-managed infrastructure), never on
user endpoints. Registration in the MCP Registry and Backstage is an external,
per-deployment action — not repo content. The tool catalog the registration
needs is machine-readable from this repo: every tool carries MCP behavioral
annotations (`READ_ONLY` / `WRITE` / `CREATE` / `DELETE`,
`lib/mcp/utils.py`), and the startup `config_snapshot` audit event records the
exact tool/resource surface each pod actually serves.

## Authentication (MCPSS-2)

Auth mode is selected at startup by `MCP_AUTH_MODE` (`run_mcp.py:49-87`):

| Mode    | Provider                                     | Behavior                                                                                                                                                                                                       |
| ------- | -------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `token` | `QuerybookTokenVerifier` (`lib/mcp/auth.py`) | Legacy Querybook API key as bearer. SHA-512 hash looked up in `api_access_token` (enabled rows only). No expiry — enable/disable in DB.                                                                        |
| `oauth` | `OktaOIDCProvider` (`lib/mcp/okta_auth.py`)  | OAuth 2.0 / OIDC via Okta (FastMCP `OIDCProxy`). Scopes `openid email profile offline_access`, `verify_id_token=True`, consent required, client redirect URIs allowlisted (`MCP_OAUTH_ALLOWED_REDIRECT_URIS`). |
| `dual`  | `OktaOIDCProvider(allow_api_tokens=True)`    | OAuth, with API tokens still accepted (32-hex-char shape detection) — the migration mode.                                                                                                                      |

-   **No anonymous access**: every request terminates in a token verifier;
    failures produce a 401 (and an `auth` audit event — see MCPSS-8).
-   **Token verification** (signature, `aud`/`iss`/`exp`) is delegated to
    FastMCP's `OIDCProxy` / JWT verifier — not re-implemented here. Okta access
    tokens are short-lived (~60 min, an Okta-side IdP setting; not enforced in
    this repo).
-   The authenticated user (`creator_uid`) is resolved from the verified token's
    claims — OAuth mode maps `preferred_username` to a Querybook user
    (auto-creating on first login). Callers never pass an identity.
-   **Secrets** (`MCP_AUTH_SECRET`, `OAUTH_CLIENT_ID/SECRET`) arrive as
    Vault-injected env vars (`containers/start-with-vault.sh`); the config
    snapshot logs their presence as booleans, never values. OAuth client state in
    Redis is Fernet-encrypted; JWT signing and storage keys are HKDF-derived from
    `MCP_AUTH_SECRET` with distinct salts.
-   `AuthDeprecationNoticeMiddleware` (`middleware.py`) nudges legacy API-token
    callers toward Okta OAuth (stated deadline 2026-06-30). Non-expiring API
    tokens remain a [known gap](#known-gaps) until token mode is retired.

## Least privilege & authorization (MCPSS-3)

Authorization is enforced **server-side, inside every tool/resource handler**,
against the identity derived from the verified token:

-   Every tool and resource takes `token: AccessToken = CurrentAccessToken()`
    and derives `uid = token.claims["creator_uid"]` (verified across all modules;
    the only exceptions are identity-independent directory lookups and the static
    guide/reference resources).
-   Handlers call the same permission helpers as the REST API
    (`user_can_read` / `user_can_write`, environment-permission checks, etc.);
    a failed check raises `AuthorizationError(action, resource)`
    (`lib/mcp/exceptions.py`) — deny-by-default at the data level.
-   Denies are audited centrally (see [Authorization decisions](#authorization-decisions)).
-   Sharing tools (`add_datadoc_editor` / `update_datadoc_editor`) grant explicit
    read/write/execute rather than all-or-nothing.
-   **Human-in-the-loop for destructive ops** is delegated to the MCP client via
    the standard annotation mechanism: destructive tools carry
    `DELETE_ANNOTATIONS` (`destructiveHint`), which conformant clients use to
    gate on user approval. The server cannot render an approval UI; this is the
    standard MCP division of responsibility.

## Transport & network (MCPSS-4, MCPSS-5)

-   Transport is **streamable HTTP** with `stateless_http=True` (horizontal
    scaling; no server-side session state), binding `0.0.0.0:$MCP_PORT`
    (`run_mcp.py:148-166`).
-   **TLS, ingress restriction, and network segmentation are platform concerns**:
    the app serves plain HTTP behind RCP ingress / the MCP Gateway, which
    terminate TLS and control exposure. Nothing in-repo to do.
-   **Per-credential rate limiting (MCPSS-5.3)** is implemented in-app at the
    ASGI layer (`lib/mcp/audit/rate_limit.py`), returning a real **HTTP 429 +
    `Retry-After`** (a FastMCP tool-middleware `ToolError` would surface as HTTP
    200, which defeats client backoff):
    -   Keyed per credential: SHA-256 of the bearer token (same derivation as the
        audit layer's `session_id`). Blanket per-credential — deliberately not
        per-tool and not parsing the JSON-RPC body; the goal is server resource
        protection, so total request rate is the right signal.
    -   Atomic fixed window via one Redis Lua `EVAL` (INCR + PEXPIRE-on-create +
        PTTL, one round trip), key `mcp:ratelimit:{token_hash}:{window_epoch}`.
        Shared Redis counter is safe across replicas.
    -   Async Redis (`redis.asyncio`) with 250 ms socket timeouts plus
        `asyncio.wait_for` — a slow Redis cannot stall requests. **Fail-open**,
        unconditionally (fault → allow + `mcp.rate_limit.backend_error` metric).
        Matches the audit layer's fail-open contract; failing closed on a Redis
        blip would take down every MCP tool call, so there's no configurable
        fail-closed mode.
    -   Runs after FastMCP's auth middleware (the SDK always prepends it), so only
        authenticated requests are counted; and **before** `RequestAuditMiddleware`
        so a 429 is not mis-recorded as an auth event. A throttled request emits
        one `rejected_invocation{reason=rate_limited}` audit record.
    -   **Ships disabled** (`MCP_RATE_LIMIT_MAX_REQUESTS=0`); enable per
        environment via Vault. The EG MCP Gateway (Cequence) may also provide rate
        limiting at the ingress tier — having the in-app limiter means 5.3 is
        satisfiable either way, and stacking is a per-environment enablement
        decision, not a code change.

## Input validation & output handling (MCPSS-6)

Inputs are validated server-side in three layers; each rejection produces
exactly one `rejected_invocation` audit record:

1. **Oversized inputs** — `PayloadSizeGuardMiddleware` (`middleware.py`),
   registered **outermost** so a breach is rejected before a LangSmith trace
   opens or the tool body runs. Sums UTF-8 **bytes** over string leaves _and
   dict keys_ of the tool arguments using an iterative (stack-based) traversal
   with short-circuit — deep nesting can't blow the Python stack. Cap:
   `MCP_MAX_FREETEXT_INPUT_BYTES` (default 1 MiB; `0` disables). Breach →
   `rejected_invocation{reason=oversized}` + generic `ToolError`.
2. **Malformed parameters** — FastMCP/Pydantic schema validation. Uncoercible
   or missing args raise `ValidationError`, detected in the event-logging
   middleware's except path via `find_validation_error` (walks the exception
   `__cause__` chain) → `rejected_invocation{reason=malformed_params}`.
   `strict_input_validation=False` is pinned on `FastMCP(...)` so a future
   library default flip can't move validation below the middleware where this
   branch couldn't see it.
3. **Domain validation** — per-tool checks (e.g. `limit` caps with
   `ValueError`) inside handlers.

Raw transport body limits (HTTP 413) are a Gateway / RCP-ingress concern, not
in-app — the guard protects tool execution, which is the part this repo owns.

On the output side, tool results and error strings are **redacted before every
audit sink** (see [Sensitive-field handling](#sensitive-field-handling)), and
`ExceptionMappingMiddleware` (innermost) maps raw domain exceptions to curated
`ToolError`s so internals don't leak to clients. A content-inspection /
prompt-injection scanning layer over tool outputs is **not** implemented — see
[Design decisions](#design-decisions--accepted-interpretations).

## Server integrity & supply chain (MCPSS-7)

-   Base image from the internal Artifactory mirror
    (`artifactory-edge.expedia.biz/public-docker-virtual/python:3.10-bookworm`),
    not Docker Hub.
-   **SAST**: GitHub Advanced Security CodeQL (`.github/workflows/codeql-analysis.yaml`)
    for Python and JS/TS — PRs to master, pushes, weekly cron, `security-extended`
    query pack.
-   Config is version-controlled; deployment is IaC (helm/k8s in-repo plus the
    RCP manifests in the infra repo).
-   Tool descriptions are static Python decorators — no dynamic runtime
    modification of the tool catalog.
-   Container hardening (non-root user, read-only rootfs) and dependency/SCA
    scanning are **not** in place — see [Known gaps](#known-gaps).

## Audit logging & monitoring (MCPSS-8)

The audit layer is the largest piece of MCPSS work in this repo. One curated
audit record per request, fanned out to three sinks by a single router
(`emit_audit_event`, `lib/mcp/audit/router.py`):

| Sink                              | Role                                                                                                                                                | Gate                          |
| --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------- |
| **LangSmith**                     | **The forensic audit store** — rich trace per tool/resource execution, lightweight run per security event. 400-day retention, externally immutable. | `LANGSMITH_TRACING`           |
| **EventLog** (MySQL)              | In-app operational mirror, one row per event. 7-day purge (`tasks/db_clean_up_jobs.py`) — not the compliance store.                                 | `EVENT_LOGGER_NAME != "null"` |
| **App log (`LOG.info`) → Splunk** | The security-signal subset in `key=value` form for SecOps search. **Unconditional** — no config can silence it. Platform forwards stdout to Splunk. | none                          |

Datadog counters are derived from the same envelope (see
[Metrics](#metrics-and-alerting)). Sinks are **fail-soft, never fail-closed**:
a sink outage degrades retention but never blocks an operation or suppresses
the other sinks, and the startup `config_snapshot` makes each pod's sink
posture auditable after the fact.

### Core invariant

**One audited request → at most one EventLog row and at most one LangSmith
record** (a rich trace _or_ a lightweight run, never both). The `event_type` is
a classification of that single record, not a license to emit several. The one
deliberate exception is the pattern-scoped `anomaly` event
([below](#anomaly-detection)), which is owned by a window, not a request.

**Curation over completeness**: security-irrelevant protocol chatter (`ping`,
`tools/list`, `initialize`, no-token discovery probes) is discarded — no row,
no trace. Every failure is captured; success is captured for every
tool/resource operation.

### Event envelope

`get_request_context()` (`lib/mcp/audit/context.py`) supplies correlation
fields; the router adds `event_type` and a UTC ISO-8601 `timestamp`:

-   `request_id` — UUID per request, set by the ASGI `RequestAuditMiddleware`
    into a `ContextVar`.
-   `session_id` — SHA-256 of the presented bearer (or a `session_id` claim).
    Under `stateless_http` the bearer is the only stable per-credential
    correlator; since Okta tokens are short-TTL its hash approximates a session.
    The raw token is never logged. `session_kind="access_token"` when derived.
-   `subject` (uid), `client_id`, `auth_method` — from the verified token claims.
-   `environment` — from `ENVIRONMENT` (falls back to `DD_ENV`, then the
    `PRODUCTION` flag).

Payload fields vary by type: `tool` / `resource_uri` / `resource_template`,
`status`, `result`, `duration_ms`, `parameters`, `error`, `auth_reason`,
`reason`, and deny fields (`authz_denied_resource`, `authz_denied_action`,
`authz_reason`).

### Event types and routing

`_ALWAYS_LOG = {authz, rejected_invocation, anomaly, config_snapshot}`;
LOG.info additionally gets any event with `status=error` or an `auth` failure.
LangSmith gets a lightweight run for events outside
`_RICH_TRACE_EVENTS = {tool_invocation, resource_read}` (those carry their own
rich trace), excluding routine `no_token` and `emit_langsmith=False` calls.

| Event                                                                                             | LOG.info | EventLog |         LangSmith         |
| ------------------------------------------------------------------------------------------------- | :------: | :------: | :-----------------------: |
| `tool_invocation` / `resource_read` success                                                       |    —     |    ✅    |       ✅ rich trace       |
| `tool_invocation` / `resource_read` error                                                         |    ✅    |    ✅    |       ✅ rich trace       |
| `auth` failure                                                                                    |    ✅    |    ✅    |    ✅ lightweight run     |
| `auth` token issuance/refresh (success / failure)                                                 |  — / ✅  |    ✅    |    ✅ lightweight run     |
| `no_token` (routine discovery probe)                                                              |    —     |    ✅    |             —             |
| `authz` deny                                                                                      |    ✅    |    ✅    | (rides on the rich trace) |
| `rejected_invocation` (`oversized`, `malformed_params`, `rate_limited`; `write_blocked` reserved) |    ✅    |    ✅    |   ✅ / rides on trace †   |
| `anomaly` (`failure_burst`)                                                                       |    ✅    |    ✅    |    ✅ lightweight run     |
| `config_snapshot` (startup)                                                                       |    ✅    |    ✅    |    ✅ lightweight run     |

> † `malformed_params` and `authz` denies occur _inside_ the tracing
> middleware, whose rich trace (ended with the error) is already the request's
> one LangSmith record — so they pass `emit_langsmith=False` to suppress a
> duplicate lightweight run. `oversized` and `rate_limited` fire before any
> trace opens and get the lightweight run.

### Auth outcome model

Auth-event emission is unified at the request boundary. Verifiers only
**record facts** to a request-scoped `ContextVar`
(`record_auth_success` / `record_auth_failure` / `record_token_issuance`,
`lib/mcp/audit/auth.py`); the ASGI `RequestAuditMiddleware` flushes in a
`finally` block:

1. A recorded **standalone** outcome (failure, token issuance/refresh) → one
   `auth` event.
2. Else a 401 **with** a bearer → `auth` failure,
   `auth_reason=unclassified_token_rejection` (a presented-but-unrecorded
   bearer is a rejected credential, not a probe).
3. Else a 401 with **no** bearer → `no_token` (EventLog-only).
4. A recorded login **success** emits nothing at the boundary — it rides on the
   `tool_invocation` event as `auth_reason` (a per-call auth-success row would
   drown the signal).

`auth_reason` vocabulary: `valid_api_token`, `invalid_api_token`,
`api_token_not_allowed`, `valid_oauth_token`, `invalid_oauth_token`,
`oauth_missing_username`, `unclassified_token_rejection`, `token_issued`,
`token_issuance_failed`, `token_refreshed`, `token_refresh_failed`.

Token rejections are **never downgraded to "expired"**: the provider does not
decode the unverified JWT's `exp` — a forged token could carry an old `exp`
and launder itself from security signal into benign churn.

### Authorization decisions

Denies are structured signals, not call-site logging: permission gates raise
`AuthorizationError(action, resource)`, and the deny event is emitted
**centrally** — `MCPEventLoggingMiddleware` (tools) / the resource wrapper
walk the exception `__cause__` chain (`find_authorization_error`; FastMCP
re-raises handler exceptions as `ToolError ... from cause`) and emit the
request's single `authz` event (`result=deny`,
`authz_reason=no_<action>_permission`) instead of a `tool_invocation`. A
successful invocation is implicitly the allow; only denies are events.

### Sensitive-field handling

`lib/mcp/redact.py` scrubs tool inputs, outputs, and error strings **before
every sink**. Governing principle: **precision over recall** — over-redaction
corrupts the audit trail (and logged SQL) worse than an occasional miss, so
every pattern is anchored and biased to high confidence, with the residual
documented:

| Pattern                     | Guard against false positives                                                                                                 |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| Payment card (13–19 digits) | **Luhn checksum gate** — long IDs pass through                                                                                |
| Email                       | standard form, TLD required                                                                                                   |
| JWT / `Bearer <token>`      | distinctive structure                                                                                                         |
| Key/value secrets           | fires on **key name** only (`password`, `token`, `api_key`, `client_secret`, … — segment-aware suffix match), not value shape |
| SSN                         | dashed form only — bare 9-digit runs collide with IDs                                                                         |
| Phone                       | formatted / `+country` forms only — bare 10-digit runs collide with IDs                                                       |
| IPv4/IPv6                   | **off by default** (`include_ip`)                                                                                             |

Matches become typed placeholders (`[REDACTED:email]`, `[REDACTED:secret]`, …)
so surrounding SQL stays readable. A positive+negative test corpus
(`test_audit_redact.py`) — realistic SQL with IDs, UUIDs, versions, literals
that must pass untouched — is the safeguard against precision regressions.

Capping (`MAX_STR_PARAM_LENGTH = 128`) is applied _after_ redaction per string
leaf (truncation can never split a match and leak the tail): EventLog and
LOG.info payloads are capped; **LangSmith inputs/outputs are redacted but
uncapped** — the forensic trail keeps full values. Accepted residuals:
bare-digit SSN/phone, IPs (off by default), free-form names/addresses,
Luhn-failing digit runs, and resource URIs (identifier paths, not free text).

### Config snapshot

At startup each pod emits a `config_snapshot` event (8.4) recording the
security posture it actually booted with
(`lib/mcp/audit/config_snapshot.py`): auth mode, oauth/oidc-configured
booleans (never secret values), redirect-URI count, rate-limit and
anomaly-detection settings, `max_freetext_input_bytes`,
`strict_input_validation`, the full sorted tool/resource surface, sink
selection (`event_logger_name`, `stats_logger_name`, `langsmith_tracing`), and
query-result size limits. Config _changes_ are deploys — a new snapshot per
pod start, diffable across restarts.

### Metrics and alerting

All counters are emitted from **one place** — `_emit_metric()` in the router,
driven off the audit envelope (call sites must not increment them; verified
single-emitter). Fail-soft, after the sinks, so a stats fault never suppresses
the audit record. No-op unless `STATS_LOGGER_NAME=datadog`.

| Envelope                            | Counter (tags)                                     |
| ----------------------------------- | -------------------------------------------------- |
| `tool_invocation` / `resource_read` | `mcp.tool.call` (`surface`, `tool`, `environment`) |
| … with `status=error`               | + `mcp.tool.error`                                 |
| `auth` failure                      | `mcp.auth.failure`                                 |
| `authz` deny                        | `mcp.authz.deny` (`tool`)                          |
| `rejected_invocation`               | `mcp.rejected` (`reason`)                          |
| … with `reason=rate_limited`        | + `mcp.rate_limit`                                 |
| `anomaly`                           | `mcp.anomaly` (`reason`)                           |
| _(direct — no envelope exists)_     | `mcp.rate_limit.backend_error`                     |

The resource-side `tool` tag uses the registered URI **template** (bounded
cardinality), never the resolved URI. Monitors over these metrics (auth-failure
rate, rejection rate, anomaly) are defined externally — not repo content.

### Anomaly detection

Per-credential **failure-burst** detection (`lib/mcp/audit/anomaly.py`), hooked
into the single audit funnel so every security signal passes through it:

-   Counts only failure signals — `authz` denies, `rejected_invocation` (any
    reason), `auth` failures — in a Redis fixed window keyed by `session_id`
    (`mcp:anomaly:{session_id}:{window_epoch}`). Tool execution _errors_ are
    deliberately not counted (a bad query is expected input, not a security
    signal), and `anomaly` itself is excluded so it can't self-trigger.
-   **Detection-only, debounced**: fires exactly one `anomaly` event
    (`reason=failure_burst`, `failure_count`, `window_seconds`,
    `trigger_event_type`) when a credential _crosses_ the threshold
    (`count == threshold + 1`), once per window — it never blocks, so it can
    never lock out a legitimate credential.
-   Synchronous but fail-soft under a 250 ms Redis timeout; runs only on rare
    failure events. Ships disabled (`MCP_ANOMALY_FAILURE_THRESHOLD=0`).
-   This is a request-rate-independent complement to the blanket rate limiter
    (which counts _all_ requests and enforces), and gives the per-credential
    signal Datadog can't produce without high-cardinality tags.
-   The event does not materialize contributing `request_id`s; an investigator
    pivots on `session_id` + window in LangSmith/EventLog, where every
    contributing failure already has its own record. (A capped contributing-refs
    list was considered and deferred as extra Redis state without proportionate
    value.)

### Retention

| Store               | Retention                                       | Role                                                               |
| ------------------- | ----------------------------------------------- | ------------------------------------------------------------------ |
| LangSmith           | **400 days** (project setting, per environment) | The ≥12-month audit store; also "readily available" (queryable UI) |
| Splunk (via stdout) | ~7–10 days (platform)                           | Operational search / SecOps alerting window                        |
| EventLog (MySQL)    | 7-day purge                                     | In-product convenience only                                        |

### Tamper resistance

No in-process cryptographic hash chain — a chain the same process both writes
and vouches for adds negligible tamper resistance. The standard's text is
"cryptographic hashing **or** write-once storage"; we satisfy it with the
latter: the forensic trail lives in LangSmith (and the operational copy in
Splunk), external systems in which end users cannot modify or delete recorded
data. Accepted design decision — see
[Design decisions](#design-decisions--accepted-interpretations).

## Data handling & privacy (MCPSS-9)

-   **Data minimization**: the curated tool surface returns serialized summaries
    with `resource_uri` pointers rather than bulk data; list/history tools carry
    hard result caps (e.g. `list_query_executions` caps `limit` at 100); query
    result reads are bounded by the platform limits recorded in the config
    snapshot (`db_max_upload_size`, `store_max_read_size`,
    `table_max_upload_rows`). The audit discard policy (no blanket
    protocol-chatter logging) is itself a data-minimization measure.
-   PII/secrets are redacted before any log sink (above).
-   **Session lifetime**: `stateless_http=True` means there is no server-side
    session to bound; effective session length is the bearer's validity — ~60 min
    for Okta access tokens (IdP-side). Legacy API tokens have no expiry (known
    gap, resolved by retiring token mode).

## Secure development (MCPSS-10)

-   **Curated tool surface, not raw CRUD**: 9 tool modules + read-only resources,
    a deliberately smaller surface than the Flask REST API, each tool
    hand-designed (see `mcp.md`). Destructive tools are individually
    permission-gated and annotated `DELETE`.
-   CodeQL SAST in CI (security-extended, weekly + per-PR).
-   OWASP-relevant hygiene is structural: parameterized ORM access via the shared
    `logic/` layer, typed exception mapping so internals don't reach clients,
    server-side validation everywhere.
-   Dependency scanning and DAST are **not** in-repo — see
    [Known gaps](#known-gaps).

## Configuration reference

Defined in `env.py`, defaulted in `querybook_default_config.yaml`,
positive-int validated, recorded in the startup config snapshot. Enforcement
features **ship disabled** so merging is inert; enable per environment via
Vault.

| Variable                                                                                 | Default                               | Meaning                                                           |
| ---------------------------------------------------------------------------------------- | ------------------------------------- | ----------------------------------------------------------------- |
| `MCP_AUTH_MODE`                                                                          | `token`                               | `token` / `oauth` / `dual`                                        |
| `MCP_AUTH_SECRET`, `MCP_OIDC_CONFIG_URL`, `MCP_OAUTH_BASE_URL`, `OAUTH_CLIENT_ID/SECRET` | —                                     | Required for `oauth`/`dual` (Vault)                               |
| `MCP_OAUTH_ALLOWED_REDIRECT_URIS`                                                        | —                                     | Client redirect allowlist                                         |
| `MCP_RATE_LIMIT_MAX_REQUESTS`                                                            | `0` (off)                             | Per-credential requests/window                                    |
| `MCP_RATE_LIMIT_WINDOW_SECONDS`                                                          | `60`                                  | Rate-limit window                                                 |
| `MCP_MAX_FREETEXT_INPUT_BYTES`                                                           | `1048576` (1 MiB)                     | Free-text tool-arg cap; `0` = off                                 |
| `MCP_ANOMALY_FAILURE_THRESHOLD`                                                          | `0` (off)                             | Failures/window before an `anomaly` fires                         |
| `MCP_ANOMALY_WINDOW_SECONDS`                                                             | `300`                                 | Anomaly window                                                    |
| `LANGSMITH_TRACING` / `LANGSMITH_API_KEY` / `LANGSMITH_PROJECT`                          | off / — / —                           | Forensic trail (400-day retention is a LangSmith project setting) |
| `EVENT_LOGGER_NAME`                                                                      | `null`                                | EventLog backend (`db`/`console`/`null`)                          |
| `STATS_LOGGER_NAME`                                                                      | `null`                                | `datadog` enables DogStatsD counters                              |
| `ENVIRONMENT`                                                                            | `DD_ENV` → `production`/`development` | Environment tag on every envelope                                 |

The security-signal LOG.info path is **unconditional** — no combination of
these settings can silence it.

## Implementation map

| Component                                                                                                         | Location                                                    |
| ----------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| Entry point: auth-mode selection, middleware registration, transport                                              | `run_mcp.py`                                                |
| Envelope, sink routing, single metric emitter, anomaly wiring                                                     | `lib/mcp/audit/router.py`                                   |
| Request boundary (request_id, auth flush) + outcome recorders                                                     | `lib/mcp/audit/auth.py`                                     |
| Correlation context (`request_id`, `session_id`)                                                                  | `lib/mcp/audit/context.py`                                  |
| Rate limiter (ASGI, Lua fixed window)                                                                             | `lib/mcp/audit/rate_limit.py`                               |
| Failure-burst anomaly detector                                                                                    | `lib/mcp/audit/anomaly.py`                                  |
| Startup config snapshot                                                                                           | `lib/mcp/audit/config_snapshot.py`                          |
| LangSmith lightweight-run adapter                                                                                 | `lib/mcp/audit/langsmith.py`                                |
| Redaction                                                                                                         | `lib/mcp/redact.py`                                         |
| Tool middleware (payload guard, tracing, event logging, deprecation notice, exception mapping) + resource wrapper | `lib/mcp/middleware.py`                                     |
| Typed authz/validation errors + cause-chain walkers                                                               | `lib/mcp/exceptions.py`                                     |
| Token verifiers (pure recorders)                                                                                  | `lib/mcp/auth.py`, `lib/mcp/okta_auth.py`                   |
| Metric-name constants                                                                                             | `lib/stats_logger/__init__.py`                              |
| EventLog store + 7-day purge                                                                                      | `lib/event_logger/__init__.py`, `tasks/db_clean_up_jobs.py` |
| Tests (redaction corpus, routing, rate limit, anomaly, okta, tracing)                                             | `querybook/tests/test_lib/test_mcp/`                        |

Tool-path middleware order (outermost → innermost, registration order in
`run_mcp.py`): `PayloadSizeGuard` → `LangSmithTracing` → `MCPEventLogging` →
`AuthDeprecationNotice` → `ExceptionMapping`. ASGI order: FastMCP auth
(SDK-prepended) → `RateLimit` → `RequestAudit`.

## Design decisions & accepted interpretations

Pragmatic interpretations of the standard, adopted deliberately and signed off
by the project owner (senior engineer). These are decisions, not gaps.

1. **Audit integrity via write-once storage, no hash chain (8.5).** An
   in-process hash chain the emitting process itself maintains is security
   theater. LangSmith (400-day) and Splunk are external stores end users cannot
   tamper with or delete from — the standard's "write-once storage" branch.
2. **Splunk gets the security subset, not every tool call (8.1).** The full
   per-call trail lives in LangSmith; shipping every invocation to a 7–10-day
   operational store adds ingest cost, not audit value. Splunk delivery itself
   is the platform's guaranteed stdout forwarding — no in-app shipper.
3. **Successful auth on tool-less requests is discarded (8.2).** Every auth
   _failure_ is captured; success is captured on every tool/resource event
   (`auth_reason`). Blanket-logging protocol re-auth would drown the signal and
   conflicts with data minimization.
4. **Anomaly record is the simple `failure_burst` variant.** One combined
   failure counter, no per-type split, no materialized contributing
   `request_id`s — investigators pivot on `session_id` + window in
   LangSmith/EventLog. Richer materialization is possible later if incident
   response actually needs it.
5. **No prompt-injection / content-inspection heuristic on tool I/O (6.3/6.4).**
   SQL is _expected_ input for this server, so instruction-pattern heuristics
   fire on normal use; and payloads are redacted + truncated before any sink,
   so there is no in-app data path to inspect. Output-side content inspection
   belongs at the MCP Gateway / client tier if required.
6. **Rate limiting ships disabled; gateway may own it (5.3).** The in-app
   limiter exists and is production-ready; whether to enable it per environment
   (vs. relying on the EG Gateway) is an ops decision, not code.
7. **`write_blocked` stays a reserved, inert rejection reason.** It implies a
   read-only server mode; most tools here are intentionally mutating, and no
   MCPSS control requires such a mode.
8. **Datadog monitors are defined externally.** The app emits metrics; monitor
   definitions were never going to live in this repo. Not a gap.
9. **HITL for destructive ops is the MCP client's job (3.x).** Communicated
   via standard `destructiveHint` annotations; a server cannot render approval
   UI in the MCP architecture.

## Known gaps

Genuine gaps as of this document (verified against code, not just docs):

| #   | Gap                                                                                      | MCPSS                    | Notes / path to close                                                                                                                                                                     |
| --- | ---------------------------------------------------------------------------------------- | ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Legacy API tokens never expire                                                           | 2 (no long-lived tokens) | Deprecation notice in place (deadline 2026-06-30 has passed); close by moving deployments to `oauth` mode and retiring `token`/`dual`.                                                    |
| 2   | Container runs as root; no read-only rootfs / securityContext in-repo                    | 7 (container hardening)  | No `USER` in Dockerfile; RCP-side pod security may mitigate — verify in infra repo, add `USER` regardless.                                                                                |
| 3   | No dependency/SCA scanning in CI                                                         | 10.3                     | CodeQL SAST only; no Dependabot/pip-audit/Snyk.                                                                                                                                           |
| 4   | Image provenance/signing disabled (`provenance: false` in `docker.yml`); no IaC scanning | 7                        | Low-effort CI additions.                                                                                                                                                                  |
| 5   | No DAST in-repo                                                                          | 10.4                     | Presumed org-level; confirm coverage of the MCP endpoint.                                                                                                                                 |
| 6   | Enforcement ships disabled                                                               | 5.3 / 8.5                | Rate limiting and anomaly detection are built but off by default; enabling per environment (Vault) is an open infra-repo action, as is Datadog monitor creation over the emitted metrics. |
| 7   | Async LangSmith-middleware tests inert in CI                                             | — (test hygiene)         | `pytest-asyncio` not installed, so `@pytest.mark.asyncio` tests in `test_langsmith_tracing.py` don't run. Add the dev dependency.                                                         |
| 8   | MCP Registry registration                                                                | 1                        | External per-deployment action; not repo content but listed for completeness.                                                                                                             |
