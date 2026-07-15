"""Unit tests for the MCP audit redaction module.

The real deliverable is the negative+positive corpus: a precision-over-recall
redactor must leave benign analytic values (bigint ids, version strings, UUIDs,
row counts, dates) untouched while reliably scrubbing emails, SSNs, Luhn-valid
cards, bearer tokens, JWTs, formatted phones, and secret-keyed dict values.
"""

import pytest

from lib.mcp.redact import (
    PLACEHOLDER_CARD,
    PLACEHOLDER_EMAIL,
    PLACEHOLDER_IP,
    PLACEHOLDER_JWT,
    PLACEHOLDER_PHONE,
    PLACEHOLDER_SECRET,
    PLACEHOLDER_SSN,
    PLACEHOLDER_TOKEN,
    redact,
    redact_text,
)

# --------------------------------------------------------------------------- #
# Negative corpus: redact_text must return the string unchanged.
# --------------------------------------------------------------------------- #
NEGATIVE_TEXT = [
    pytest.param(
        "SELECT * FROM orders WHERE order_id = 1234567890123",
        id="bigint_13_digits_luhn_fail",
    ),
    pytest.param(
        "SELECT * FROM t WHERE id IN (100000000, 200000000, 300000000)",
        id="nine_digit_id_list",
    ),
    pytest.param("WHERE phone_col = 4155551234", id="bare_10_digit_phone"),
    pytest.param("WHERE ssn_raw = 123456789", id="bare_9_digit_ssn"),
    pytest.param("version = '1.2.3.4'", id="version_string_ip_off"),
    pytest.param("app_version = 10.20.30.40", id="app_version_ip_off"),
    pytest.param("id = '550e8400-e29b-41d4-a716-446655440000'", id="uuid_unchanged"),
    pytest.param("LIMIT 1000 OFFSET 50000", id="limit_offset"),
    pytest.param(
        "WHERE created_at BETWEEN DATE '2026-01-01' AND DATE '2026-06-22'",
        id="date_range",
    ),
    pytest.param(
        "SELECT customer_id, account_number, card_network FROM dim_customer",
        id="benign_column_names",
    ),
    pytest.param(
        "WHERE invoice_number = '4000000000000001'",
        id="sixteen_digit_luhn_fail",
    ),
    pytest.param("email_domain = 'localhost'", id="email_no_tld"),
    pytest.param("Bearerton AS name", id="bearer_word_only_no_token"),
    pytest.param("ip 192.168.1.1", id="ipv4_off_by_default"),
    pytest.param("WHERE delta = +1234567", id="signed_int_not_phone"),
    pytest.param("val = +12345678901", id="long_signed_int_not_phone"),
]


@pytest.mark.parametrize("text", NEGATIVE_TEXT)
def test_redact_text_leaves_benign_values_unchanged(text):
    assert redact_text(text) == text


# --------------------------------------------------------------------------- #
# Positive corpus: redact_text must scrub and emit the right placeholder.
# --------------------------------------------------------------------------- #
POSITIVE_TEXT = [
    pytest.param(
        "WHERE email = 'jane.doe@expediagroup.com'",
        PLACEHOLDER_EMAIL,
        "jane.doe@expediagroup.com",
        id="email",
    ),
    pytest.param(
        "WHERE ssn = '123-45-6789'",
        PLACEHOLDER_SSN,
        "123-45-6789",
        id="ssn_dashed",
    ),
    pytest.param(
        "card = '4242424242424242'",
        PLACEHOLDER_CARD,
        "4242424242424242",
        id="card_luhn_valid",
    ),
    pytest.param(
        "card2 = '4000 0566 5566 5556'",
        PLACEHOLDER_CARD,
        "4000 0566 5566 5556",
        id="card_spaced_luhn_valid",
    ),
    pytest.param(
        "JWT eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0."
        "dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U",
        PLACEHOLDER_JWT,
        "eyJhbGci",
        id="jwt",
    ),
    pytest.param(
        "phone = '+1 (415) 555-1234'",
        PLACEHOLDER_PHONE,
        "415",
        id="phone_intl",
    ),
    pytest.param(
        "phone = '415-555-1234'",
        PLACEHOLDER_PHONE,
        "555-1234",
        id="phone_us",
    ),
]


@pytest.mark.parametrize("text,placeholder,leaked", POSITIVE_TEXT)
def test_redact_text_scrubs_sensitive_values(text, placeholder, leaked):
    out = redact_text(text)
    assert placeholder in out
    assert leaked not in out


