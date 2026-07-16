"""Tests for the central MCP exception mapper and its wiring.

Covers ``lib.mcp.exceptions.to_tool_error`` (pure function), the
``ExceptionMappingMiddleware`` used for tools, and the resource decorator
wrapper in ``wrap_mcp_resources``. The async middleware is driven via
``asyncio.run`` so these run without pytest-asyncio (not installed in CI).
"""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from fastmcp.exceptions import ToolError
from pydantic import BaseModel, ValidationError
from logic.board_permission import BoardDoesNotExist
from logic.datadoc_permission import DocDoesNotExist

from lib.mcp.exceptions import (
    AuthorizationError,
    classify_exception,
    find_authorization_error,
    find_validation_error,
    to_tool_error,
)


def _make_validation_error():
    """Produce a real pydantic ValidationError, as arg coercion would raise."""

    class _Model(BaseModel):
        n: int

    try:
        _Model(n="not-an-int")
    except ValidationError as e:
        return e


class TestAuthorizationError:
    def test_default_message_uses_action(self):
        err = AuthorizationError(action="write", resource="datadoc:1")
        assert err.action == "write"
        assert err.resource == "datadoc:1"
        assert str(err) == "You do not have permission to write this resource."

    def test_explicit_message_overrides_default(self):
        err = AuthorizationError("custom", action="read", resource="list:2")
        assert str(err) == "custom"


class TestClassifyException:
    """The single cause-chain walk that backs both to_tool_error and
    find_authorization_error — both results from one traversal."""

    def test_authorization_error_yields_both_mapped_and_authz(self):
        err = AuthorizationError(action="write", resource="datadoc:1")
        tool_error, authz_error = classify_exception(err)
        assert isinstance(tool_error, ToolError)
        assert str(tool_error) == "You do not have permission to write this resource."
        assert authz_error is err

    def test_not_found_maps_with_no_authz(self):
        tool_error, authz_error = classify_exception(DocDoesNotExist())
        assert str(tool_error) == "The requested DataDoc was not found."
        assert authz_error is None

    def test_unmapped_yields_neither(self):
        assert classify_exception(RuntimeError("boom")) == (None, None)

    def test_independent_first_match_through_chain(self):
        # A ValueError nearer the top maps the client message; a deeper
        # AuthorizationError is still recovered for the audit event. Each result
        # keeps its own "first match" independent of the other.
        authz = AuthorizationError(action="read", resource="datadoc:9")
        middle = ValueError("DataDoc cell 5 not found.")
        middle.__cause__ = authz
        tool_error, authz_error = classify_exception(middle)
        assert str(tool_error) == "DataDoc cell 5 not found."
        assert authz_error is authz

    def test_accessors_match_classify(self):
        wrapped = ToolError("Error calling tool 'x': ")
        wrapped.__cause__ = AuthorizationError(action="edit", resource="list:2")
        tool_error, authz_error = classify_exception(wrapped)
        assert to_tool_error(wrapped) is not None
        assert str(to_tool_error(wrapped)) == str(tool_error)
        assert find_authorization_error(wrapped) is authz_error


class TestFindAuthorizationError:
    """The audit layer keys its `authz` deny event off the AuthorizationError in
    the failed call's cause chain (carrying action/resource), so it must be found
    both when raised directly (resources) and through FastMCP's wrapper (tools)."""

    def test_finds_direct_authorization_error(self):
        err = AuthorizationError(action="write", resource="datadoc:1")
        assert find_authorization_error(err) is err

    def test_finds_authorization_error_through_cause_chain(self):
        inner = AuthorizationError(action="read", resource="datadoc:9")
        wrapped = ToolError("Error calling tool 'get_datadoc': ")
        wrapped.__cause__ = inner
        assert find_authorization_error(wrapped) is inner

    def test_returns_none_when_absent(self):
        assert find_authorization_error(RuntimeError("boom")) is None
        wrapped = ToolError("x")
        wrapped.__cause__ = DocDoesNotExist()
        assert find_authorization_error(wrapped) is None


