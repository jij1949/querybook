"""Central exception mapping for the Querybook MCP server.

Tools and resources raise raw domain exceptions; ``to_tool_error`` is the single
place that maps them to consistent client-facing ``ToolError`` messages. This
keeps per-site error handling thin and the client-visible wording uniform.
"""

from fastmcp.exceptions import ToolError

from logic.board_permission import BoardDoesNotExist
from logic.datadoc_permission import DocDoesNotExist


class AuthorizationError(Exception):
    """Raised when the caller lacks permission to act on a resource.

    The ``action`` and ``resource`` attributes carry the specifics (e.g.
    ``write`` / ``datadoc:123``) for logging; the client-facing message is a
    generic permission string.
    """

    def __init__(self, message=None, *, action, resource):
        self.action = action
        self.resource = resource
        super().__init__(
            message or f"You do not have permission to {action} this resource."
        )


_NOT_FOUND_MESSAGES = {
    DocDoesNotExist: "The requested DataDoc was not found.",
    BoardDoesNotExist: "The requested list was not found.",
}


def _map_single(exc):
    """Map one exception instance to a ToolError, or None if unmapped."""
    if isinstance(exc, AuthorizationError):
        return ToolError(str(exc))
    for exc_type, message in _NOT_FOUND_MESSAGES.items():
        if isinstance(exc, exc_type):
            return ToolError(message)
    if isinstance(exc, ValueError):
        # Tools raise ValueError for intentional, client-safe validation and
        # sub-entity not-found messages (e.g. "DataDoc cell 5 not found."). Surface
        # the message directly so the client sees a clean sentence instead of
        # FastMCP's "Error calling tool 'X': ..." wrapper. NOTE: this promotes the
        # message verbatim to the client; if mask_error_details is ever enabled,
        # accidental ValueErrors would still be shown (ToolError bypasses masking).
        return ToolError(str(exc))
    return None


def classify_exception(exc):
    """Walk the ``__cause__`` chain once and return what every consumer needs.

    Returns ``(tool_error, authz_error)``:

    - ``tool_error``: the client-facing ``ToolError`` to surface, or ``None`` when
      nothing in the chain should be remapped (the original propagates unchanged,
      e.g. an explicit ``ToolError`` a tool raised on purpose).
    - ``authz_error``: the ``AuthorizationError`` in the chain — the audit layer
      reads its ``action`` / ``resource`` for the ``authz`` deny event — or
      ``None``.

    Both come from a single traversal because FastMCP catches the handler's
    exception in its innermost ``call_tool`` layer — *below all middleware* — and
    re-raises it as ``ToolError(...) from original``. By the time any middleware
    runs (the client-facing mapper *or* the audit classifier), the real domain
    exception is no longer the top-level error but a ``__cause__`` of that
    wrapper, so reading the top-level exception alone is never enough. (Resources
    raise their exception directly, so the top-level ``exc`` is checked first
    anyway.) Each result keeps its independent "first match wins" semantics; the
    walk stops early once both are found.
    """
    seen = set()
    current = exc
    tool_error = None
    authz_error = None
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if tool_error is None:
            tool_error = _map_single(current)
        if authz_error is None and isinstance(current, AuthorizationError):
            authz_error = current
        if tool_error is not None and authz_error is not None:
            break
        current = current.__cause__
    return tool_error, authz_error


def to_tool_error(exc):
    """Map a raw domain exception to a client-facing ToolError, or None.

    Thin accessor over :func:`classify_exception` for the client-mapping path
    (``ExceptionMappingMiddleware`` and the resource wrapper). None means nothing
    in the chain should be remapped, so the original exception propagates.
    """
    return classify_exception(exc)[0]


def find_authorization_error(exc):
    """Return the ``AuthorizationError`` in this exception's cause chain, or None.

    Thin accessor over :func:`classify_exception` for the audit path, which needs
    the gate's ``action`` / ``resource`` to emit the ``authz`` deny event.
    """
    return classify_exception(exc)[1]
