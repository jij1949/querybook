import sys
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Stub fastmcp so middleware.py can be imported without installing the package.
_fastmcp = ModuleType("fastmcp")
_fastmcp_server = ModuleType("fastmcp.server")
_fastmcp_server_deps = ModuleType("fastmcp.server.dependencies")
_fastmcp_server_deps.get_access_token = MagicMock(return_value=None)
_fastmcp_server_middleware = ModuleType("fastmcp.server.middleware")
_fastmcp_server_middleware.Middleware = object
_fastmcp_server_middleware.MiddlewareContext = MagicMock

sys.modules.setdefault("fastmcp", _fastmcp)
sys.modules.setdefault("fastmcp.server", _fastmcp_server)
sys.modules.setdefault("fastmcp.server.dependencies", _fastmcp_server_deps)
sys.modules.setdefault("fastmcp.server.middleware", _fastmcp_server_middleware)

# Stub env before anything else — prevents env.py from triggering the full
# server config import chain.
_env = ModuleType("env")
_env.QuerybookSettings = MagicMock(
    EVENT_LOGGER_NAME="null",
    ENVIRONMENT="test",
)
sys.modules.setdefault("env", _env)

# Stub other Querybook server modules that middleware.py and audit.py import.
for _mod in (
    "const",
    "const.event_log",
    "lib.event_logger",
    "lib.logger",
):
    sys.modules.setdefault(_mod, ModuleType(_mod))

_const_event_log = sys.modules["const.event_log"]
if not hasattr(_const_event_log, "EventType"):
    _const_event_log.EventType = MagicMock()

_event_logger_mod = sys.modules["lib.event_logger"]
if not hasattr(_event_logger_mod, "event_logger"):
    _event_logger_mod.event_logger = MagicMock()

_lib_logger_mod = sys.modules["lib.logger"]
if not hasattr(_lib_logger_mod, "get_logger"):
    _lib_logger_mod.get_logger = MagicMock(return_value=MagicMock())


def test_langsmith_tracing_middleware_exists():
    """LangSmithTracingMiddleware must be importable from middleware module."""
    from lib.mcp.middleware import LangSmithTracingMiddleware

    assert LangSmithTracingMiddleware is not None


@pytest.mark.asyncio
async def test_langsmith_tracing_middleware_traces_tool_call():
    """on_call_tool wraps the call in a langsmith.trace context."""
    from lib.mcp.middleware import LangSmithTracingMiddleware

    middleware = LangSmithTracingMiddleware()

    # Build a minimal MiddlewareContext-like mock
    context = MagicMock()
    context.message.name = "list_environments"
    context.message.arguments = {"environment_id": 1}

    # No structured_content -> the middleware records the {"status": "success"}
    # placeholder outputs rather than a redacted payload.
    tool_result = MagicMock()
    tool_result.structured_content = None
    call_next = AsyncMock(return_value=tool_result)

    # langsmith.trace is entered with a sync ``with`` (see middleware.py).
    mock_run = MagicMock()
    mock_run.__enter__ = MagicMock(return_value=mock_run)
    mock_run.__exit__ = MagicMock(return_value=False)

    # Pin the correlation context so the assertion is independent of the
    # ambient environment (ENVIRONMENT, etc.) leaking from a real settings load.
    fixed_ctx = {
        "request_id": "unknown",
        "subject": 0,
        "client_id": None,
        "auth_method": "unknown",
        "session_id": None,
        "session_kind": None,
        "environment": "test",
    }

    with patch("lib.mcp.middleware.langsmith") as mock_ls, patch(
        "lib.mcp.middleware.get_access_token", return_value=None
    ), patch("lib.mcp.middleware.get_request_context", return_value=fixed_ctx), patch(
        "lib.mcp.middleware.QuerybookSettings.LANGSMITH_TRACING", True
    ):
        mock_ls.trace.return_value = mock_run

        await middleware.on_call_tool(context, call_next)

        mock_ls.trace.assert_called_once_with(
            name="mcp.tool.list_environments",
            run_type="tool",
            inputs={"arguments": {"environment_id": 1}},
            metadata={
                **fixed_ctx,
                "operation_type": "tool",
                "tool": "list_environments",
            },
            tags=["mcp", "querybook", "tool"],
        )
        mock_run.end.assert_called_once_with(outputs={"status": "success"})
        call_next.assert_awaited_once_with(context)


@pytest.mark.asyncio
async def test_langsmith_tracing_middleware_records_error():
    """on_call_tool ends the run with error= when call_next raises."""
    from lib.mcp.middleware import LangSmithTracingMiddleware

    middleware = LangSmithTracingMiddleware()

    context = MagicMock()
    context.message.name = "get_datadoc"
    context.message.arguments = {}

    call_next = AsyncMock(side_effect=RuntimeError("boom"))

    # langsmith.trace is entered with a sync ``with`` (see middleware.py).
    mock_run = MagicMock()
    mock_run.__enter__ = MagicMock(return_value=mock_run)
    mock_run.__exit__ = MagicMock(return_value=False)

    with patch("lib.mcp.middleware.langsmith") as mock_ls, patch(
        "lib.mcp.middleware.get_access_token", return_value=None
    ), patch("lib.mcp.middleware.QuerybookSettings.LANGSMITH_TRACING", True):
        mock_ls.trace.return_value = mock_run

        with pytest.raises(RuntimeError, match="boom"):
            await middleware.on_call_tool(context, call_next)

        mock_run.end.assert_called_once_with(error="boom")


