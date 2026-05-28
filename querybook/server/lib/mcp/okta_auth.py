import hashlib

from cryptography.fernet import Fernet
from fastmcp.server.auth import AccessToken
from fastmcp.server.auth.jwt_issuer import derive_jwt_key
from fastmcp.server.auth.oidc_proxy import OIDCProxy
from pydantic import AnyHttpUrl
from key_value.aio.stores.redis import RedisStore
from key_value.aio.wrappers.encryption import FernetEncryptionWrapper

from app.db import DBSession
from env import QuerybookSettings
from lib.logger import get_logger
from lib.mcp.auth import QuerybookTokenVerifier
from logic.user import create_user, get_user_by_name

LOG = get_logger(__file__)


def _derive_mcp_jwt_signing_key(auth_secret: str) -> bytes:
    return derive_jwt_key(
        high_entropy_material=auth_secret,
        salt="querybook-mcp-jwt-signing-key",
    )


def _derive_mcp_storage_encryption_key(auth_secret: str) -> bytes:
    return derive_jwt_key(
        high_entropy_material=auth_secret,
        salt="querybook-mcp-storage-encryption-key",
    )


def _build_redis_storage(auth_secret: str) -> FernetEncryptionWrapper:
    """Build an encrypted Redis-backed storage for OAuth state.

    Mirrors FastMCP's default file-based encrypted storage but uses Redis
    for horizontal scalability.
    """
    from redis.asyncio import Redis

    encryption_key = _derive_mcp_storage_encryption_key(auth_secret)
    key_fingerprint = hashlib.sha256(encryption_key).hexdigest()[:12]

    # Pass a pre-built client so RedisStore doesn't try to manage its lifecycle
    # (avoids .aclose() incompatibility with redis<5).
    redis_client = Redis.from_url(QuerybookSettings.REDIS_URL, decode_responses=True)
    redis_store = RedisStore(
        client=redis_client,
        default_collection=f"mcp-oauth:{key_fingerprint}",
    )
    return FernetEncryptionWrapper(
        key_value=redis_store,
        fernet=Fernet(key=encryption_key),
        raise_on_decryption_error=False,
    )


class OktaOIDCProvider(OIDCProxy):
    """Okta OIDC proxy for MCP OAuth authentication.

    Bridges Okta OAuth with MCP's dynamic client registration expectations
    using FastMCP's OIDCProxy, and resolves Okta identity to Querybook user IDs.
    """

    def __init__(
        self,
        *,
        config_url,
        client_id,
        client_secret,
        auth_secret,
        base_url,
        allow_api_tokens=True,
    ):
        super().__init__(
            config_url=config_url,
            client_id=client_id,
            client_secret=client_secret,
            base_url=base_url,
            required_scopes=["openid", "email", "profile", "offline_access"],
            token_endpoint_auth_method="client_secret_post",
            require_authorization_consent=True,
            verify_id_token=True,
            allowed_client_redirect_uris=QuerybookSettings.MCP_OAUTH_ALLOWED_REDIRECT_URIS,
            enable_cimd=False,
            jwt_signing_key=_derive_mcp_jwt_signing_key(auth_secret),
            client_storage=_build_redis_storage(auth_secret),
        )
        self._allow_api_tokens = allow_api_tokens
        self._token_verifier = QuerybookTokenVerifier() if allow_api_tokens else None

    def _get_resource_url(self, path: str | None = None) -> AnyHttpUrl | None:
        if self.base_url is None:
            return None
        base = str(self.base_url).rstrip("/")
        if not base.endswith("/mcp"):
            base = f"{base}/mcp"
        return AnyHttpUrl(base)

    async def verify_token(self, token: str) -> AccessToken | None:
        if _is_api_token(token):
            token_hint = token[:8] + "..."
            if self._allow_api_tokens:
                api_result = await self._token_verifier.verify_token(token)
                if api_result is not None:
                    api_result.scopes = list(self.required_scopes)
                    return api_result
                LOG.warning("API key rejected (invalid or revoked): %s", token_hint)
            else:
                LOG.warning(
                    "API key rejected (server requires OAuth): %s — "
                    "client must remove 'headers' block from MCP config",
                    token_hint,
                )
            return None

        validated = await super().verify_token(token)
        if validated is None:
            return None

        username = validated.claims.get("preferred_username")
        if not username:
            LOG.warning("OAuth token missing preferred_username claim")
            return None

        email = validated.claims.get("email")
        fullname = validated.claims.get("name")

        with DBSession() as session:
            user = get_user_by_name(username, session=session)
            if not user:
                LOG.info("Creating new user from OAuth login: %s", username)
                user = create_user(
                    username=username,
                    fullname=fullname,
                    email=email,
                    session=session,
                )
                _sync_new_user(username)

            validated.claims["creator_uid"] = user.id
            validated.claims["auth_method"] = "oauth"

        # id_tokens don't carry scope claims, so the parent's verify_token
        # returns empty scopes. Populate them so the bearer auth middleware
        # doesn't reject with "insufficient_scope".
        validated.scopes = list(self.required_scopes)
        return validated


def _is_api_token(token: str) -> bool:
    return len(token) == 32 and all(c in "0123456789abcdef" for c in token)


def _sync_new_user(username: str):
    """Sync LDAP groups for first-time OAuth users (best-effort)."""
    try:
        from tasks_plugin import sync_ldap_user_task

        sync_ldap_user_task(username=username)
    except Exception:
        LOG.debug("LDAP sync unavailable for new user: %s", username)
