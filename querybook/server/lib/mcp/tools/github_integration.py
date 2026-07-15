"""
GitHub integration tools for DataDoc version control.

Tools for managing GitHub synchronization, commit history, and version restoration
for DataDocs linked to GitHub repositories.

Provides 7 tools covering the complete user workflow:
- Setup & Discovery (4 tools): check auth, explore directories, get recommendations, validate
- Core Operations (2 tools): link, commit
- History & Versioning (1 tool): compare/restore versions, unlink

Note: GitHub status and history are available via resources:
- querybook://datadoc/{id} - includes GitHub status with history_resource_uri
- querybook://datadoc/{id}/github-history - commit history with pagination

Workflow reference: querybook://reference/github
"""

import uuid
import webbrowser
from datetime import datetime
from typing import Annotated

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.server.auth import AccessToken
from fastmcp.server.dependencies import CurrentAccessToken

from app.db import DBSession
from clients.github_client import GitHubClient
from clients.redis_client import get_redis
from env import QuerybookSettings
from lib.github.github import github_manager, MCP_OAUTH_SESSION_TTL
from lib.logger import get_logger
from lib.github.serializers import serialize_datadoc_to_markdown
from lib.mcp.exceptions import AuthorizationError
from lib.mcp.lib.github import (
    analyze_directory_structure,
    format_commit_message,
    generate_directory_recommendations,
    get_directory_usage_stats,
    get_smart_default_directory,
    get_token_suffix,
    serialize_commit,
    validate_directory_path,
)
from lib.mcp.utils import (
    DELETE_ANNOTATIONS,
    READ_ONLY_ANNOTATIONS,
    WRITE_ANNOTATIONS,
)
from logic import datadoc as datadoc_logic
from logic import github as github_logic
from logic.datadoc import restore_data_doc_from_commit
from logic.datadoc_permission import (
    user_can_read,
    user_can_write,
)
from logic.user import get_user_by_id

LOG = get_logger(__file__)


def _get_github_client(datadoc_id: int, uid: int, session) -> GitHubClient:
    """Get configured GitHub client for a DataDoc."""
    github_link = github_logic.get_repo_link(datadoc_id, session=session)
    if not github_link:
        raise ValueError(
            f"DataDoc {datadoc_id} is not linked to GitHub. "
            "Use link_datadoc_github to set up version control first."
        )

    access_token = github_manager.get_github_token(uid=uid)
    return GitHubClient(
        github_link=github_link,
        access_token=access_token,
        repo_name=QuerybookSettings.GITHUB_REPO_NAME,
        branch=QuerybookSettings.GITHUB_BRANCH,
    )


