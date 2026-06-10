from pathlib import Path

from fastmcp import FastMCP
from fastmcp.server.auth import AccessToken
from fastmcp.server.dependencies import CurrentAccessToken

from lib.mcp.utils import RESOURCE_ANNOTATIONS

_REFERENCE_DIR = Path(__file__).with_name("reference_content")

REFERENCE_RESOURCES = {
    "chart-cells": {
        "uri": "querybook://reference/chart-cells",
        "name": "Chart Cell Reference",
        "description": "Markdown reference for Querybook chart cell metadata schema and examples",
        "filename": "chart-cells.md",
    },
    "rich-text": {
        "uri": "querybook://reference/rich-text",
        "name": "Rich Text Reference",
        "description": "Markdown reference for Querybook text cell HTML formatting",
        "filename": "rich-text.md",
    },
    "github": {
        "uri": "querybook://reference/github",
        "name": "GitHub Integration Reference",
        "description": "Markdown reference for Querybook DataDoc GitHub workflows",
        "filename": "github.md",
    },
    "downloading-results": {
        "uri": "querybook://reference/downloading-results",
        "name": "Downloading Results Reference",
        "description": "Markdown reference for downloading large Querybook query results",
        "filename": "downloading-results.md",
    },
    "agent-skill": {
        "uri": "querybook://reference/agent-skill",
        "name": "Agent Skill Reference",
        "description": "Markdown reference for the optional Querybook Agent Skill and full Data Platform Skills Plugin",
        "filename": "agent-skill.md",
    },
}


def _load_reference(filename: str) -> str:
    return (_REFERENCE_DIR / filename).read_text(encoding="utf-8")


def _build_reference_getter(filename: str, slug: str):
    def get_reference(
        token: AccessToken = CurrentAccessToken(),
    ) -> str:
        """Returns a Markdown Querybook reference document."""
        return _load_reference(filename)

    get_reference.__name__ = f"get_{slug.replace('-', '_')}_reference"
    return get_reference


def register(mcp: FastMCP) -> None:
    """Register static reference resources on the given MCP server."""
    for slug, resource in REFERENCE_RESOURCES.items():
        mcp.resource(
            uri=resource["uri"],
            name=resource["name"],
            description=resource["description"],
            mime_type="text/markdown",
            annotations=RESOURCE_ANNOTATIONS,
        )(_build_reference_getter(resource["filename"], slug))
