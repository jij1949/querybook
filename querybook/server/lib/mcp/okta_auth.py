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
from lib.mcp.audit import (
    record_auth_failure,
    record_auth_success,
    record_token_issuance,
)
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
                # The inner verifier records its own success/failure outcome.
                api_result = await self._token_verifier.verify_token(token)
                if api_result is not None:
                    api_result.scopes = list(self.required_scopes)
                    return api_result
                LOG.warning("API key rejected (invalid or revoked): %s", token_hint)
            else:
                record_auth_failure("api_token_not_allowed", "api_token")
                LOG.warning(
                    "API key rejected (server requires OAuth): %s — "
                    "client must remove 'headers' block from MCP config",
                    token_hint,
                )
            return None

        validated = await super().verify_token(token)
        if validated is None:
            # super() collapses every rejection cause to None. Do not classify
            # expiry from the unverified JWT payload: a forged token can carry an
            # old exp and would otherwise be downgraded from security signal to a
            # routine expiry event.
            record_auth_failure("invalid_oauth_token", "oauth")
            return None

        fastmcp_claims = _fastmcp_token_audit_claims(self.jwt_issuer, token)
        creator_uid = _get_or_create_querybook_user_id(validated.claims)
        if creator_uid is None:
            record_auth_failure("oauth_missing_username", "oauth")
            LOG.warning("OAuth token missing preferred_username claim")
            return None

        validated.claims["creator_uid"] = creator_uid
        validated.claims["auth_method"] = "oauth"
        validated.claims["client_id"] = fastmcp_claims.get("client_id")
        validated.claims["session_id"] = _hash_token_value(token)

        record_auth_success("valid_oauth_token", "oauth")

        # id_tokens don't carry scope claims, so the parent's verify_token
        # returns empty scopes. Populate them so the bearer auth middleware
        # doesn't reject with "insufficient_scope".
        validated.scopes = list(self.required_scopes)
        return validated

    async def exchange_authorization_code(self, client, authorization_code):
        """Issue FastMCP tokens for an authorization code (OAuth login completion).

        Pure recorder for the token-lifecycle audit event (8.2): the /token
        request runs no tool, so record_token_issuance marks it standalone and
        RequestAuditMiddleware emits it at the boundary.
        """
        try:
            token = await super().exchange_authorization_code(
                client, authorization_code
            )
            record_token_issuance(
                "token_issued",
                "oauth",
                success=True,
                **_token_audit_context(
                    token, client, getattr(self, "jwt_issuer", None)
                ),
            )
            return token
        except Exception:
            record_token_issuance(
                "token_issuance_failed",
                "oauth",
                success=False,
                **_token_audit_context(None, client, getattr(self, "jwt_issuer", None)),
            )
            raise

    async def exchange_refresh_token(self, client, refresh_token, scopes):
        """Issue a new FastMCP access token from a refresh token.

        Recorded like issuance (8.2): standalone token-lifecycle `auth` event,
        emitted at the request boundary.
        """
        try:
            token = await super().exchange_refresh_token(client, refresh_token, scopes)
            record_token_issuance(
                "token_refreshed",
                "oauth",
                success=True,
                **_token_audit_context(
                    token, client, getattr(self, "jwt_issuer", None)
                ),
            )
            return token
        except Exception:
            record_token_issuance(
                "token_refresh_failed",
                "oauth",
                success=False,
                **_token_audit_context(None, client, getattr(self, "jwt_issuer", None)),
            )
            raise

    async def _extract_upstream_claims(self, idp_tokens: dict) -> dict | None:
        """Embed the Querybook user id in FastMCP tokens issued by this proxy.

        FastMCP calls this hook during token issuance/refresh before it signs the
        client-facing JWT. We keep the embedded claim deliberately small so the
        later `auth` audit event can identify the human without exposing Okta
        profile data in the token.
        """
        verification_token = (
            idp_tokens.get("id_token")
            if getattr(self, "_verify_id_token", False)
            else idp_tokens.get("access_token")
        )
        if not verification_token:
            return None

        try:
            validated = await self._token_validator.verify_token(verification_token)
        except Exception as e:
            LOG.debug("Unable to extract upstream claims for audit context: %s", e)
            return None

        if not validated or not getattr(validated, "claims", None):
            return None

        creator_uid = _get_or_create_querybook_user_id(validated.claims)
        return {"creator_uid": creator_uid} if creator_uid is not None else None


def _is_api_token(token: str) -> bool:
    return len(token) == 32 and all(c in "0123456789abcdef" for c in token)


def _hash_token_value(value) -> str | None:
    if not value:
        return None
    return hashlib.sha256(str(value).encode()).hexdigest()


def _fastmcp_token_audit_claims(jwt_issuer, token: str) -> dict:
    """Return verified FastMCP JWT metadata safe for audit context.

    This is only audit decoration. The actual auth decision already happened in
    OIDCProxy.verify_token(); if decoding unexpectedly fails here, keep the
    request successful and emit the rest of the audit context.
    """
    try:
        claims = jwt_issuer.verify_token(token)
        return claims if isinstance(claims, dict) else {}
    except Exception as e:
        LOG.debug("Unable to decode FastMCP token for audit context: %s", e)
        return {}


def _get_or_create_querybook_user_id(claims: dict) -> int | None:
    username = claims.get("preferred_username")
    if not username:
        return None

    with DBSession() as session:
        user = get_user_by_name(username, session=session)
        if not user:
            LOG.info("Creating new user from OAuth login: %s", username)
            user = create_user(
                username=username,
                fullname=claims.get("name"),
                email=claims.get("email"),
                session=session,
            )
            _sync_new_user(username)
        return user.id


def _token_audit_context(token, client, jwt_issuer=None) -> dict:
    """Best-effort context for FastMCP OAuth token lifecycle audit events.

    The subject comes only from the verified FastMCP JWT's `upstream_claims`,
    which this provider injects via _extract_upstream_claims().
    """
    raw_token = token.access_token if token is not None else None
    fastmcp_claims = (
        _fastmcp_token_audit_claims(jwt_issuer, raw_token)
        if raw_token and jwt_issuer is not None
        else {}
    )
    upstream_claims = fastmcp_claims.get("upstream_claims") or {}
    return {
        "subject": upstream_claims.get("creator_uid", 0),
        "client_id": client.client_id if client is not None else None,
        "session_id": _hash_token_value(raw_token),
    }


def _sync_new_user(username: str):
    """Sync LDAP groups for first-time OAuth users (best-effort)."""
    try:
        from tasks_plugin import sync_ldap_user_task

        sync_ldap_user_task(username=username)
    except Exception:
        LOG.debug("LDAP sync unavailable for new user: %s", username)