def register(mcp: FastMCP) -> None:
    """Register GitHub integration tools on the given MCP server."""

    @mcp.tool(
        title="Check GitHub Authorization Status",
        annotations=READ_ONLY_ANNOTATIONS,
    )
    def check_github_auth(
        token: AccessToken = CurrentAccessToken(),
    ) -> dict:
        """
        Check if your GitHub account is authorized for Querybook integration.

        Returns authorization status and GitHub username if connected.
        You must authorize via the Querybook UI before using GitHub tools.
        """
        uid = token.claims["creator_uid"]
        try:
            github_manager.get_github_token(uid=uid)
            is_authorized = True

            # Try to get GitHub username
            try:
                temp_client = GitHubClient(
                    access_token=github_manager.get_github_token(uid=uid),
                    repo_name=QuerybookSettings.GITHUB_REPO_NAME,
                    branch=QuerybookSettings.GITHUB_BRANCH,
                    github_link=None,
                )
                github_username = temp_client.user.login
            except Exception as e:
                LOG.debug(f"Could not fetch GitHub username for uid={uid}: {e}")
                github_username = None

        except Exception as e:
            LOG.debug(f"GitHub auth check failed for uid={uid}: {e}")
            is_authorized = False
            github_username = None

        return {
            "is_authorized": is_authorized,
            "github_username": github_username,
            "repository": QuerybookSettings.GITHUB_REPO_NAME,
            "branch": QuerybookSettings.GITHUB_BRANCH,
            "message": (
                "Connected to GitHub"
                if is_authorized
                else "Not connected. Please authorize via Querybook UI settings."
            ),
        }

    @mcp.tool(
        title="Revoke GitHub Authorization",
        annotations=WRITE_ANNOTATIONS,
    )
    def revoke_github_auth(
        token: AccessToken = CurrentAccessToken(),
    ) -> dict:
        """
        Revoke your GitHub authorization for Querybook integration.

        This removes the stored GitHub access token. You will need to
        re-authorize via authorize_github to use GitHub features again.
        """
        uid = token.claims["creator_uid"]

        try:
            github_manager.invalidate_token(uid=uid)
            return {
                "success": True,
                "message": "GitHub authorization revoked successfully. Use authorize_github to reconnect.",
                "repository": QuerybookSettings.GITHUB_REPO_NAME,
            }
        except Exception as e:
            LOG.error(
                f"Failed to revoke GitHub authorization for uid={uid}: {e}",
                exc_info=True,
            )
            raise ToolError(f"Failed to revoke authorization: {str(e)}")

    @mcp.tool(
        title="Authorize GitHub Account",
        annotations=READ_ONLY_ANNOTATIONS,
    )
    def authorize_github(
        token: AccessToken = CurrentAccessToken(),
    ) -> dict:
        """
        Authorize your GitHub account for Querybook integration.

        Returns a short, easy-to-copy URL that redirects to GitHub authorization.
        The URL is valid for 5 minutes. After authorizing, use check_github_auth
        to verify the connection.
        """
        uid = token.claims["creator_uid"]

        try:
            # Generate unique session ID
            session_id = str(uuid.uuid4())

            # Store pending request in Redis
            redis_client = get_redis()
            pending_key = f"github_oauth_pending:{session_id}"

            redis_client.setex(
                pending_key, MCP_OAUTH_SESSION_TTL, str(uid)  # Store user_id as value
            )

            # Use short redirect URL instead of long OAuth URL
            # This Flask route will generate the full OAuth URL and auto-redirect
            short_url = f"{QuerybookSettings.PUBLIC_URL}/github/mcp-oauth-initiate?session_id={session_id}"

            # Try to open browser automatically
            browser_opened = False
            try:
                browser_opened = webbrowser.open(short_url)
            except Exception as e:
                LOG.debug(f"Could not auto-open browser: {e}")
                # If browser fails to open, that's okay - URL is in the response
                pass

            # Format URL as clickable link for modern terminals
            clickable_url = f"\x1b]8;;{short_url}\x1b\\{short_url}\x1b]8;;\x1b\\"

            return {
                "success": True,
                "authorization_url": short_url,
                "authorization_url_clickable": clickable_url,
                "session_id": session_id,
                "browser_opened": browser_opened,
                "message": (
                    f"Open this URL in your browser:\n{short_url}\n\n"
                    "Copy the entire URL (it should fit on one line)."
                ),
                "instructions": [
                    f"1. Open this URL in your browser: {short_url}",
                    "2. Authorize Querybook when prompted by GitHub",
                    "3. Wait for the success message",
                    "4. Use check_github_auth to verify the connection",
                ],
                "expires_in_seconds": MCP_OAUTH_SESSION_TTL,
                "repository": QuerybookSettings.GITHUB_REPO_NAME,
                "branch": QuerybookSettings.GITHUB_BRANCH,
            }

        except Exception as e:
            LOG.error(
                f"Failed to generate GitHub authorization URL for uid={uid}: {e}",
                exc_info=True,
            )
            raise ToolError(f"Failed to generate authorization URL: {str(e)}")

    @mcp.tool(
        title="Get GitHub Directory Structure",
        annotations=READ_ONLY_ANNOTATIONS,
    )
    def get_github_directory_structure(
        datadoc_id: Annotated[int, "DataDoc ID for authentication context"],
        token: AccessToken = CurrentAccessToken(),
    ) -> dict:
        """
        Get the GitHub repository directory structure with recommendations.

        Returns organized directory structure (team/, user/, etc.) with usage
        statistics and personalized recommendations for where to place DataDocs.
        See querybook://reference/github for the full linking workflow.
        """
        uid = token.claims["creator_uid"]

        with DBSession() as session:
            # Check read permission on the datadoc (just for auth context)
            if not user_can_read(datadoc_id, uid=uid, session=session):
                raise AuthorizationError(
                    action="read", resource=f"datadoc:{datadoc_id}"
                )

            # Get directories from GitHub
            try:
                access_token = github_manager.get_github_token(uid=uid)
                github_client = GitHubClient(
                    access_token=access_token,
                    repo_name=QuerybookSettings.GITHUB_REPO_NAME,
                    branch=QuerybookSettings.GITHUB_BRANCH,
                    github_link=None,
                )
                directories = github_client.get_repo_directories()
            except Exception as e:
                LOG.error(
                    f"Failed to fetch GitHub directories for uid={uid}, "
                    f"datadoc {datadoc_id}: {e}",
                    exc_info=True,
                )
                raise ToolError(f"Failed to fetch GitHub directories: {str(e)}")

            # Get current user
            user = get_user_by_id(uid, session=session)

            # Analyze structure
            structure = analyze_directory_structure(directories)

            # Get usage statistics
            usage_stats = get_directory_usage_stats(session)

            # Generate recommendations
            recommendations = generate_directory_recommendations(
                user=user,
                directories=directories,
                usage_stats=usage_stats,
                session=session,
            )

            return {
                "repository": QuerybookSettings.GITHUB_REPO_NAME,
                "branch": QuerybookSettings.GITHUB_BRANCH,
                "structure": structure,
                "recommendations": recommendations,
                "usage_statistics": usage_stats,
                "can_create_new": True,
                "naming_rules": {
                    "pattern": "^[a-z0-9-]+(?:/[a-z0-9-]+)*$",
                    "description": "Use lowercase letters, numbers, and hyphens. No spaces or special characters.",
                    "examples": [
                        "user/username",
                        "team/teamname",
                        "team/analytics/forecasting",
                    ],
                },
            }

    @mcp.tool(
        title="Get DataDoc GitHub Directory Recommendation",
        annotations=READ_ONLY_ANNOTATIONS,
    )
    def get_datadoc_github_directory_recommendation(
        datadoc_id: Annotated[int, "DataDoc ID to recommend directory for"],
        token: AccessToken = CurrentAccessToken(),
    ) -> dict:
        """
        Get a smart directory recommendation in the GitHub repository
        querybook-datadocs based on DataDoc context.

        Analyzes the DataDoc's ownership, visibility, collaborators, and
        environment to suggest the most appropriate GitHub directory in the repo for this DataDoc.
        See querybook://reference/github for directory conventions.
        """
        uid = token.claims["creator_uid"]

        with DBSession() as session:
            if not user_can_read(datadoc_id, uid=uid, session=session):
                raise AuthorizationError(
                    action="read", resource=f"datadoc:{datadoc_id}"
                )

            doc = datadoc_logic.get_data_doc_by_id(datadoc_id, session=session)
            if not doc:
                raise ValueError(f"DataDoc {datadoc_id} not found")

            user = get_user_by_id(uid, session=session)

            # Get smart recommendation
            recommendation = get_smart_default_directory(
                doc=doc, user=user, session=session
            )

            return recommendation

    @mcp.tool(
        title="Validate GitHub Directory Path",
        annotations=READ_ONLY_ANNOTATIONS,
    )
    def validate_github_directory(
        directory: Annotated[str, "Directory path to validate"],
        datadoc_id: Annotated[int, "DataDoc ID for permission context"],
        token: AccessToken = CurrentAccessToken(),
    ) -> dict:
        """
        Validate a directory path before linking a DataDoc.

        Checks format, naming conventions, permissions, and whether
        the directory exists or can be created.
        """
        uid = token.claims["creator_uid"]

        with DBSession() as session:
            if not user_can_read(datadoc_id, uid=uid, session=session):
                raise AuthorizationError(
                    action="read", resource=f"datadoc:{datadoc_id}"
                )

            user = get_user_by_id(uid, session=session)

            validation = {
                "directory": directory,
                "is_valid": False,
                "exists": False,
                "can_create": False,
                "has_permission": False,
                "errors": [],
                "warnings": [],
            }

            # Check format
            if not validate_directory_path(directory):
                validation["errors"].append(
                    "Invalid directory format. Must match pattern: "
                    "user/<username>, team/<teamname>, or shared/<name>. "
                    "Use lowercase letters, numbers, and hyphens only."
                )
                return validation

            # Check if exists
            try:
                access_token = github_manager.get_github_token(uid=uid)
                github_client = GitHubClient(
                    access_token=access_token,
                    repo_name=QuerybookSettings.GITHUB_REPO_NAME,
                    branch=QuerybookSettings.GITHUB_BRANCH,
                    github_link=None,
                )
                directories = github_client.get_repo_directories()
                validation["exists"] = directory in directories
            except Exception as e:
                validation["warnings"].append(
                    f"Could not check directory existence: {str(e)}"
                )

            # Check permissions
            if directory.startswith("user/"):
                username = directory.split("/")[1]
                validation["has_permission"] = user.username == username
                if not validation["has_permission"]:
                    validation["errors"].append(
                        f"You can only link to your own user directory (user/{user.username})"
                    )
            else:
                # For team/ and shared/, allow for now
                # TODO: Implement proper team permission checks
                validation["has_permission"] = True
                validation["warnings"].append(
                    "Team/shared directory permissions not fully validated. "
                    "Ensure you have write access."
                )

            # Can create if doesn't exist and has permission
            validation["can_create"] = (
                not validation["exists"] and validation["has_permission"]
            )
            validation["is_valid"] = validation["has_permission"] and (
                validation["exists"] or validation["can_create"]
            )

            if validation["can_create"]:
                validation["warnings"].append(
                    f"Directory '{directory}' will be created on first commit"
                )

            return validation

    @mcp.tool(
        title="Link DataDoc to GitHub",
        annotations=WRITE_ANNOTATIONS,
    )
    def link_datadoc_github(
        datadoc_id: Annotated[int, "DataDoc ID"],
        directory: Annotated[
            str,
            "Directory path in repo (e.g., 'user/rchandna' or 'team/analytics'). "
            "REQUIRED: Use get_datadoc_github_directory_recommendation to see "
            "suggestions before linking. See querybook://reference/github.",
        ],
        token: AccessToken = CurrentAccessToken(),
    ) -> dict:
        """
        Link a DataDoc to a GitHub directory for version control.

        IMPORTANT: You must specify a directory. Use get_datadoc_github_directory_recommendation first
        to see personalized suggestions based on the DataDoc's context.

        The directory structure follows:
        - user/<username>/ - Personal DataDocs
        - team/<teamname>/ - Team-shared DataDocs
        - shared/ - Cross-team resources
        - datadocs/ - Temporary/unorganized (use with caution)

        Workflow:
        1. Call get_datadoc_github_directory_recommendation(datadoc_id) to see suggestions
        2. Present options to user or choose based on recommendation
        3. Call link_datadoc_github(datadoc_id, directory) with chosen directory

        Full workflow reference: querybook://reference/github.
        """
        uid = token.claims["creator_uid"]

        with DBSession() as session:
            # Check write permission using uid (not current_user which doesn't exist in MCP context)
            if not user_can_write(datadoc_id, uid=uid, session=session):
                raise AuthorizationError(
                    action="write", resource=f"datadoc:{datadoc_id}"
                )

            doc = datadoc_logic.get_data_doc_by_id(datadoc_id, session=session)
            if not doc:
                raise ValueError(f"DataDoc {datadoc_id} not found")

            user = get_user_by_id(uid, session=session)
            if not user:
                raise ValueError(f"User {uid} not found")
            if not hasattr(user, "id") or user.id is None:
                raise ValueError(f"User object has no id: {user}")

            # Directory is now required - no auto-default
            # Users must call get_datadoc_github_directory_recommendation first

            # Validate directory
            if not validate_directory_path(directory):
                raise ValueError(
                    f"Invalid directory path '{directory}'. "
                    "Must match pattern: user/<username>, team/<teamname>, or shared/<name>. "
                    "Use lowercase letters, numbers, and hyphens only."
                )

            # Check permissions
            if directory.startswith("user/"):
                username = directory.split("/")[1]
                if user.username != username:
                    raise ValueError(
                        f"You can only link to your own user directory (user/{user.username})"
                    )

            # Create or update the link
            try:
                github_logic.create_repo_link(
                    datadoc_id=datadoc_id,
                    user_id=uid,
                    directory=directory,
                    session=session,
                )
            except Exception as e:
                LOG.error(
                    f"Failed to create GitHub link for datadoc {datadoc_id}: {e}",
                    exc_info=True,
                )
                raise ToolError(f"create_repo_link failed: {str(e)}")

            file_path = f"{directory}/datadoc_{datadoc_id}.md"
            github_url = f"https://github.com/{QuerybookSettings.GITHUB_REPO_NAME}/tree/{QuerybookSettings.GITHUB_BRANCH}/{directory}"

            return {
                "datadoc_id": datadoc_id,
                "directory": directory,
                "file_path": file_path,
                "linked": True,
                "github_url": github_url,
                "next_steps": [
                    "Use commit_datadoc_github to push your first commit",
                    f"View directory at: {github_url}",
                ],
                "datadoc_resource_uri": f"querybook://datadoc/{datadoc_id}",
            }

    @mcp.tool(
        title="Unlink DataDoc from GitHub",
        annotations=DELETE_ANNOTATIONS,
    )
    def unlink_datadoc_github(
        datadoc_id: Annotated[int, "DataDoc ID"],
        token: AccessToken = CurrentAccessToken(),
    ) -> dict:
        """
        Remove GitHub version control from a DataDoc.

        This only removes the link in Querybook - the file in GitHub
        is not deleted. You can manually delete it later if needed.
        """
        uid = token.claims["creator_uid"]

        with DBSession() as session:
            if not user_can_write(datadoc_id, uid=uid, session=session):
                raise AuthorizationError(
                    action="write", resource=f"datadoc:{datadoc_id}"
                )

            github_link = github_logic.get_repo_link(datadoc_id, session=session)

            if not github_link:
                return {
                    "datadoc_id": datadoc_id,
                    "unlinked": False,
                    "message": "DataDoc was not linked to GitHub",
                }

            file_path = f"{github_link.directory}/datadoc_{datadoc_id}.md"
            github_url = f"https://github.com/{QuerybookSettings.GITHUB_REPO_NAME}/blob/{QuerybookSettings.GITHUB_BRANCH}/{file_path}"

            # Delete the link
            session.delete(github_link)
            session.commit()

            return {
                "datadoc_id": datadoc_id,
                "unlinked": True,
                "previous_directory": github_link.directory,
                "previous_file_path": file_path,
                "message": (
                    f"DataDoc unlinked from GitHub. The file at {file_path} "
                    "still exists in the repository. Delete manually if needed."
                ),
                "github_file_url": github_url,
            }

    @mcp.tool(
        title="Commit DataDoc to GitHub",
        annotations=WRITE_ANNOTATIONS,
    )
    def commit_datadoc_github(
        datadoc_id: Annotated[int, "DataDoc ID"],
        commit_message: Annotated[
            str | None,
            "Commit message. Auto-generated if not provided. See "
            "querybook://reference/github for commit message guidance.",
        ] = None,
        token: AccessToken = CurrentAccessToken(),
    ) -> dict:
        """
        Push the current DataDoc state to GitHub as a commit.

        Creates or updates the markdown file in GitHub with the DataDoc's
        current content. Commits made via MCP are automatically tagged with
        metadata for auditing and analytics. See querybook://reference/github.
        """
        uid = token.claims["creator_uid"]

        with DBSession() as session:
            if not user_can_write(datadoc_id, uid=uid, session=session):
                raise AuthorizationError(
                    action="write", resource=f"datadoc:{datadoc_id}"
                )

            # Check if linked
            github_link = github_logic.get_repo_link(datadoc_id, session=session)
            if not github_link:
                raise ValueError(
                    f"DataDoc {datadoc_id} is not linked to GitHub. "
                    "Use link_datadoc_github first."
                )

            # Get user and datadoc info
            user = get_user_by_id(uid, session=session)
            datadoc = github_link.datadoc

            # Build commit metadata for tagging
            commit_metadata = {
                "source": "mcp",
                "tool": "commit_datadoc_github",
                "user": user.username,
                "uid": uid,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "client": "querybook-mcp",  # Could be enhanced to detect client
                "api_token_suffix": get_token_suffix(token),
            }

            # Generate commit message with metadata
            if not commit_message:
                commit_message = f"Update DataDoc {datadoc_id}"
                if datadoc.title:
                    commit_message += f": {datadoc.title}"

            full_commit_message = format_commit_message(
                user_message=commit_message,
                metadata=commit_metadata,
                datadoc_id=datadoc_id,
            )

            # Validate DataDoc serialization before committing through GitHubClient.
            serialize_datadoc_to_markdown(datadoc, exclude_metadata=False)

            # Commit to GitHub
            github_client = _get_github_client(datadoc_id, uid, session)

            try:
                github_client.commit_datadoc(commit_message=full_commit_message)
            except Exception as e:
                LOG.error(
                    f"Failed to commit datadoc {datadoc_id} to GitHub: {e}",
                    exc_info=True,
                )
                raise ToolError(f"Failed to commit to GitHub: {str(e)}")

            # Get the commit info
            commits = github_client.get_datadoc_versions(page=1)
            latest_commit = commits[0] if commits else None

            result = {
                "success": True,
                "datadoc_id": datadoc_id,
                "file_path": github_client.file_path,
                "message": commit_message,
                "datadoc_resource_uri": f"querybook://datadoc/{datadoc_id}",
            }

            if latest_commit:
                result["commit_sha"] = latest_commit["sha"]
                result["commit_url"] = latest_commit["html_url"]

            return result

    @mcp.tool(
        title="Compare DataDoc with GitHub Version",
        annotations=READ_ONLY_ANNOTATIONS,
    )
    def compare_datadoc_github_version(
        datadoc_id: Annotated[int, "DataDoc ID"],
        commit_sha: Annotated[str, "Commit SHA to compare against"],
        token: AccessToken = CurrentAccessToken(),
    ) -> dict:
        """
        Compare the current DataDoc with a specific GitHub commit.

        Returns both the current content and the commit content as markdown,
        allowing you to see what changed between versions. See
        querybook://reference/github for history workflows.
        """
        uid = token.claims["creator_uid"]

        with DBSession() as session:
            if not user_can_read(datadoc_id, uid=uid, session=session):
                raise AuthorizationError(
                    action="read", resource=f"datadoc:{datadoc_id}"
                )

            github_client = _get_github_client(datadoc_id, uid, session)
            datadoc = datadoc_logic.get_data_doc_by_id(datadoc_id, session=session)

            if not datadoc:
                raise ValueError(f"DataDoc {datadoc_id} not found")

            # Get current content
            current_markdown = serialize_datadoc_to_markdown(
                datadoc, exclude_metadata=True
            )

            # Get commit content
            try:
                commit_datadoc = github_client.get_datadoc_at_commit(commit_sha)
                commit_markdown = serialize_datadoc_to_markdown(
                    commit_datadoc, exclude_metadata=True
                )
            except Exception as e:
                raise ToolError(f"Failed to get commit {commit_sha}: {str(e)}")

            # Get commit info
            try:
                commits = github_client.get_datadoc_versions(page=1)
                commit_info = next(
                    (c for c in commits if c["sha"].startswith(commit_sha)), None
                )
            except Exception as e:
                LOG.warning(f"Could not fetch commit info for {commit_sha}: {e}")
                commit_info = None

            github_file_url = f"https://github.com/{QuerybookSettings.GITHUB_REPO_NAME}/blob/{commit_sha}/{github_client.file_path}"
            diff_url = f"https://github.com/{QuerybookSettings.GITHUB_REPO_NAME}/commit/{commit_sha}"

            result = {
                "datadoc_id": datadoc_id,
                "current_content": current_markdown,
                "commit_content": commit_markdown,
                "commit_sha": commit_sha,
                "github_file_url": github_file_url,
                "github_diff_url": diff_url,
            }

            if commit_info:
                result["commit_info"] = serialize_commit(commit_info)

            return result

    @mcp.tool(
        title="Restore DataDoc from GitHub",
        annotations=WRITE_ANNOTATIONS,
    )
    def restore_datadoc_from_github(
        datadoc_id: Annotated[int, "DataDoc ID"],
        commit_sha: Annotated[str, "Commit SHA to restore from"],
        token: AccessToken = CurrentAccessToken(),
    ) -> dict:
        """
        Restore a DataDoc to a previous GitHub commit state.

        Replaces the current DataDoc content with the content from
        the specified commit. This is reversible - you can restore
        to any other commit including the current state. See
        querybook://reference/github for restore guidance.
        """
        uid = token.claims["creator_uid"]

        with DBSession() as session:
            if not user_can_write(datadoc_id, uid=uid, session=session):
                raise AuthorizationError(
                    action="write", resource=f"datadoc:{datadoc_id}"
                )

            github_client = _get_github_client(datadoc_id, uid, session)

            # Get the commit content
            try:
                commit_datadoc = github_client.get_datadoc_at_commit(commit_sha)
            except Exception as e:
                raise ToolError(f"Failed to get commit {commit_sha}: {str(e)}")

            # Get commit info for the response
            try:
                commits = github_client.get_datadoc_versions(page=1)
                commit_info = next(
                    (c for c in commits if c["sha"].startswith(commit_sha)), None
                )
                commit_message = (
                    commit_info["commit"]["message"] if commit_info else commit_sha
                )
            except Exception as e:
                LOG.debug(f"Could not extract commit message from {commit_sha}: {e}")
                commit_message = f"Restored to {commit_sha[:7]} via MCP"

            # Restore the DataDoc using existing logic
            restore_data_doc_from_commit(
                datadoc_id=datadoc_id,
                commit_datadoc=commit_datadoc,
                commit=True,
                session=session,
            )

            return {
                "success": True,
                "datadoc_id": datadoc_id,
                "restored_from_sha": commit_sha,
                "restored_from_message": commit_message,
                "message": f"DataDoc restored to commit {commit_sha[:7]}",
                "datadoc_resource_uri": f"querybook://datadoc/{datadoc_id}",
            }
