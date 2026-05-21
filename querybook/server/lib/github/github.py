import certifi
import uuid
from typing import Optional, Dict, Any
from urllib.parse import quote, unquote

from app.auth.github_auth import GitHubLoginManager
from app.auth.utils import AuthenticationError
from app.flask_app import flask_app
from clients.redis_client import get_redis
from env import QuerybookSettings
from flask import session as flask_session, request, redirect
from flask_login import current_user
from github import Github, Auth
from lib.logger import get_logger
from ..utils.token_utils import TokenManager

LOG = get_logger(__file__)

GITHUB_OAUTH_CALLBACK = "/github/oauth2callback"
GITHUB_ACCESS_TOKEN = "github_access_token"
OAUTH_STATE_KEY = "oauth_state"
MCP_OAUTH_SESSION_TTL = 300  # 5 minutes


class GitHubManager(GitHubLoginManager):
    def __init__(
        self,
        additional_scopes: Optional[list] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ):
        self.additional_scopes = additional_scopes or []
        self._client_id = client_id
        self._client_secret = client_secret
        super().__init__()

        self.token_manager = TokenManager(
            token_type=GITHUB_ACCESS_TOKEN,
            encryption_key=QuerybookSettings.GITHUB_CRYPTO_SECRET,
        )

    @property
    def oauth_config(self) -> Dict[str, Any]:
        config = super().oauth_config
        config["scope"] = "user email " + " ".join(self.additional_scopes)
        config["callback_url"] = (
            f"{QuerybookSettings.PUBLIC_URL}{GITHUB_OAUTH_CALLBACK}"
        )
        if self._client_id:
            config["client_id"] = self._client_id
        if self._client_secret:
            config["client_secret"] = self._client_secret
        return config

    def save_github_token(self, token: str) -> None:
        self.token_manager.save_token(current_user.id, token)

    def get_github_token(self, uid: int = None) -> str:
        """
        Get GitHub token for a user.

        Args:
            uid: User ID. If None, uses current_user.id from Flask context.

        Returns:
            Validated GitHub access token
        """
        user_id = uid if uid is not None else current_user.id
        token = self.token_manager.get_token(user_id)
        return self.validate_token(token)

    def validate_token(self, token: str) -> str:
        try:
            auth = Auth.Token(token)
            github_client = Github(auth=auth)
            github_user = github_client.get_user()
            if github_user and github_user.login:
                LOG.debug(f"Validated GitHub token for user: {github_user.login}")
                return token
            else:
                LOG.error("GitHub token validation failed: User login not found")
                self.token_manager.invalidate_token(current_user.id)
                raise AuthenticationError("GitHub token validation failed.")
        except Exception as e:
            LOG.error(f"GitHub API error during token validation: {e}")
            raise AuthenticationError("GitHub API error during token validation.")

    def initiate_github_integration(self) -> Dict[str, str]:
        github = self.oauth_session
        authorization_url, state = github.authorization_url(
            self.oauth_config["authorization_url"]
        )
        flask_session[OAUTH_STATE_KEY] = state
        return {"url": authorization_url}

    def initiate_mcp_oauth(self, user_id: int) -> Dict[str, str]:
        """
        Initiate OAuth flow for MCP context using Redis for state storage.

        Args:
            user_id: User ID to associate with this OAuth session

        Returns:
            Dict with session_id and initiation_url
        """
        # Generate unique session ID
        session_id = str(uuid.uuid4())

        # Store pending request in Redis
        redis_client = get_redis()
        pending_key = f"github_oauth_pending:{session_id}"
        redis_client.setex(
            pending_key,
            MCP_OAUTH_SESSION_TTL,
            str(user_id)  # Store user_id as value
        )

        # Build URL to datasource endpoint that will generate OAuth URL
        initiation_url = f"{QuerybookSettings.PUBLIC_URL}/ds/github/mcp-oauth-initiate/?session_id={session_id}"

        LOG.info(f"Initiated MCP OAuth session {session_id} for user {user_id}")

        return {
            "session_id": session_id,
            "initiation_url": initiation_url,
        }

    def github_integration_callback(self) -> str:
        try:
            github = self.oauth_session

            github_state = flask_session.pop(OAUTH_STATE_KEY, None)
            # Validate the state parameter to protect against CSRF attacks
            if github_state is None or github_state != request.args.get("state"):
                raise AuthenticationError("Invalid state parameter")

            access_token = github.fetch_token(
                self.oauth_config["token_url"],
                client_secret=self.oauth_config["client_secret"],
                authorization_response=request.url,
                cert=certifi.where(),
            )
            token = access_token["access_token"]
            self.save_github_token(token)
            return self.success_response()
        except Exception as e:
            LOG.error(f"Failed to obtain credentials: {e}")
            return self.error_response(str(e))

    def mcp_oauth_callback(self, session_id: str, state: str) -> str:
        """
        Handle OAuth callback for MCP-initiated flow.

        Args:
            session_id: MCP OAuth session ID
            state: OAuth state from GitHub

        Returns:
            HTML response for the user
        """
        try:
            redis_client = get_redis()

            # Validate session exists and get stored state
            state_key = f"github_oauth_state:{session_id}"
            stored_state = redis_client.get(state_key)

            if not stored_state:
                raise AuthenticationError("OAuth session expired or invalid")

            stored_state = stored_state.decode('utf-8')

            # Validate state matches (CSRF protection)
            if stored_state != state:
                raise AuthenticationError("Invalid state parameter")

            # Get user_id from pending request
            pending_key = f"github_oauth_pending:{session_id}"
            user_id_bytes = redis_client.get(pending_key)

            if not user_id_bytes:
                raise AuthenticationError("OAuth session not found")

            user_id = int(user_id_bytes.decode('utf-8'))

            # Exchange code for token
            # Note: OAuth codes are single-use - GitHub will reject duplicate exchanges
            github = self.oauth_session
            access_token = github.fetch_token(
                self.oauth_config["token_url"],
                client_secret=self.oauth_config["client_secret"],
                authorization_response=request.url,
                cert=certifi.where(),
            )
            token = access_token["access_token"]

            # Save token to database for this user
            self.token_manager.save_token(user_id, token)

            # Store success in Redis for MCP to poll
            complete_key = f"github_oauth_complete:{session_id}"
            redis_client.setex(complete_key, 60, "success")  # 60 second TTL

            # Cleanup Redis state
            redis_client.delete(state_key, pending_key)

            LOG.info(f"MCP OAuth completed successfully for user {user_id}, session {session_id}")

            return self.success_response()

        except Exception as e:
            LOG.error(f"MCP OAuth callback failed: {e}")
            return self.error_response(str(e))

    def success_response(self) -> str:
        return """
            <p>Success! Please close the tab.</p>
            <script>
                window.opener.receiveChildMessage()
            </script>
        """

    def error_response(self, error_message: str) -> str:
        return f"""
            <p>Failed to obtain credentials, reason: {error_message}</p>
        """

    def invalidate_token(self, uid: int = None) -> None:
        """
        Invalidate the GitHub token for a user.

        Args:
            uid: User ID. If None, uses current_user.id from Flask context.
        """
        user_id = uid if uid is not None else current_user.id
        self.token_manager.invalidate_token(user_id)
        LOG.info("GitHub token invalidated for user: %s", user_id)


