"""Tests for OktaOIDCProvider auth helpers."""

import asyncio
import base64
import json
from types import SimpleNamespace

import pytest
from fastmcp.server.auth.oidc_proxy import OIDCProxy

from lib.mcp import okta_auth
from lib.mcp.okta_auth import OktaOIDCProvider, _fastmcp_token_audit_claims


def _make_jwt(claims: dict) -> str:
    """Build a structurally-valid (unsigned) JWT string with the given claims."""
    segment = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=")
    return "header." + segment.decode() + ".signature"


def test_rejected_expired_shaped_jwt_records_failure(monkeypatch):
    """A rejected JWT with an old exp is still an auth failure.

    Expiry cannot be classified from an unverified payload because a forged token
    can carry any exp it wants. The upstream verifier has already rejected this
    token, so the audit path must keep it as a security signal.
    """
    calls = []

    async def fake_verify_token(self, token):
        return None

    monkeypatch.setattr(OIDCProxy, "verify_token", fake_verify_token)
    monkeypatch.setattr(
        okta_auth,
        "record_auth_failure",
        lambda reason, method: calls.append((reason, method)),
    )

    provider = _bare_provider()
    provider._allow_api_tokens = False

    result = asyncio.run(
        provider.verify_token(_make_jwt({"exp": 1, "sub": "attacker"}))
    )

    assert result is None
    assert calls == [("invalid_oauth_token", "oauth")]


def test_fastmcp_token_audit_claims_returns_verified_claims():
    jwt_issuer = SimpleNamespace(
        verify_token=lambda token: {"client_id": "claude", "jti": "jti-123"}
    )

    assert _fastmcp_token_audit_claims(jwt_issuer, "signed-token") == {
        "client_id": "claude",
        "jti": "jti-123",
    }


def test_fastmcp_token_audit_claims_fails_soft():
    def fail(_token):
        raise ValueError("bad token")

    jwt_issuer = SimpleNamespace(verify_token=fail)
    assert _fastmcp_token_audit_claims(jwt_issuer, "signed-token") == {}


def test_extract_upstream_claims_embeds_creator_uid(monkeypatch):
    async def verify_token(token):
        assert token == "id-token"
        return SimpleNamespace(claims={"preferred_username": "alice"})

    monkeypatch.setattr(
        okta_auth,
        "_get_or_create_querybook_user_id",
        lambda claims: 99,
    )

    provider = _bare_provider()
    provider._verify_id_token = True
    provider._token_validator = SimpleNamespace(verify_token=verify_token)

    assert asyncio.run(provider._extract_upstream_claims({"id_token": "id-token"})) == {
        "creator_uid": 99
    }


# -- Token issuance / refresh overrides (8.2) -------------------------------
# The exchange_* overrides are thin recorders: delegate to super(), then record
# the credential-lifecycle outcome. Built with object.__new__ to skip the heavy
# Redis/OIDC constructor; the parent exchange is patched via the MRO.


@pytest.fixture
def capture_issuance(monkeypatch):
    calls = []
    monkeypatch.setattr(
        okta_auth,
        "record_token_issuance",
        lambda reason, method, success, **kwargs: calls.append(
            (reason, method, success, kwargs)
        ),
    )
    return calls


def _bare_provider():
    return object.__new__(OktaOIDCProvider)


def test_exchange_authorization_code_records_success(monkeypatch, capture_issuance):
    async def fake_super(self, client, authorization_code):
        return SimpleNamespace(access_token="issued-token")

    monkeypatch.setattr(OIDCProxy, "exchange_authorization_code", fake_super)
    provider = _bare_provider()
    # jwt_issuer is a read-only property on OIDCProxy; shadow it on the subclass
    # so instance lookup resolves to this fake issuer.
    monkeypatch.setattr(
        OktaOIDCProvider,
        "jwt_issuer",
        SimpleNamespace(
            verify_token=lambda token: {
                "client_id": "claude",
                "upstream_claims": {"creator_uid": 42},
            }
        ),
        raising=False,
    )
    client = SimpleNamespace(client_id="claude")
    result = asyncio.run(provider.exchange_authorization_code(client, None))
    assert result.access_token == "issued-token"
    assert capture_issuance[0][:3] == ("token_issued", "oauth", True)
    assert capture_issuance[0][3]["subject"] == 42
    assert capture_issuance[0][3]["client_id"] == "claude"
    assert capture_issuance[0][3]["session_id"] is not None
    assert "issued-token" not in capture_issuance[0][3]["session_id"]


def test_exchange_authorization_code_records_failure(monkeypatch, capture_issuance):
    async def fake_super(self, client, authorization_code):
        raise ValueError("invalid_grant")

    monkeypatch.setattr(OIDCProxy, "exchange_authorization_code", fake_super)
    with pytest.raises(ValueError):
        asyncio.run(_bare_provider().exchange_authorization_code(None, None))
    assert capture_issuance == [
        (
            "token_issuance_failed",
            "oauth",
            False,
            {"subject": 0, "client_id": None, "session_id": None},
        )
    ]


def test_exchange_refresh_token_records_success(monkeypatch, capture_issuance):
    async def fake_super(self, client, refresh_token, scopes):
        return SimpleNamespace(access_token="refreshed-token")

    monkeypatch.setattr(OIDCProxy, "exchange_refresh_token", fake_super)
    provider = _bare_provider()
    # jwt_issuer is a read-only property on OIDCProxy; shadow it on the subclass
    # so instance lookup resolves to this fake issuer.
    monkeypatch.setattr(
        OktaOIDCProvider,
        "jwt_issuer",
        SimpleNamespace(
            verify_token=lambda token: {
                "client_id": "cursor",
                "upstream_claims": {"creator_uid": 84},
            }
        ),
        raising=False,
    )
    client = SimpleNamespace(client_id="cursor")
    result = asyncio.run(provider.exchange_refresh_token(client, None, []))
    assert result.access_token == "refreshed-token"
    assert capture_issuance[0][:3] == ("token_refreshed", "oauth", True)
    assert capture_issuance[0][3]["subject"] == 84
    assert capture_issuance[0][3]["client_id"] == "cursor"
    assert capture_issuance[0][3]["session_id"] is not None


def test_exchange_refresh_token_records_failure(monkeypatch, capture_issuance):
    async def fake_super(self, client, refresh_token, scopes):
        raise ValueError("upstream refresh failed")

    monkeypatch.setattr(OIDCProxy, "exchange_refresh_token", fake_super)
    with pytest.raises(ValueError):
        asyncio.run(_bare_provider().exchange_refresh_token(None, None, []))
    assert capture_issuance == [
        (
            "token_refresh_failed",
            "oauth",
            False,
            {"subject": 0, "client_id": None, "session_id": None},
        )
    ]
