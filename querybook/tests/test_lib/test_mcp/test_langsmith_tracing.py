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

# Stub other Querybook server modules that middleware.py imports.
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

    call_next = AsyncMock(return_value=MagicMock())

    mock_run = MagicMock()
    mock_run.__aenter__ = AsyncMock(return_value=mock_run)
    mock_run.__aexit__ = AsyncMock(return_value=False)

    with patch("lib.mcp.middleware.langsmith") as mock_ls, \
         patch("lib.mcp.middleware.get_access_token", return_value=None):
        mock_ls.trace.return_value = mock_run

        await middleware.on_call_tool(context, call_next)

        mock_ls.trace.assert_called_once_with(
            name="list_environments",
            run_type="tool",
            inputs={"arguments": {"environment_id": 1}},
            metadata={"user_id": 0},
            tags=["mcp", "querybook"],
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

    mock_run = MagicMock()
    mock_run.__aenter__ = AsyncMock(return_value=mock_run)
    mock_run.__aexit__ = AsyncMock(return_value=False)

    with patch("lib.mcp.middleware.langsmith") as mock_ls, \
         patch("lib.mcp.middleware.get_access_token", return_value=None):
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

    with patch("lib.mcp.middleware.langsmith") as mock_ls, \
         patch("lib.mcp.middleware._log_mcp_event"):
        mock_ls.trace.return_value = mock_run

        wrapped_func(env_id=42)

        mock_ls.trace.assert_called_once()
        call_kwargs = mock_ls.trace.call_args
        assert call_kwargs.kwargs.get("run_type") == "tool"
        assert "querybook://environment/42" in call_kwargs.kwargs.get("name", "")
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

    with patch("lib.mcp.middleware.langsmith") as mock_ls, \
         patch("lib.mcp.middleware._log_mcp_event"):
        mock_ls.trace.return_value = mock_run

        with pytest.raises(RuntimeError, match="not found"):
            wrapped_func(datadoc_id=99)

        mock_run.end.assert_called_once_with(error="not found")
