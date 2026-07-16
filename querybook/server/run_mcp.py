import base64
from pathlib import Path

from mcp.types import Icon
from fastmcp import FastMCP
from starlette.middleware import Middleware as StarletteMiddleware

from env import QuerybookSettings
from lib.mcp.auth import QuerybookTokenVerifier
from lib.mcp.audit import (
    RateLimitMiddleware,
    RequestAuditMiddleware,
    log_config_snapshot,
)
from lib.mcp.middleware import (
    AuthDeprecationNoticeMiddleware,
    ExceptionMappingMiddleware,
    LangSmithTracingMiddleware,
    MCPEventLoggingMiddleware,
    PayloadSizeGuardMiddleware,
    wrap_mcp_resources,
)
from lib.mcp.resources import (
    comments as comments_resources,
    datadocs as datadocs_resources,
    environments as environments_resources,
    guide as guide_resources,
    lists as lists_resources,
    reference as reference_resources,
    query_engines as query_engines_resources,
    query_executions as query_executions_resources,
    schedules as schedules_resources,
    statement_executions as statement_executions_resources,
    users as users_resources,
)
from lib.mcp.tools import (
    comments,
    datadocs,
    environments,
    github_integration,
    lists,
    query_engines,
    query_executions,
    schedules,
    users,
)


_VALID_AUTH_MODES = ("token", "oauth", "dual")


def _build_auth_provider():
    mode = (QuerybookSettings.MCP_AUTH_MODE or "token").lower().strip()
    if mode not in _VALID_AUTH_MODES:
        raise RuntimeError(
            f"Invalid MCP_AUTH_MODE={QuerybookSettings.MCP_AUTH_MODE!r}; "
            f"expected one of: {', '.join(_VALID_AUTH_MODES)}"
        )

    if mode in ("oauth", "dual"):
        missing = [
            name
            for name in (
                "MCP_AUTH_SECRET",
                "MCP_OIDC_CONFIG_URL",
                "MCP_OAUTH_BASE_URL",
                "OAUTH_CLIENT_ID",
                "OAUTH_CLIENT_SECRET",
            )
            if not getattr(QuerybookSettings, name, None)
        ]
        if missing:
            raise RuntimeError(
                f"MCP_AUTH_MODE={mode} requires these env vars: {', '.join(missing)}"
            )

        from lib.mcp.okta_auth import OktaOIDCProvider

        return OktaOIDCProvider(
            config_url=QuerybookSettings.MCP_OIDC_CONFIG_URL,
            client_id=QuerybookSettings.OAUTH_CLIENT_ID,
            client_secret=QuerybookSettings.OAUTH_CLIENT_SECRET,
            auth_secret=QuerybookSettings.MCP_AUTH_SECRET,
            base_url=QuerybookSettings.MCP_OAUTH_BASE_URL,
            allow_api_tokens=(mode == "dual"),
        )
    return QuerybookTokenVerifier()


def _build_logo_data_uri() -> str:
    svg_path = (
        Path(__file__).resolve().parent.parent / "static" / "favicon" / "querybook.svg"
    )
    svg_bytes = svg_path.read_bytes()
    b64 = base64.b64encode(svg_bytes).decode()
    return f"data:image/svg+xml;base64,{b64}"


# Querybook MCP server
mcp = FastMCP(
    "Querybook MCP",
    auth=_build_auth_provider(),
    icons=[Icon(src=_build_logo_data_uri(), mimeType="image/svg+xml")],
    # FastMCP 3.0.2 default; pinned so a future default flip can't silently
    # reject args below the middleware where the malformed_params branch (which
    # relies on the ValidationError propagating up through call_next) can't see
    # it. Inputs are coerced; uncoercible/missing args still raise ValidationError.
    strict_input_validation=False,
)

# Add tracing and event logging middleware for tools (must be registered before tools)
# PayloadSizeGuardMiddleware is registered first so it is outermost: an oversized
# call is rejected before a LangSmith trace opens and before the tool body runs.
mcp.add_middleware(PayloadSizeGuardMiddleware())
mcp.add_middleware(LangSmithTracingMiddleware())
mcp.add_middleware(MCPEventLoggingMiddleware())
mcp.add_middleware(AuthDeprecationNoticeMiddleware())
# Registered last so it is innermost — maps raw domain exceptions to ToolErrors
# before the logging/tracing middlewares observe them.
mcp.add_middleware(ExceptionMappingMiddleware())

# Wrap resource decorator to add logging (FastMCP middleware doesn't support resource hooks)
wrap_mcp_resources(mcp)

comments.register(mcp)
datadocs.register(mcp)
environments.register(mcp)
github_integration.register(mcp)
lists.register(mcp)
query_engines.register(mcp)
query_executions.register(mcp)
schedules.register(mcp)
users.register(mcp)

# Register resources
guide_resources.register(mcp)
reference_resources.register(mcp)
comments_resources.register(mcp)
datadocs_resources.register(mcp)
environments_resources.register(mcp)
lists_resources.register(mcp)
query_engines_resources.register(mcp)
query_executions_resources.register(mcp)
schedules_resources.register(mcp)
statement_executions_resources.register(mcp)
users_resources.register(mcp)

if __name__ == "__main__":
    # Audit 8.4: record the security posture the pod actually started under.
    log_config_snapshot(mcp)
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=QuerybookSettings.MCP_PORT,
        # Stateless mode used to enable horizontally-scaled deployments.
        stateless_http=True,
        # FastMCP always prepends its own auth middleware ahead of this list,
        # so RateLimitMiddleware runs after token verification (see its module
        # docstring) but must still precede RequestAuditMiddleware here, or a
        # 429'd request would reach RequestAuditMiddleware and get mis-emitted
        # as an auth/no_token event.
        middleware=[
            StarletteMiddleware(RateLimitMiddleware),
            StarletteMiddleware(RequestAuditMiddleware),
        ],
    )