github_manager = GitHubManager(
    additional_scopes=["repo"],
    client_id=QuerybookSettings.GITHUB_CLIENT_ID,
    client_secret=QuerybookSettings.GITHUB_CLIENT_SECRET,
)


@flask_app.route(GITHUB_OAUTH_CALLBACK)
def github_callback() -> str:
    """
    OAuth callback handling both web UI and MCP flows.
    Checks if state contains MCP session_id marker.
    """
    state = request.args.get("state", "")
    # URL decode the state parameter since we encode it when generating the URL
    state = unquote(state)

    # Check if this is an MCP-initiated OAuth (state contains "mcp:" prefix)
    if "|mcp:" in state:
        # Extract session_id from state
        parts = state.split("|mcp:")
        if len(parts) == 2:
            oauth_state = parts[0]
            session_id = parts[1]
            return github_manager.mcp_oauth_callback(session_id, oauth_state)

    # Regular web UI flow
    return github_manager.github_integration_callback()


@flask_app.route("/github/mcp-oauth-initiate")
def mcp_oauth_initiate() -> str:
    """
    Initiate OAuth flow from MCP context.
    Validates session_id from Redis, generates OAuth URL, and auto-redirects.
    """
    session_id = request.args.get("session_id")
    if not session_id:
        return github_manager.error_response("Missing session_id parameter")

    try:
        redis_client = get_redis()

        # Validate session exists
        pending_key = f"github_oauth_pending:{session_id}"
        user_id_bytes = redis_client.get(pending_key)

        if not user_id_bytes:
            return github_manager.error_response(
                "OAuth session not found or expired. Please try again."
            )

        # Generate OAuth URL with custom state containing session_id
        github = github_manager.oauth_session

        # Include session_id in state parameter (format: "oauth_state|session_id")
        authorization_url, oauth_state = github.authorization_url(
            github_manager.oauth_config["authorization_url"]
        )

        # Embed session_id in the state parameter with proper URL encoding
        combined_state = f"{oauth_state}|mcp:{session_id}"
        encoded_combined_state = quote(combined_state, safe='')
        authorization_url = authorization_url.replace(
            f"state={oauth_state}",
            f"state={encoded_combined_state}"
        )

        # Store OAuth state in Redis (keyed by session_id)
        state_key = f"github_oauth_state:{session_id}"
        redis_client.setex(state_key, MCP_OAUTH_SESSION_TTL, oauth_state)

        LOG.info(f"Redirecting to GitHub OAuth for MCP session {session_id}")

        # Auto-redirect to GitHub
        return redirect(authorization_url)

    except Exception as e:
        LOG.error(f"Failed to initiate MCP OAuth: {e}")
        return github_manager.error_response(str(e))
