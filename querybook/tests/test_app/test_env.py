from unittest import TestCase

from env import _parse_uri_list, _resolve_allowed_redirect_uris

DEFAULTS = ["http://localhost:*", "http://127.0.0.1:*"]


class ParseUriListTestCase(TestCase):
    def test_none(self):
        self.assertEqual(_parse_uri_list(None), [])

    def test_empty_string(self):
        self.assertEqual(_parse_uri_list(""), [])

    def test_comma_separated_with_whitespace(self):
        self.assertEqual(
            _parse_uri_list("http://a/* , http://b/*"),
            ["http://a/*", "http://b/*"],
        )

    def test_skips_blank_entries(self):
        self.assertEqual(_parse_uri_list("http://a/*,,"), ["http://a/*"])

    def test_already_a_list(self):
        # get_env_config returns a parsed list for JSON-array config values
        self.assertEqual(
            _parse_uri_list(["http://a/*", "http://b/*"]),
            ["http://a/*", "http://b/*"],
        )


class ResolveAllowedRedirectUrisTestCase(TestCase):
    def test_defaults_when_unset(self):
        self.assertEqual(_resolve_allowed_redirect_uris(None, None, DEFAULTS), DEFAULTS)

    def test_extra_appended_to_defaults(self):
        self.assertEqual(
            _resolve_allowed_redirect_uris(None, "https://app/*", DEFAULTS),
            [*DEFAULTS, "https://app/*"],
        )

    def test_base_overrides_defaults(self):
        self.assertEqual(
            _resolve_allowed_redirect_uris("https://only/*", None, DEFAULTS),
            ["https://only/*"],
        )

    def test_extra_appended_to_explicit_base(self):
        self.assertEqual(
            _resolve_allowed_redirect_uris(
                "https://base/*", "https://extra/*", DEFAULTS
            ),
            ["https://base/*", "https://extra/*"],
        )

    def test_dedupes_preserving_order(self):
        self.assertEqual(
            _resolve_allowed_redirect_uris(
                None, "http://localhost:*,https://app/*", DEFAULTS
            ),
            [*DEFAULTS, "https://app/*"],
        )
