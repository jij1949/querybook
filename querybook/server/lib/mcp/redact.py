"""Best-effort PII/secret redaction for MCP audit payloads.

Audit envelopes carry tool arguments and results that may contain sensitive
values (SQL text, request bodies, credential-bearing dicts). This module applies
a fixed set of value-pattern redactors to free text, plus key-name secret
detection when descending into structured dicts.

Design stance is **precision over recall**: every pattern is tightened with
false-positive guards so that benign analytic values (bigint ids, version
strings, UUIDs, row counts, dates) survive unredacted. The cost is a documented
set of residuals (see below) that are intentionally NOT redacted.

Intentionally un-redacted residuals (documented for the 8.3 sign-off):
  - Bare 9-digit SSNs (no dashes) -- indistinguishable from ordinary ids.
  - Bare 10-digit phone numbers (no separators) -- collide with bigint ids.
  - IPv4/IPv6 addresses -- OFF by default (``include_ip``); collide with version
    strings and other dotted/colon-separated tokens.
  - Free-form names and postal addresses -- no reliable pattern.
  - Card-shaped digit runs that fail the Luhn checksum -- treated as non-cards
    (e.g. invoice numbers, account numbers).

All redactors are idempotent: re-running redaction over already-redacted text is
a no-op because the ``[REDACTED:...]`` placeholders do not match any pattern.
"""

import re

__all__ = ["redact", "redact_text"]

# Placeholder template. ``type`` in {jwt, token, card, email, ssn, phone, secret, ip}.
REDACTED = "[REDACTED:{type}]"

PLACEHOLDER_JWT = REDACTED.format(type="jwt")
PLACEHOLDER_TOKEN = REDACTED.format(type="token")
PLACEHOLDER_CARD = REDACTED.format(type="card")
PLACEHOLDER_EMAIL = REDACTED.format(type="email")
PLACEHOLDER_SSN = REDACTED.format(type="ssn")
PLACEHOLDER_PHONE = REDACTED.format(type="phone")
PLACEHOLDER_SECRET = REDACTED.format(type="secret")
PLACEHOLDER_IP = REDACTED.format(type="ip")

# Dict keys whose values are always secrets, matched segment-aware (see
# ``_key_is_secret``) so that e.g. ``token_count`` does NOT match but
# ``access_token`` does. Stored separator-free because ``_key_is_secret``
# compares against segments joined without separators, so a compound key matches
# the same with or without a prefix (``api_key`` and ``svc_api_key`` both reduce
# to the ``apikey`` suffix).
SECRET_KEYS = frozenset(
    {
        "password",
        "passwd",
        "pwd",
        "token",
        "accesstoken",
        "refreshtoken",
        "secret",
        "clientsecret",
        "apikey",
        "privatekey",
        "signingkey",
        "encryptionkey",
        "authorization",
        "credential",
        "credentials",
    }
)

# Value patterns, applied by ``redact_text`` in the order defined below.
_JWT_RE = re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b")
_BEARER_RE = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+")
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
# Candidate card: 13-19 digits with optional single space/hyphen separators.
# Luhn-gated in ``_luhn_repl`` -- non-passing runs are returned unchanged.
_CARD_RE = re.compile(r"(?<!\d)\d(?:[ -]?\d){12,18}(?!\d)")
_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
# Phone: formatted only. International (leading +) or US grouped with a
# mandatory separator/paren so bare digit runs do not match. The first
# separator after the country code is required (``[\s.-]``) so a ``+``-prefixed
# integer literal (e.g. ``+1234567``) is not mistaken for a phone number.
_PHONE_INTL_RE = re.compile(r"\+\d{1,3}[\s.-]\(?\d{1,4}\)?[\s.-]?\d{2,4}[\s.-]?\d{2,4}")
_PHONE_US_RE = re.compile(r"\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}")
# IPv4 / IPv6. OFF by default; only applied when ``include_ip`` is set.
_IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
# Matches the whole IPv6 literal, including ``::``-compressed forms, so the
# entire address is replaced (a group-anchored pattern would redact only a
# suffix and leak the compressed prefix). The lookahead requires either a ``::``
# run or a full 8-group address, so ordinary colon-separated tokens (times, MAC
# addresses) are left untouched, preserving the module's precision stance.
_IPV6_RE = re.compile(
    r"(?<![A-Fa-f0-9:])"
    r"(?=[A-Fa-f0-9:]*::|(?:[A-Fa-f0-9]{1,4}:){7}[A-Fa-f0-9]{1,4})"
    r"[A-Fa-f0-9:]+"
    r"(?![A-Fa-f0-9:])"
)

# Splits a dict key into alphanumeric segments for segment-aware secret matching.
_KEY_SEGMENT_RE = re.compile(r"[^a-z0-9]+")


def _luhn_ok(digits: str) -> bool:
    """Return True if the digit string passes the Luhn checksum."""
    total = 0
    parity = len(digits) % 2
    for index, char in enumerate(digits):
        value = ord(char) - ord("0")
        if index % 2 == parity:
            value *= 2
            if value > 9:
                value -= 9
        total += value
    return total % 10 == 0


