"""MCP Middleware: event logging, LangSmith tracing, and resource wrappers.

The middleware classes here are thin wrappers that call audit.log_mcp_event()
with the right event_type and payload. Envelope construction, routing, and
correlation live in audit.py.

NOTE: FastMCP middleware only supports tool hooks. Resource logging is handled via
a decorator pattern since on_read_resource() is not supported.
"""

import functools
import time
from contextlib import nullcontext
from datetime import date

import langsmith
from fastmcp.server.dependencies import get_access_token
from fastmcp.server.middleware import Middleware, MiddlewareContext

from env import QuerybookSettings
from lib.mcp.audit import (
    get_recorded_auth_reason,
    get_request_context,
    log_mcp_event,
)
from lib.mcp.exceptions import (
    classify_exception,
    find_authorization_error,
    to_tool_error,
)
from lib.mcp.redact import redact, redact_text

MAX_STR_PARAM_LENGTH = 128


class _NoopLangSmithRun:
    """Stand-in run for the resource wrapper when LangSmith tracing is disabled.

    Lets the ``with`` block call ``.end(...)`` unconditionally without opening a
    real LangSmith trace when ``LANGSMITH_TRACING`` is off.
    """

    def end(self, *args, **kwargs):
        pass


_AUTH_DEPRECATION_DEADLINE = date(2026, 6, 30)
_AUTH_DEPRECATION_NOTICE = (
    "**Authentication update for Querybook MCP**: the current Querybook API token / Bearer token flow "
    "will be deprecated soon (2026-06-30). Please follow the updated setup guide to migrate to Okta Auth: "
    "https://go/querybook-mcp. For support: [#eg-querybook-mcp-server-community](https://expediagroup.enterprise.slack.com/archives/C0ANE004S91). "
    "Include this notice once per conversation with the user, before presenting tool results; do not repeat it unless asked."
)


class AuthDeprecationNoticeMiddleware(Middleware):
    """Injects an auth deprecation notice into every tool call result during the migration window.

    Appended as a structured note in structured_content.notes so LLMs see it on every call
    while the "once per conversation" directive in the notice text prevents repetition.
    """

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        result = await call_next(context)
        if date.today() <= _AUTH_DEPRECATION_DEADLINE:
            token = get_access_token()
            if (
                token
                and token.claims.get("auth_method") == "api_token"
                and result.structured_content is not None
            ):
                notes = result.structured_content.get("notes", [])
                notes.append(
                    {
                        "level": "warning",
                        "code": "AUTH_DEPRECATION",
                        "message": _AUTH_DEPRECATION_NOTICE,
                    }
                )
                result.structured_content["notes"] = notes
        return result


class MCPEventLoggingMiddleware(Middleware):
    """Middleware that logs MCP tool calls to the structured audit envelope."""

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        start_time = time.perf_counter()
        tool_name = context.message.name
        # Auth success has no standalone record — it rides on this event.
        auth_reason = get_recorded_auth_reason()

        try:
            result = await call_next(context)
            duration_ms = (time.perf_counter() - start_time) * 1000

            log_mcp_event(
                "tool_invocation",
                {
                    "tool": tool_name,
                    "status": "success",
                    "auth_reason": auth_reason,
                    "duration_ms": round(duration_ms, 2),
                    "parameters": redact(
                        context.message.arguments, max_len=MAX_STR_PARAM_LENGTH
                    ),
                },
            )
            return result

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            authz_error = find_authorization_error(e)

            if authz_error is not None:
                # An authorization denial is the request's single record: the
                # tool never ran, so no tool_invocation is emitted. The
                # AuthorizationError raised at the user_can_* gate carries the
                # action/resource (the client sees only the generic message
                # ExceptionMappingMiddleware maps it to). emit_langsmith is False
                # because the outer LangSmithTracingMiddleware already opened this
                # request's one rich trace and ends it with the error — a
                # lightweight run would duplicate it.
                log_mcp_event(
                    "authz",
                    {
                        "tool": tool_name,
                        "result": "deny",
                        "authz_denied_resource": authz_error.resource,
                        "authz_denied_action": authz_error.action,
                        "authz_reason": f"no_{authz_error.action}_permission",
                        "auth_reason": auth_reason,
                        "duration_ms": round(duration_ms, 2),
                    },
                    emit_langsmith=False,
                )
            else:
                log_mcp_event(
                    "tool_invocation",
                    {
                        "tool": tool_name,
                        "status": "error",
                        "auth_reason": auth_reason,
                        "error": redact_text(str(e), max_len=MAX_STR_PARAM_LENGTH),
                        "duration_ms": round(duration_ms, 2),
                        "parameters": redact(
                            context.message.arguments, max_len=MAX_STR_PARAM_LENGTH
                        ),
                    },
                )
            raise