class TestFindValidationError:
    """The audit layer emits rejected_invocation{malformed_params} off the
    pydantic ValidationError in the failed call's cause chain, so it must be found
    both when raised directly and through FastMCP's ToolError wrapper."""

    def test_finds_direct_validation_error(self):
        err = _make_validation_error()
        assert find_validation_error(err) is err

    def test_finds_validation_error_through_cause_chain(self):
        inner = _make_validation_error()
        wrapped = ToolError("Error calling tool 'execute_ad_hoc_query': ")
        wrapped.__cause__ = inner
        assert find_validation_error(wrapped) is inner

    def test_returns_none_when_absent(self):
        assert find_validation_error(RuntimeError("boom")) is None
        wrapped = ToolError("x")
        wrapped.__cause__ = DocDoesNotExist()
        assert find_validation_error(wrapped) is None


class TestToToolError:
    def test_authorization_error_maps_to_tool_error(self):
        result = to_tool_error(AuthorizationError(action="write", resource="datadoc:1"))
        assert isinstance(result, ToolError)
        assert str(result) == "You do not have permission to write this resource."

    def test_doc_not_found_maps_to_tool_error(self):
        result = to_tool_error(DocDoesNotExist())
        assert isinstance(result, ToolError)
        assert str(result) == "The requested DataDoc was not found."

    def test_board_not_found_maps_to_tool_error(self):
        result = to_tool_error(BoardDoesNotExist())
        assert isinstance(result, ToolError)
        assert str(result) == "The requested list was not found."

    def test_value_error_maps_to_tool_error_verbatim(self):
        # Tools raise ValueError for intentional client-safe messages; these are
        # surfaced directly (no "Error calling tool 'X':" prefix).
        result = to_tool_error(ValueError("DataDoc cell 5 not found."))
        assert isinstance(result, ToolError)
        assert str(result) == "DataDoc cell 5 not found."

    def test_value_error_wrapped_by_fastmcp_maps_verbatim(self):
        wrapped = ToolError("Error calling tool 'update_list_item': ")
        wrapped.__cause__ = ValueError("List item 5 not found.")
        result = to_tool_error(wrapped)
        assert str(result) == "List item 5 not found."

    def test_unmapped_exception_returns_none(self):
        assert to_tool_error(RuntimeError()) is None
        assert to_tool_error(KeyError("x")) is None

    def test_maps_domain_exception_wrapped_by_fastmcp(self):
        # FastMCP catches the tool's raw exception below all middleware and
        # re-raises ``ToolError(...) from original`` before middleware sees it,
        # so the domain exception survives only as ``__cause__``.
        wrapped = ToolError("Error calling tool 'update_datadoc': ")
        wrapped.__cause__ = DocDoesNotExist()
        result = to_tool_error(wrapped)
        assert isinstance(result, ToolError)
        assert str(result) == "The requested DataDoc was not found."

    def test_maps_authorization_error_wrapped_by_fastmcp(self):
        wrapped = ToolError("Error calling tool 'update_datadoc': ...")
        wrapped.__cause__ = AuthorizationError(action="write", resource="datadoc:1")
        result = to_tool_error(wrapped)
        assert str(result) == "You do not have permission to write this resource."

    def test_explicit_tool_error_without_mapped_cause_returns_none(self):
        # A ToolError a tool raises on purpose (e.g. GitHub failures) must pass
        # through unchanged rather than being remapped.
        explicit = ToolError("GitHub authorization required")
        assert to_tool_error(explicit) is None

    def test_deeply_nested_cause_is_mapped(self):
        inner = DocDoesNotExist()
        middle = RuntimeError("layer")
        middle.__cause__ = inner
        outer = ToolError("Error calling tool 'x': ")
        outer.__cause__ = middle
        result = to_tool_error(outer)
        assert str(result) == "The requested DataDoc was not found."


