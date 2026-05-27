"""MCP Event Logging Middleware and Decorators

Tracks all MCP tool calls and resource reads using Querybook's existing EventLog system.
Uses a dedicated EventType.MCP for clean semantic separation from REST API events.

NOTE: FastMCP middleware only supports tool hooks. Resource logging is handled via
a decorator pattern since on_read_resource() is not supported.
"""

import functools
import time
from datetime import date

import langsmith
from fastmcp.server.dependencies import get_access_token
from fastmcp.server.middleware import Middleware, MiddlewareContext

from const.event_log import EventType
from lib.event_logger import event_logger
from lib.logger import get_logger

LOG = get_logger(__file__)


def _get_user_id_from_token() -> int:
    """Extract user ID from the current request's access token."""
    try:
        token = get_access_token()
        if token:
            return token.claims.get("creator_uid", 0)
    except Exception as e:
        LOG.warning(f"Failed to extract user ID from MCP context: {e}")
    return 0


# Maximum length for string parameters (same as BaseEventLogger)
MAX_STR_PARAM_LENGTH = 128

_AUTH_DEPRECATION_DEADLINE = date(2026, 6, 30)
_AUTH_DEPRECATION_NOTICE = (
    "**Authentication update for Querybook MCP**: the current Querybook API token / Bearer token flow "
    "will be deprecated soon (2026-06-30). Please follow the updated setup guide to migrate to Okta Auth: "
    "https://go/querybook-mcp. For support: [#eg-querybook-mcp-server-community](https://expediagroup.enterprise.slack.com/archives/C0ANE004S91). "
    "Include this notice once per conversation with the user, before presenting tool results; do not repeat it unless asked."
)