def test_bearer_keeps_prefix_and_redacts_token():
    out = redact_text("Authorization: Bearer abc.def.ghi123")
    assert out == "Authorization: Bearer " + PLACEHOLDER_TOKEN


def test_mixed_text_redacts_all_three_and_preserves_punctuation():
    out = redact_text(
        "INSERT INTO t VALUES ('jane@x.com', '123-45-6789', 4242424242424242)"
    )
    assert out == (
        "INSERT INTO t VALUES ('"
        + PLACEHOLDER_EMAIL
        + "', '"
        + PLACEHOLDER_SSN
        + "', "
        + PLACEHOLDER_CARD
        + ")"
    )


def test_dashed_ssn_adjacent_to_card_redacts_both():
    """A dashed SSN directly abutting a card must not shield the card.

    The card candidate pattern allows single space/hyphen separators, so an
    SSN immediately followed by a card would merge into one over-long,
    Luhn-failing digit run and leak the card. SSN is substituted before card
    precisely to prevent this; both must end up redacted.
    """
    out = redact_text("123-45-6789 4111 1111 1111 1111")
    assert out == PLACEHOLDER_SSN + " " + PLACEHOLDER_CARD
    assert "4111" not in out


# --------------------------------------------------------------------------- #
# Size capping (max_len) -- one traversal redacts and size-bounds the payload.
# --------------------------------------------------------------------------- #
def test_max_len_caps_after_redaction():
    out = redact_text("SELECT " + "a" * 200, max_len=128)
    assert out == "SELECT " + "a" * 121 + "..."
    assert len(out) == 131  # 128 + "..."


def test_max_len_leaves_short_strings_alone():
    assert redact_text("SELECT 1", max_len=128) == "SELECT 1"


def test_max_len_redacts_before_truncating():
    # A secret near the front is scrubbed even though the value is over-length;
    # truncation never exposes a tail the redactor would have caught.
    out = redact_text("jane@x.com " + "x" * 200, max_len=128)
    assert PLACEHOLDER_EMAIL in out
    assert "jane@x.com" not in out
    assert out.endswith("...")


def test_max_len_caps_string_leaves_in_structure():
    out = redact({"query": "x" * 200, "id": 5}, max_len=128)
    assert out["query"] == "x" * 128 + "..."
    assert out["id"] == 5


def test_max_len_is_idempotent():
    once = redact_text("y" * 200, max_len=128)
    assert redact_text(once, max_len=128) == once


# --------------------------------------------------------------------------- #
# IP gating behavior.
# --------------------------------------------------------------------------- #
def test_ip_off_by_default():
    assert redact_text("ip 192.168.1.1") == "ip 192.168.1.1"


def test_ip_redacted_when_enabled():
    out = redact_text("ip 192.168.1.1", include_ip=True)
    assert out == "ip " + PLACEHOLDER_IP
    assert "192.168.1.1" not in out


def test_ipv6_redacted_when_enabled():
    # A ``::``-compressed address must be redacted in full — no prefix leak.
    out = redact_text("addr 2001:db8::ff00:42:8329", include_ip=True)
    assert out == "addr " + PLACEHOLDER_IP
    assert "2001" not in out and "8329" not in out


def test_ipv6_full_form_redacted_when_enabled():
    out = redact_text("addr 2001:0db8:0000:0000:0000:ff00:0042:8329", include_ip=True)
    assert out == "addr " + PLACEHOLDER_IP


def test_ipv6_compressed_prefix_forms_redacted_when_enabled():
    for addr in ("::1", "fe80::1"):
        out = redact_text(f"addr {addr}", include_ip=True)
        assert out == "addr " + PLACEHOLDER_IP


def test_ipv6_pattern_does_not_touch_colon_tokens():
    # Times and MAC addresses share the hex/colon alphabet but are not IPv6
    # (no ``::`` run, not a full 8-group address); they must survive.
    for token in ("time 12:34:56", "mac 01:23:45:67:89:ab"):
        assert redact_text(token, include_ip=True) == token


# --------------------------------------------------------------------------- #
# Idempotence.
# --------------------------------------------------------------------------- #
def test_redact_text_is_idempotent():
    s = (
        "email jane@x.com ssn 123-45-6789 card 4242424242424242 "
        "Bearer abc.def token JWT "
        "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ4In0.AAAA phone 415-555-1234"
    )
    once = redact_text(s)
    twice = redact_text(once)
    assert once == twice