def _luhn_repl(match: "re.Match") -> str:
    """Replace a card candidate with the placeholder only if Luhn passes.

    Strips separators before running the checksum; non-passing runs (e.g.
    invoice numbers) are returned exactly as matched.
    """
    matched = match.group(0)
    digits = matched.replace(" ", "").replace("-", "")
    return PLACEHOLDER_CARD if _luhn_ok(digits) else matched


def _key_is_secret(key) -> bool:
    """Return True if ``key`` names a secret, matched segment-suffix-aware.

    The key is lowercased and split on non-alphanumeric boundaries. A match
    requires a *trailing* run of segments (joined separator-free) to equal one of
    ``SECRET_KEYS`` -- the secret word must be the noun the key names, not a
    leading qualifier. This is the central word-aware guard:

      - ``access_token``, ``db_password``, ``client_secret``, ``svc_private_key``
        -> suffix is a secret word -> redact.
      - ``token_count`` (suffix ``count``), ``tokenizer`` (single segment, not
        equal to ``token``), ``tokenize_flag`` (suffix ``flag``) -> keep.

    Because segments are joined without separators, a compound secret key matches
    whether or not it carries a prefix (``api_key`` and ``svc_api_key`` both
    reduce to the ``apikey`` suffix); the whole-key case is just ``start == 0``.

    ``secret`` is additionally matched as *any* whole segment (not just the
    suffix), so leading/embedded forms like ``secret_key``, ``secret_value``,
    ``secret_access_key`` and ``aws_secret_access_key`` redact. This is safe
    because ``secret`` standing alone as a segment is unambiguous. ``key`` is
    deliberately NOT treated this way -- it collides with benign analytic keys
    (``partition_key``, ``sort_key``, ``primary_key``, ``idempotency_key``), so
    key-typed secrets are enumerated explicitly in ``SECRET_KEYS`` instead.
    """
    if not isinstance(key, str):
        return False
    segments = [seg for seg in _KEY_SEGMENT_RE.split(key.lower()) if seg]
    if not segments:
        return False
    if "secret" in segments:
        return True
    # Suffix match: a trailing run of segments (including the whole key at
    # start == 0, and the last segment alone) names a secret.
    return any(
        "".join(segments[start:]) in SECRET_KEYS for start in range(len(segments))
    )


def redact_text(s: str, include_ip: bool = False, max_len: int = None) -> str:
    """Apply all value-pattern redactors to a free-text string (e.g. SQL).

    Does NOT apply key-name secret detection (no key in scope). Patterns are
    applied JWT -> Bearer -> email -> SSN -> card (Luhn-gated) -> phone ->
    optional IP. Idempotent: ``[REDACTED:...]`` placeholders never re-match.

    SSN runs before card on purpose: the card candidate pattern allows single
    space/hyphen separators, so a dashed SSN sitting immediately next to a card
    (e.g. ``"123-45-6789 4111 1111 1111 1111"``) would otherwise be swallowed
    into one over-long digit run that fails the Luhn gate, leaving the real
    card un-redacted. Substituting the SSN first replaces it with a placeholder
    so the card stands alone and redacts correctly.

    ``max_len`` (when set) caps the result *after* redaction, so size-bounding a
    sink's payload never truncates a value mid-pattern and leaks the tail.
    """
    if not isinstance(s, str):
        return s
    s = _JWT_RE.sub(PLACEHOLDER_JWT, s)
    s = _BEARER_RE.sub("Bearer " + PLACEHOLDER_TOKEN, s)
    s = _EMAIL_RE.sub(PLACEHOLDER_EMAIL, s)
    s = _SSN_RE.sub(PLACEHOLDER_SSN, s)
    s = _CARD_RE.sub(_luhn_repl, s)
    s = _PHONE_INTL_RE.sub(PLACEHOLDER_PHONE, s)
    s = _PHONE_US_RE.sub(PLACEHOLDER_PHONE, s)
    if include_ip:
        s = _IPV4_RE.sub(PLACEHOLDER_IP, s)
        s = _IPV6_RE.sub(PLACEHOLDER_IP, s)
    if max_len is not None and len(s) > max_len:
        s = s[:max_len] + "..."
    return s


def redact(value, _key=None, max_len: int = None):
    """Recursively redact a structured value (str | dict | list | scalar).

    - str  -> ``redact_text``; if ``_key`` names a secret -> ``[REDACTED:secret]``.
    - dict -> redact each value, passing the key so secret detection applies.
    - list/tuple -> redact each item. NOTE: a tuple is normalized to a list.
    - other scalars (int/float/bool/None) -> unchanged. ``bytes`` are also
      returned unchanged (no decoding) -- audit payloads originate from JSON and
      are str-typed, so this is not a redaction path in practice.

    When ``_key`` names a secret, the entire value becomes ``[REDACTED:secret]``
    regardless of its shape; otherwise recursion proceeds and value-patterns
    still apply. ``max_len`` (when set) caps each redacted string leaf, so one
    traversal both redacts and size-bounds the payload.
    """
    if _key is not None and _key_is_secret(_key):
        return PLACEHOLDER_SECRET
    if isinstance(value, str):
        return redact_text(value, max_len=max_len)
    if isinstance(value, dict):
        return {k: redact(v, _key=k, max_len=max_len) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(item, max_len=max_len) for item in value]
    return value