class AuthDeprecationNoticeMiddleware(Middleware):
    """Surfaces an auth deprecation notice during the migration window.

    Two injection points:
    - on_list_tools: prepends notice to every tool description (picked up at session start)
    - on_call_tool: appends notice as a structured note in structured_content (picked up per call)
    """

    async def on_list_tools(self, context: MiddlewareContext, call_next):
        tools = await call_next(context)
        if date.today() <= _AUTH_DEPRECATION_DEADLINE:
            for tool in tools:
                tool.description = f"{_AUTH_DEPRECATION_NOTICE}\n\n" + (
                    tool.description or ""
                )
        return tools

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        result = await call_next(context)
        if (
            date.today() <= _AUTH_DEPRECATION_DEADLINE
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
    """Middleware that logs MCP tool calls and resource reads to Querybook's event log."""

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        """Log MCP tool calls with timing and parameters.

        Args:
            context: FastMCP middleware context containing tool name and arguments
            call_next: Next middleware/handler in the chain

        Returns:
            Tool execution result

        Raises:
            Exception: Re-raises any exceptions after logging them
        """
        start_time = time.perf_counter()
        tool_name = context.message.name
        user_id = self._get_user_id(context)
        auth_method = self._get_auth_method()

        try:
            result = await call_next(context)
            duration_ms = (time.perf_counter() - start_time) * 1000

            _log_mcp_event(
                user_id=user_id,
                event_data={
                    "operation_type": "tool",
                    "tool": tool_name,
                    "auth_method": auth_method,
                    "status": "success",
                    "duration_ms": round(duration_ms, 2),
                    "parameters": self._sanitize_params(context.message.arguments),
                },
            )
            return result

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000

            _log_mcp_event(
                user_id=user_id,
                event_data={
                    "operation_type": "tool",
                    "tool": tool_name,
                    "auth_method": auth_method,
                    "status": "error",
                    "error": str(e)[:MAX_STR_PARAM_LENGTH],
                    "duration_ms": round(duration_ms, 2),
                    "parameters": self._sanitize_params(context.message.arguments),
                },
            )
            raise

    def _get_user_id(self, context: MiddlewareContext) -> int:
        return _get_user_id_from_token()

    def _get_auth_method(self) -> str:
        try:
            token = get_access_token()
            if token:
                return token.claims.get("auth_method", "unknown")
        except Exception:
            pass
        return "unknown"

    def _sanitize_params(self, params: dict) -> dict:
        """Sanitize parameters by trimming long strings.

        Recursively processes nested dictionaries and trims strings longer than
        MAX_STR_PARAM_LENGTH to prevent logging large payloads.

        Args:
            params: Dictionary of parameters to sanitize

        Returns:
            New dictionary with sanitized parameters
        """
        if not isinstance(params, dict):
            return params

        sanitized = {}
        for key, value in params.items():
            if isinstance(value, str) and len(value) > MAX_STR_PARAM_LENGTH:
                sanitized[key] = value[:MAX_STR_PARAM_LENGTH] + "..."
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_params(value)
            elif isinstance(value, list):
                sanitized[key] = self._sanitize_list(value)
            else:
                sanitized[key] = value

        return sanitized

    def _sanitize_list(self, items: list) -> list:
        """Sanitize list items recursively.

        Args:
            items: List to sanitize

        Returns:
            New list with sanitized items
        """
        sanitized = []
        for item in items:
            if isinstance(item, str) and len(item) > MAX_STR_PARAM_LENGTH:
                sanitized.append(item[:MAX_STR_PARAM_LENGTH] + "...")
            elif isinstance(item, dict):
                sanitized.append(self._sanitize_params(item))
            elif isinstance(item, list):
                sanitized.append(self._sanitize_list(item))
            else:
                sanitized.append(item)

        return sanitized


class LangSmithTracingMiddleware(Middleware):
    """Middleware that traces MCP tool calls in LangSmith."""

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        tool_name = context.message.name
        user_id = _get_user_id_from_token()

        async with langsmith.trace(
            name=tool_name,
            run_type="tool",
            inputs={"arguments": context.message.arguments},
            metadata={"user_id": user_id},
            tags=["mcp", "querybook"],
        ) as run:
            try:
                result = await call_next(context)
                outputs = result.structured_content if result.structured_content is not None else {"status": "success"}
                run.end(outputs=outputs)
                return result
            except Exception as e:
                run.end(error=str(e))
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

                # Extract user ID from token
                token = None
                for arg in args:
                    if (
                        hasattr(arg, "__class__")
                        and arg.__class__.__name__ == "AccessToken"
                    ):
                        token = arg
                        break
                if not token:
                    token = kwargs.get("token")

                user_id = 0
                auth_method = "unknown"
                if token and hasattr(token, "claims"):
                    user_id = token.claims.get("creator_uid", 0)
                    auth_method = token.claims.get("auth_method", "unknown")

                # Extract resource URI from decorator kwargs if available
                resource_uri = decorator_kwargs.get(
                    "uri", f"{func.__module__}.{func.__name__}"
                )

                # Substitute parameters in URI template (e.g., {datadoc_id})
                for key, value in kwargs.items():
                    placeholder = f"{{{key}}}"
                    if placeholder in resource_uri:
                        resource_uri = resource_uri.replace(placeholder, str(value))

                # Remove query string template from URI
                resource_uri = resource_uri.split("{?")[0]

                with langsmith.trace(
                    name=resource_uri,
                    run_type="tool",
                    inputs={"uri": resource_uri, "user_id": user_id},
                    tags=["mcp", "querybook"],
                ) as ls_run:
                    try:
                        result = func(*args, **kwargs)
                        duration_ms = (time.perf_counter() - start_time) * 1000

                        _log_mcp_event(
                            user_id=user_id,
                            event_data={
                                "operation_type": "resource",
                                "resource_uri": resource_uri,
                                "auth_method": auth_method,
                                "status": "success",
                                "duration_ms": round(duration_ms, 2),
                            },
                        )
                        ls_run.end(outputs={"status": "success"})
                        return result

                    except Exception as e:
                        duration_ms = (time.perf_counter() - start_time) * 1000

                        _log_mcp_event(
                            user_id=user_id,
                            event_data={
                                "operation_type": "resource",
                                "resource_uri": resource_uri,
                                "auth_method": auth_method,
                                "status": "error",
                                "error": str(e)[:MAX_STR_PARAM_LENGTH],
                                "duration_ms": round(duration_ms, 2),
                            },
                        )
                        ls_run.end(error=str(e))
                        raise

            # Apply original resource decorator to wrapped function
            return original_resource(*decorator_args, **decorator_kwargs)(wrapper)

        return decorator

    # Replace mcp.resource with our wrapped version
    mcp.resource = logging_resource
    return mcp


def _log_mcp_event(user_id: int, event_data: dict) -> None:
    """Log MCP event using EventLogger singleton.

    Wraps event_logger.log() with additional error handling to prevent
    logging failures from interrupting MCP operations.

    Args:
        user_id: ID of the user performing the action
        event_data: Event data dictionary
    """
    try:
        # Note: event_logger.log() normally gets user_id from current_user (Flask context)
        # but in MCP we don't have Flask context, so we need to pass uid directly
        # to the underlying logger. Since event_logger.log() doesn't accept uid parameter,
        # we call the underlying logger directly.
        event_logger.logger.log(
            uid=user_id,
            event_type=EventType.MCP,
            event_data=event_data,
        )
    except Exception as e:
        # Log error but don't interrupt MCP operation
        LOG.error(f"Failed to log MCP event: {e}", exc_info=True)