class LangSmithTracingMiddleware(Middleware):
    """Middleware that traces MCP tool calls in LangSmith."""

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        # Gate on the same flag the audit router honors so LangSmith stays fully
        # inert (no trace, no egress) when tracing is disabled.
        if not QuerybookSettings.LANGSMITH_TRACING:
            return await call_next(context)

        tool_name = context.message.name
        ctx = get_request_context()

        # Sync ``with`` (not ``async with``) to match the resource wrapper and
        # audit/langsmith.py: run setup/teardown are synchronous and only
        # ``call_next`` is awaited, so this stays consistent and works across the
        # whole ``langsmith>=0.2.0`` range (async CM support on ``trace`` is newer).
        with langsmith.trace(
            name=f"mcp.tool.{tool_name}",
            run_type="tool",
            inputs={"arguments": redact(context.message.arguments)},
            metadata={**ctx, "operation_type": "tool", "tool": tool_name},
            tags=["mcp", "querybook", "tool"],
        ) as run:
            try:
                result = await call_next(context)
                outputs = (
                    redact(result.structured_content)
                    if result.structured_content is not None
                    else {"status": "success"}
                )
                run.end(outputs=outputs)
                return result
            except Exception as e:
                run.end(error=redact_text(str(e)))
                raise


class ExceptionMappingMiddleware(Middleware):
    """Maps raw domain exceptions raised by tools to client-facing ToolErrors.

    Registered innermost (last ``add_middleware`` call) so it sees a tool's raw
    exception before the logging/tracing middlewares, keeping their logs and the
    client message consistent. See ``lib.mcp.exceptions.to_tool_error``.
    """

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        try:
            return await call_next(context)
        except Exception as e:
            mapped = to_tool_error(e)
            if mapped is not None:
                raise mapped from e
            raise


def wrap_mcp_resources(mcp):
    """Wrap FastMCP's resource decorator to add logging.

    FastMCP middleware doesn't support resource hooks, so we monkey-patch
    the resource decorator to automatically add logging to all resources.

    Args:
        mcp: FastMCP instance to wrap

    Returns:
        The same FastMCP instance with wrapped resource decorator
    """
    original_resource = mcp.resource

    def logging_resource(*decorator_args, **decorator_kwargs):
        """Wrapped resource decorator that adds logging."""

        def decorator(func):
            """Actual decorator applied to resource functions."""

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                ctx = get_request_context()
                # Auth success has no standalone record — it rides on this event
                # (mirrors the tool path in MCPEventLoggingMiddleware).
                auth_reason = get_recorded_auth_reason()

                resource_uri = decorator_kwargs.get(
                    "uri", f"{func.__module__}.{func.__name__}"
                )
                for key, value in kwargs.items():
                    placeholder = f"{{{key}}}"
                    if placeholder in resource_uri:
                        resource_uri = resource_uri.replace(placeholder, str(value))
                resource_uri = resource_uri.split("{?")[0]

                # Gate on the same flag the audit router honors so LangSmith
                # stays fully inert (no trace, no egress) when tracing is off.
                trace_ctx = (
                    langsmith.trace(
                        name="mcp.resource.read",
                        run_type="tool",
                        inputs={"uri": resource_uri},
                        metadata={
                            **ctx,
                            "operation_type": "resource",
                            "resource_uri": resource_uri,
                        },
                        tags=["mcp", "querybook", "resource"],
                    )
                    if QuerybookSettings.LANGSMITH_TRACING
                    else nullcontext(_NoopLangSmithRun())
                )
                with trace_ctx as ls_run:
                    try:
                        result = func(*args, **kwargs)
                        duration_ms = (time.perf_counter() - start_time) * 1000

                        log_mcp_event(
                            "resource_read",
                            {
                                "resource_uri": resource_uri,
                                "status": "success",
                                "auth_reason": auth_reason,
                                "duration_ms": round(duration_ms, 2),
                            },
                        )
                        ls_run.end(outputs={"status": "success"})
                        return result

                    except Exception as e:
                        duration_ms = (time.perf_counter() - start_time) * 1000

                        # One walk of the cause chain yields both the client
                        # message and the authz classification (see
                        # classify_exception). Map first so the event log and
                        # LangSmith run record the same client-facing message the
                        # caller receives — mirroring the tool path, where the
                        # innermost ExceptionMappingMiddleware maps the raw
                        # exception before the logging/tracing middlewares see it.
                        mapped, authz_error = classify_exception(e)
                        error_message = str(mapped) if mapped is not None else str(e)

                        if authz_error is not None:
                            # Mirror the tool path: an authz denial is the
                            # request's single `authz` deny record (no
                            # resource_read). The lightweight run is suppressed
                            # because this wrapper's own trace (ls_run, ended
                            # below) is the one LangSmith record for the read.
                            log_mcp_event(
                                "authz",
                                {
                                    "resource_uri": resource_uri,
                                    "result": "deny",
                                    "authz_denied_resource": authz_error.resource,
                                    "authz_denied_action": authz_error.action,
                                    "authz_reason": (
                                        f"no_{authz_error.action}_permission"
                                    ),
                                    "auth_reason": auth_reason,
                                    "duration_ms": round(duration_ms, 2),
                                },
                                emit_langsmith=False,
                            )
                        else:
                            log_mcp_event(
                                "resource_read",
                                {
                                    "resource_uri": resource_uri,
                                    "status": "error",
                                    "auth_reason": auth_reason,
                                    "error": redact_text(
                                        error_message, max_len=MAX_STR_PARAM_LENGTH
                                    ),
                                    "duration_ms": round(duration_ms, 2),
                                },
                            )
                        ls_run.end(error=redact_text(error_message))
                        if mapped is not None:
                            raise mapped from e
                        raise

            return original_resource(*decorator_args, **decorator_kwargs)(wrapper)

        return decorator

    mcp.resource = logging_resource
    return mcp
