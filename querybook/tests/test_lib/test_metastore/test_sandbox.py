from unittest.mock import MagicMock

from lib.metastore.sandbox import get_user_sandbox_schema


def _make_user(email):
    u = MagicMock()
    u.email = email
    return u


# --- get_user_sandbox_schema ---


def test_get_user_sandbox_schema_simple():
    assert (
        get_user_sandbox_schema(_make_user("lvillalobos@expedia.com")) == "lvillalobos"
    )


def test_get_user_sandbox_schema_vendor_prefix():
    assert (
        get_user_sandbox_schema(_make_user("v-marjmartinez@expedia.com"))
        == "v-marjmartinez"
    )


def test_get_user_sandbox_schema_associate_prefix():
    assert get_user_sandbox_schema(_make_user("a-jsmith@expedia.com")) == "a-jsmith"


def test_get_user_sandbox_schema_null_email():
    assert get_user_sandbox_schema(_make_user(None)) == ""
