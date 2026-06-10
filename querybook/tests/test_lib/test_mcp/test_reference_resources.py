import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest


@pytest.fixture()
def reference_resource_stubs(monkeypatch):
    fastmcp = sys.modules.get("fastmcp", ModuleType("fastmcp"))
    monkeypatch.setitem(sys.modules, "fastmcp", fastmcp)
    monkeypatch.setattr(fastmcp, "FastMCP", MagicMock, raising=False)

    fastmcp_server = sys.modules.get("fastmcp.server", ModuleType("fastmcp.server"))
    monkeypatch.setitem(sys.modules, "fastmcp.server", fastmcp_server)

    fastmcp_server_auth = sys.modules.get(
        "fastmcp.server.auth", ModuleType("fastmcp.server.auth")
    )
    monkeypatch.setitem(sys.modules, "fastmcp.server.auth", fastmcp_server_auth)
    monkeypatch.setattr(fastmcp_server_auth, "AccessToken", MagicMock, raising=False)

    fastmcp_server_deps = sys.modules.get(
        "fastmcp.server.dependencies", ModuleType("fastmcp.server.dependencies")
    )
    monkeypatch.setitem(sys.modules, "fastmcp.server.dependencies", fastmcp_server_deps)
    monkeypatch.setattr(
        fastmcp_server_deps,
        "CurrentAccessToken",
        MagicMock(return_value=MagicMock()),
        raising=False,
    )

    mcp_utils = ModuleType("lib.mcp.utils")
    mcp_utils.RESOURCE_ANNOTATIONS = {
        "readOnlyHint": True,
        "idempotentHint": True,
    }
    monkeypatch.setitem(sys.modules, "lib.mcp.utils", mcp_utils)

    yield

    sys.modules.pop("lib.mcp.resources.reference", None)
    sys.modules.pop("lib.mcp.resources.guide", None)


class FakeMCP:
    def __init__(self):
        self.registered_resources = []

    def resource(self, **kwargs):
        def decorator(func):
            self.registered_resources.append((kwargs, func))
            return func

        return decorator


def test_reference_resources_register_expected_static_uris(reference_resource_stubs):
    from lib.mcp.resources import reference

    mcp = FakeMCP()
    reference.register(mcp)

    by_uri = {
        kwargs["uri"]: (kwargs, func) for kwargs, func in mcp.registered_resources
    }

    assert set(by_uri) == {
        "querybook://reference/chart-cells",
        "querybook://reference/rich-text",
        "querybook://reference/github",
        "querybook://reference/downloading-results",
        "querybook://reference/agent-skill",
    }

    chart_kwargs, chart_func = by_uri["querybook://reference/chart-cells"]
    assert chart_kwargs["mime_type"] == "text/markdown"
    chart_file = (
        reference._REFERENCE_DIR
        / reference.REFERENCE_RESOURCES["chart-cells"]["filename"]
    )
    assert chart_file.exists()
    assert chart_func() == chart_file.read_text(encoding="utf-8")
    assert "source_type" in chart_func()
    assert (
        "querybook://reference/chart-cells"
        in reference.REFERENCE_RESOURCES["chart-cells"]["uri"]
    )

    rich_text = by_uri["querybook://reference/rich-text"][1]()
    assert "<strong>Bold text</strong>" in rich_text

    github = by_uri["querybook://reference/github"][1]()
    assert "commit_datadoc_github" in github

    downloading = by_uri["querybook://reference/downloading-results"][1]()
    assert "results_download_url" in downloading

    agent_skill = by_uri["querybook://reference/agent-skill"][1]()
    assert "Analytics+Platform+Agent+Skills" in agent_skill
    assert "data-platform-skills-plugin" in agent_skill


def test_resource_guide_lists_static_references(reference_resource_stubs):
    from lib.mcp.resources.guide import RESOURCE_GUIDE

    assert "## Static Reference Guides" in RESOURCE_GUIDE
    assert "querybook://reference/chart-cells" in RESOURCE_GUIDE
    assert "querybook://reference/rich-text" in RESOURCE_GUIDE
    assert "querybook://reference/github" in RESOURCE_GUIDE
    assert "querybook://reference/downloading-results" in RESOURCE_GUIDE
    assert "querybook://reference/agent-skill" in RESOURCE_GUIDE
