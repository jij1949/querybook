# Querybook Agent Skill

The Querybook MCP server includes lightweight built-in reference resources for
common Querybook workflows. The full Querybook Agent Skill lives in the Data
Platform Skills Plugin and may include broader, more current guidance for setup,
agent-specific usage, workflow patterns, best practices, and troubleshooting.

Documentation:
https://expediagroup.atlassian.net/wiki/spaces/DSPKB/pages/1029592183/Analytics+Platform+Agent+Skills

Source repository:
https://github.com/eg-internal/data-platform-skills-plugin

Built-in Querybook MCP references:

-   `querybook://resource-guide`: list of available Querybook MCP resources.
-   `querybook://reference/chart-cells`: chart cell metadata schema and examples.
-   `querybook://reference/rich-text`: HTML formatting for DataDoc text cells.
-   `querybook://reference/github`: DataDoc GitHub workflows.
-   `querybook://reference/downloading-results`: large result download guidance.

These built-in references are intentionally smaller than the Agent Skill. They
are meant to help MCP clients when the full skill is not installed, not to replace
the external documentation or source repository.