class TestExceptionMappingMiddleware:
    def _run(self, call_next):
        from lib.mcp.middleware import ExceptionMappingMiddleware

        middleware = ExceptionMappingMiddleware()
        return asyncio.run(middleware.on_call_tool(MagicMock(), call_next))

    def test_maps_domain_exception_to_tool_error(self):
        async def call_next(_context):
            raise DocDoesNotExist()

        with pytest.raises(ToolError) as exc_info:
            self._run(call_next)
        assert str(exc_info.value) == "The requested DataDoc was not found."

    def test_maps_authorization_error_to_tool_error(self):
        async def call_next(_context):
            raise AuthorizationError(action="read", resource="datadoc:9")

        with pytest.raises(ToolError) as exc_info:
            self._run(call_next)
        assert str(exc_info.value) == (
            "You do not have permission to read this resource."
        )

    def test_maps_domain_exception_wrapped_by_fastmcp(self):
        # Production path: FastMCP wraps the domain exception before middleware
        # runs, so the middleware actually catches a generic ToolError whose
        # ``__cause__`` is the real error.
        async def call_next(_context):
            try:
                raise DocDoesNotExist()
            except DocDoesNotExist as e:
                raise ToolError("Error calling tool 'update_datadoc': ") from e

        with pytest.raises(ToolError) as exc_info:
            self._run(call_next)
        assert str(exc_info.value) == "The requested DataDoc was not found."

    def test_passes_unmapped_exception_through_unchanged(self):
        async def call_next(_context):
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            self._run(call_next)

    def test_maps_value_error_to_tool_error(self):
        async def call_next(_context):
            raise ValueError("DataDoc cell 5 not found.")

        with pytest.raises(ToolError) as exc_info:
            self._run(call_next)
        assert str(exc_info.value) == "DataDoc cell 5 not found."

    def test_returns_result_on_success(self):
        async def call_next(_context):
            return "ok"

        assert self._run(call_next) == "ok"


class TestResourceWrapperMapping:
    """The resource decorator wrapper must apply the same mapping as tools,
    since resources bypass the on_call_tool middleware hook."""

    def _make_wrapped_resource(self, func):
        from lib.mcp import middleware as mw_mod

        class FakeMCP:
            def resource(self, **kwargs):
                def decorator(fn):
                    return fn

                return decorator

        fake = FakeMCP()
        mw_mod.wrap_mcp_resources(fake)
        # mcp.resource is now the logging wrapper; register the resource func.
        return fake.resource(uri="querybook://list/{list_id}")(func)

    def test_resource_exception_is_mapped(self):
        from lib.mcp import middleware as mw_mod

        def raises_board(list_id, token=None):
            raise BoardDoesNotExist()

        wrapped = self._make_wrapped_resource(raises_board)

        with patch.object(mw_mod, "log_mcp_event"), patch.object(
            mw_mod, "langsmith", MagicMock()
        ):
            with pytest.raises(ToolError) as exc_info:
                wrapped(list_id=1)
        assert str(exc_info.value) == "The requested list was not found."

    def test_resource_unmapped_exception_passes_through(self):
        from lib.mcp import middleware as mw_mod

        def raises_runtime(list_id, token=None):
            raise RuntimeError("nope")

        wrapped = self._make_wrapped_resource(raises_runtime)

        with patch.object(mw_mod, "log_mcp_event"), patch.object(
            mw_mod, "langsmith", MagicMock()
        ):
            with pytest.raises(RuntimeError, match="nope"):
                wrapped(list_id=1)

    def test_resource_logs_mapped_message(self):
        """The event log and LangSmith run record the mapped client-facing
        message, not the raw exception — keeping resource logs consistent with
        the tool path and with what the caller sees."""
        from lib.mcp import middleware as mw_mod

        def raises_board(list_id, token=None):
            raise BoardDoesNotExist("internal board lookup failed")

        wrapped = self._make_wrapped_resource(raises_board)

        fake_langsmith = MagicMock()
        ls_run = fake_langsmith.trace.return_value.__enter__.return_value

        with patch.object(mw_mod, "log_mcp_event") as log_event, patch.object(
            mw_mod, "langsmith", fake_langsmith
        ), patch.object(mw_mod.QuerybookSettings, "LANGSMITH_TRACING", True):
            with pytest.raises(ToolError):
                wrapped(list_id=1)

        # log_mcp_event(event_type, payload) — payload is the second positional arg.
        logged_error = log_event.call_args.args[1]["error"]
        assert logged_error == "The requested list was not found."
        ls_run.end.assert_called_once_with(error="The requested list was not found.")