def test_wrap_mcp_resources_adds_langsmith_trace():
    """wrap_mcp_resources must call langsmith.trace for each resource read."""
    from lib.mcp.middleware import wrap_mcp_resources

    # Build a minimal mcp mock whose .resource is a pass-through decorator factory
    mcp = MagicMock()

    def fake_resource(*args, **kwargs):
        # Simulates the original mcp.resource: returns a decorator that returns the func unchanged
        def decorator(func):
            return func

        return decorator

    mcp.resource = fake_resource

    # wrap_mcp_resources replaces mcp.resource with a wrapped version
    wrap_mcp_resources(mcp)

    # After wrapping, mcp.resource is now the logging_resource wrapper
    wrapped_decorator = mcp.resource(uri="querybook://environment/{env_id}")

    mock_func = MagicMock(return_value="result")
    mock_func.__module__ = "test"
    mock_func.__name__ = "get_env"
    # wrapped_decorator(mock_func) goes through: logging_resource -> decorator -> wrapper
    # wrapper calls func(*args, **kwargs) inside langsmith.trace context
    wrapped_func = wrapped_decorator(mock_func)

    mock_run = MagicMock()
    mock_run.__enter__ = MagicMock(return_value=mock_run)
    mock_run.__exit__ = MagicMock(return_value=False)

    with patch("lib.mcp.middleware.langsmith") as mock_ls, patch(
        "lib.mcp.middleware.log_mcp_event"
    ), patch("lib.mcp.middleware.QuerybookSettings.LANGSMITH_TRACING", True):
        mock_ls.trace.return_value = mock_run

        wrapped_func(env_id=42)

        mock_ls.trace.assert_called_once()
        call_kwargs = mock_ls.trace.call_args
        assert call_kwargs.kwargs.get("run_type") == "tool"
        assert call_kwargs.kwargs["name"] == "mcp.resource.read"
        assert call_kwargs.kwargs["metadata"]["operation_type"] == "resource"
        assert (
            call_kwargs.kwargs["metadata"]["resource_uri"]
            == "querybook://environment/42"
        )
        assert call_kwargs.kwargs["tags"] == ["mcp", "querybook", "resource"]
        mock_run.end.assert_called_once_with(outputs={"status": "success"})


def test_wrap_mcp_resources_records_error_in_langsmith():
    """wrap_mcp_resources calls ls_run.end(error=...) when the resource function raises."""
    from lib.mcp.middleware import wrap_mcp_resources

    mcp = MagicMock()

    def fake_resource(*args, **kwargs):
        def decorator(func):
            return func

        return decorator

    mcp.resource = fake_resource
    wrap_mcp_resources(mcp)

    wrapped_decorator = mcp.resource(uri="querybook://datadoc/{datadoc_id}")

    mock_func = MagicMock(side_effect=RuntimeError("not found"))
    mock_func.__module__ = "test"
    mock_func.__name__ = "get_datadoc"
    wrapped_func = wrapped_decorator(mock_func)

    mock_run = MagicMock()
    mock_run.__enter__ = MagicMock(return_value=mock_run)
    mock_run.__exit__ = MagicMock(return_value=False)

    with patch("lib.mcp.middleware.langsmith") as mock_ls, patch(
        "lib.mcp.middleware.log_mcp_event"
    ), patch("lib.mcp.middleware.QuerybookSettings.LANGSMITH_TRACING", True):
        mock_ls.trace.return_value = mock_run

        with pytest.raises(RuntimeError, match="not found"):
            wrapped_func(datadoc_id=99)

        mock_run.end.assert_called_once_with(error="not found")


def test_wrap_mcp_resources_skips_trace_when_disabled():
    """No LangSmith trace is opened when LANGSMITH_TRACING is off, but the
    audit event is still logged."""
    from env import QuerybookSettings
    from lib.mcp.middleware import wrap_mcp_resources

    mcp = MagicMock()

    def fake_resource(*args, **kwargs):
        def decorator(func):
            return func

        return decorator

    mcp.resource = fake_resource
    wrap_mcp_resources(mcp)

    wrapped_decorator = mcp.resource(uri="querybook://environment/{env_id}")

    mock_func = MagicMock(return_value="result")
    mock_func.__module__ = "test"
    mock_func.__name__ = "get_env"
    wrapped_func = wrapped_decorator(mock_func)

    with patch("lib.mcp.middleware.langsmith") as mock_ls, patch(
        "lib.mcp.middleware.log_mcp_event"
    ) as mock_log, patch.object(QuerybookSettings, "LANGSMITH_TRACING", False):
        assert wrapped_func(env_id=42) == "result"

        mock_ls.trace.assert_not_called()
        mock_log.assert_called_once()