# --------------------------------------------------------------------------- #
# Structured redaction via redact().
# --------------------------------------------------------------------------- #
NEGATIVE_STRUCT = [
    pytest.param(
        {"limit": 100, "datadoc_id": 42, "query": "SELECT 1"},
        id="benign_args",
    ),
    pytest.param(
        {"token_count": 5, "tokenizer": "bert"},
        id="word_aware_benign_secret_like_keys",
    ),
    pytest.param(
        {"tokenize_flag": True, "n_tokens": 3},
        id="more_benign_token_keys",
    ),
    pytest.param(
        {"partition_key": "dt", "sort_key": "id", "primary_key": "pk"},
        id="benign_key_typed_columns",
    ),
    pytest.param(
        {"idempotency_key": "abc-123"},
        id="idempotency_key_not_secret",
    ),
]


@pytest.mark.parametrize("value", NEGATIVE_STRUCT)
def test_redact_leaves_benign_structures_unchanged(value):
    assert redact(value) == value


SECRET_DICTS = [
    pytest.param({"password": "hunter2"}, id="password"),
    pytest.param({"api_key": "sk-live-xyz"}, id="api_key"),
    pytest.param({"client_secret": "shhh"}, id="client_secret"),
    pytest.param({"token": "raw"}, id="token"),
    pytest.param({"access_token": "raw"}, id="access_token"),
    pytest.param({"refresh_token": "raw"}, id="refresh_token"),
    pytest.param({"authorization": "Bearer raw"}, id="authorization"),
    pytest.param({"private_key": "-----BEGIN"}, id="private_key"),
    pytest.param({"credentials": "raw"}, id="credentials"),
    pytest.param({"db_password": "p"}, id="db_password_segment_match"),
    pytest.param({"secret_key": "raw"}, id="secret_key_segment_match"),
    pytest.param({"secret_value": "raw"}, id="secret_value_segment_match"),
    pytest.param(
        {"aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG"},
        id="aws_secret_access_key_segment_match",
    ),
    pytest.param({"signing_key": "raw"}, id="signing_key"),
    pytest.param({"encryption_key": "raw"}, id="encryption_key"),
    # Prefixed compound keys must redact too -- the secret noun is the suffix,
    # not the whole key (regression: these leaked when SECRET_KEYS stored the
    # underscored spelling but matching joined segments separator-free).
    pytest.param({"svc_private_key": "raw"}, id="prefixed_private_key"),
    pytest.param({"svc_signing_key": "raw"}, id="prefixed_signing_key"),
    pytest.param({"app_encryption_key": "raw"}, id="prefixed_encryption_key"),
    pytest.param({"svc_api_key": "raw"}, id="prefixed_api_key"),
    pytest.param({"aws_access_token": "raw"}, id="prefixed_access_token"),
]


@pytest.mark.parametrize("value", SECRET_DICTS)
def test_secret_keyed_values_fully_redacted(value):
    out = redact(value)
    (key,) = value.keys()
    assert out[key] == PLACEHOLDER_SECRET


def test_secret_key_redacts_non_string_value():
    # On a secret-key match the value is replaced regardless of its shape.
    assert redact({"api_key": ["a", "b"]})["api_key"] == PLACEHOLDER_SECRET
    assert redact({"secret": {"nested": 1}})["secret"] == PLACEHOLDER_SECRET


def test_nested_secret_key_recurses():
    out = redact({"config": {"db_password": "p"}})
    assert out["config"]["db_password"] == PLACEHOLDER_SECRET


def test_only_sensitive_field_redacted_others_untouched():
    out = redact({"email": "u@x.com", "username": "u", "id": 5})
    assert out["email"] == PLACEHOLDER_EMAIL
    assert out["username"] == "u"
    assert out["id"] == 5


# --------------------------------------------------------------------------- #
# Scalar passthrough and structure preservation.
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("scalar", [5, 3.14, True, False, None])
def test_redact_returns_non_str_scalars_unchanged(scalar):
    assert redact(scalar) is scalar


def test_redact_preserves_dict_order_and_list_structure():
    value = {
        "a": 1,
        "items": ["SELECT 1", {"b": 2}, "jane@x.com"],
        "z": "end",
    }
    out = redact(value)
    assert list(out.keys()) == ["a", "items", "z"]
    assert out["items"][0] == "SELECT 1"
    assert out["items"][1] == {"b": 2}
    assert out["items"][2] == PLACEHOLDER_EMAIL
    assert isinstance(out["items"], list)
