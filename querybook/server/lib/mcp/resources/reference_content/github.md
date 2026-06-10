# Querybook GitHub Integration

Querybook can version-control DataDocs in a server-configured GitHub repository.
Users authorize once through OAuth, link a DataDoc to a repository directory,
then commit, compare, and restore DataDoc versions.

## Typical Workflow

1. Check authorization with `check_github_auth()`.
2. If needed, call `authorize_github()` and complete the browser flow.
3. Call `get_datadoc_github_directory_recommendation(datadoc_id)`.
4. Optionally inspect directories with `get_github_directory_structure(datadoc_id)`.
5. Optionally validate a custom path with `validate_github_directory(directory, datadoc_id)`.
6. Link with `link_datadoc_github(datadoc_id, directory)`.
7. Commit with `commit_datadoc_github(datadoc_id, commit_message)`.
8. Read history from `querybook://datadoc/{id}/github-history?limit=20&offset=0`.
9. Compare or restore with `compare_datadoc_github_version()` and `restore_datadoc_from_github()`.

## Authorization

`check_github_auth()` returns authorization status, GitHub username, repository,
and branch. If not authorized, `authorize_github()` returns a short URL that is
valid for a limited time. After the browser flow completes, call
`check_github_auth()` again.

Use `revoke_github_auth()` to remove the stored token. Reauthorization is then
required before using GitHub tools again.

## Directory Selection

Always get a recommendation before linking:

```python
get_datadoc_github_directory_recommendation(datadoc_id=123)
```

Common directory patterns:

-   `user/<username>` for personal DataDocs.
-   `team/<teamname>` for team-owned analysis.
-   `shared/<name>` for cross-team resources.
-   `datadocs/` for legacy or temporary organization.

Directory names should use lowercase letters, numbers, hyphens, and slashes.
Avoid spaces and special characters.

## Linking

```python
link_datadoc_github(
    datadoc_id=123,
    directory="user/example-user",
)
```

Linking creates or updates the Querybook-to-GitHub association. It does not
commit content by itself. Use `commit_datadoc_github` after linking.

## Committing

Commit meaningful units of work:

```python
commit_datadoc_github(
    datadoc_id=123,
    commit_message="Add checkout funnel baseline analysis",
)
```

Good commit messages describe what changed and why. Avoid messages such as
`Update`, `wip`, or `test` unless the commit is intentionally temporary.

MCP commits include metadata footers for auditability, including source, tool,
user, timestamp, client, and API token suffix.

## History, Compare, Restore

Commit history is available as an MCP resource:

```text
querybook://datadoc/{id}/github-history
querybook://datadoc/{id}/github-history?limit=50&offset=0
```

Use `compare_datadoc_github_version(datadoc_id, commit_sha)` to inspect current
content against a historical version before restoring.

Use `restore_datadoc_from_github(datadoc_id, commit_sha)` to replace the current
DataDoc with a historical version. Restoration is reversible because you can
restore another commit later. It does not automatically create a new GitHub
commit; commit the restored state if you want the rollback recorded.

## Unlinking

`unlink_datadoc_github(datadoc_id)` removes the Querybook link only. The GitHub
file remains in the repository and must be deleted manually if desired.

## Best Practices

-   Commit after completing a useful analysis step, before risky edits, or before scheduling.
-   Do not commit after every small cell edit.
-   Use team directories for shared or scheduled work.
-   Use personal directories for exploratory work.
-   Validate custom directories before linking.
-   Compare before restoring.
-   Avoid committing secrets, credentials, or sensitive result data into DataDoc content.
