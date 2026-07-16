import sys
import os
import json

from const.path import DEFAULT_PLUGIN_PATH
from lib.config import get_config_value


in_test = hasattr(sys, "_called_from_test")
querybook_config = get_config_value("querybook_config", {})
querybook_default_config = get_config_value("querybook_default_config", {})


class MissingConfigException(Exception):
    pass


def is_json(value):
    """
    Check if a given value is a valid JSON serialized dict or list
    """
    try:
        parsed = json.loads(value)
        return isinstance(parsed, (dict, list))
    except ValueError:
        return False


def get_env_config(name, optional=True):
    found = True
    val = None

    if name in os.environ:
        val = os.environ.get(name)
    elif name in querybook_config:
        val = querybook_config.get(name)
    elif name in querybook_default_config:
        val = querybook_default_config.get(name)
        found = val is not None
    else:
        found = False
    # We treat empty string as None as well
    if not found and not optional and not in_test:
        raise MissingConfigException(
            "{} is required to start the process.".format(name)
        )
    # Check for string-serialized JSON dicts/lists
    if isinstance(val, str) and is_json(val):
        val = json.loads(val)
    return val


def _parse_uri_list(raw):
    """Normalize a config value into a list of URIs.

    Accepts a JSON array, comma-separated string, or YAML list. Returns an
    empty list when the value is unset.
    """
    if isinstance(raw, str):
        return [u.strip() for u in raw.split(",") if u.strip()]
    return raw or []


def _resolve_allowed_redirect_uris(base_raw, extra_raw, defaults):
    """Resolve the allowed redirect URIs from config.

    ``base_raw`` (if set) overrides ``defaults`` entirely; ``extra_raw`` is
    always appended on top. The result is deduped with order preserved.
    """
    base = _parse_uri_list(base_raw) or defaults
    extra = _parse_uri_list(extra_raw)
    return list(dict.fromkeys([*base, *extra]))


class QuerybookSettings(object):
    # Core
    PRODUCTION = os.environ.get("production", "false") == "true"
    ENVIRONMENT = (
        get_env_config("ENVIRONMENT")
        or get_env_config("DD_ENV")
        or ("production" if PRODUCTION else "development")
    )
    PUBLIC_URL = get_env_config("PUBLIC_URL")
    FLASK_SECRET_KEY = get_env_config("FLASK_SECRET_KEY", optional=False)
    FLASK_CACHE_CONFIG = get_env_config("FLASK_CACHE_CONFIG")
    WS_CORS_ALLOWED_ORIGINS = get_env_config("WS_CORS_ALLOWED_ORIGINS", optional=False)
    IFRAME_ALLOWED_ORIGINS = get_env_config("IFRAME_ALLOWED_ORIGINS")
    QUERYBOOK_PLUGIN_PATH = get_env_config("QUERYBOOK_PLUGIN") or DEFAULT_PLUGIN_PATH

    # Celery
    REDIS_URL = get_env_config("REDIS_URL", optional=False)
    CELERY_MAX_TASKS_PER_CHILD = int(
        get_env_config("CELERY_MAX_TASKS_PER_CHILD", optional=True) or 1
    )

    # Search
    ELASTICSEARCH_HOST = get_env_config("ELASTICSEARCH_HOST", optional=False)
    ELASTICSEARCH_CONNECTION_TYPE = get_env_config("ELASTICSEARCH_CONNECTION_TYPE")

    # Lineage
    DATA_LINEAGE_BACKEND = get_env_config("DATA_LINEAGE_BACKEND")

    # Database
    DATABASE_CONN = get_env_config("DATABASE_CONN", optional=False)
    DATABASE_POOL_SIZE = int(get_env_config("DATABASE_POOL_SIZE"))
    DATABASE_POOL_RECYCLE = int(get_env_config("DATABASE_POOL_RECYCLE"))
    DATABASE_ECHO = str(get_env_config("DATABASE_ECHO")).lower() == "true"

    # Communications
    EMAILER_CONN = get_env_config("EMAILER_CONN")
    QUERYBOOK_SLACK_TOKEN = get_env_config("QUERYBOOK_SLACK_TOKEN")
    QUERYBOOK_EMAIL_ADDRESS = get_env_config("QUERYBOOK_EMAIL_ADDRESS")

    # Authentication
    AUTH_BACKEND = get_env_config("AUTH_BACKEND")
    LOGS_OUT_AFTER = int(get_env_config("LOGS_OUT_AFTER"))

    OAUTH_CLIENT_ID = get_env_config("OAUTH_CLIENT_ID")
    OAUTH_CLIENT_SECRET = get_env_config("OAUTH_CLIENT_SECRET")
    OAUTH_AUTHORIZATION_URL = get_env_config("OAUTH_AUTHORIZATION_URL")
    OAUTH_TOKEN_URL = get_env_config("OAUTH_TOKEN_URL")
    OAUTH_USER_PROFILE = get_env_config("OAUTH_USER_PROFILE")
    AZURE_TENANT_ID = get_env_config("AZURE_TENANT_ID")

    LDAP_CONN = get_env_config("LDAP_CONN")
    LDAP_USE_TLS = str(get_env_config("LDAP_USE_TLS")).lower() == "true"
    LDAP_USE_BIND_USER = str(get_env_config("LDAP_USE_BIND_USER")).lower() == "true"

    # Get global groups and check for empty string
    LDAP_GLOBAL_GROUPS = (
        get_env_config("LDAP_GLOBAL_GROUPS").split(",")
        if get_env_config("LDAP_GLOBAL_GROUPS")
        else []
    )

    # For direct authentication
    LDAP_USER_DN = get_env_config("LDAP_USER_DN")
    # For searches using bind user
    LDAP_BIND_USER = get_env_config("LDAP_BIND_USER")
    LDAP_BIND_PASSWORD = get_env_config("LDAP_BIND_PASSWORD")
    LDAP_SEARCH = get_env_config("LDAP_SEARCH")
    LDAP_FILTER = get_env_config("LDAP_FILTER")
    LDAP_UID_FIELD = get_env_config("LDAP_UID_FIELD")
    LDAP_EMAIL_FIELD = get_env_config("LDAP_EMAIL_FIELD")
    LDAP_LASTNAME_FIELD = get_env_config("LDAP_LASTNAME_FIELD")
    LDAP_FIRSTNAME_FIELD = get_env_config("LDAP_FIRSTNAME_FIELD")
    LDAP_FULLNAME_FIELD = get_env_config("LDAP_FULLNAME_FIELD")
    # Configuration validation
    if LDAP_CONN is not None:
        if LDAP_USE_BIND_USER:
            if (
                LDAP_BIND_USER is None
                or LDAP_BIND_PASSWORD is None
                or LDAP_SEARCH is None
            ):
                raise ValueError(
                    "LDAP_BIND_USER, LDAP_BIND_PASSWORD and LDAP_SEARCH has to be set when using LDAP bind user connection"
                )
        elif LDAP_USER_DN is None:
            raise ValueError(
                "LDAP_USER_DN has to be set when using direct LDAP connection"
            )

    LDAP_QUERYBOOK_ADMINS_GROUP = get_env_config(
        "LDAP_QUERYBOOK_ADMINS_GROUP", optional=True
    )

    # Result Store
    RESULT_STORE_TYPE = get_env_config("RESULT_STORE_TYPE")

    STORE_BUCKET_NAME = get_env_config("STORE_BUCKET_NAME")
    STORE_PATH_PREFIX = get_env_config("STORE_PATH_PREFIX")
    STORE_MIN_UPLOAD_CHUNK_SIZE = int(get_env_config("STORE_MIN_UPLOAD_CHUNK_SIZE"))
    STORE_MAX_UPLOAD_CHUNK_NUM = int(get_env_config("STORE_MAX_UPLOAD_CHUNK_NUM"))
    STORE_MAX_READ_SIZE = int(get_env_config("STORE_MAX_READ_SIZE"))
    STORE_READ_SIZE = int(get_env_config("STORE_READ_SIZE"))
    S3_BUCKET_S3V4_ENABLED = get_env_config("S3_BUCKET_S3V4_ENABLED") == "true"
    AWS_REGION = get_env_config("AWS_REGION")

    DB_MAX_UPLOAD_SIZE = int(get_env_config("DB_MAX_UPLOAD_SIZE"))

    GOOGLE_CREDS = get_env_config("GOOGLE_CREDS")

    # Logging
    LOG_LOCATION = get_env_config("LOG_LOCATION")

    # Table Upload (Experimental)
    TABLE_MAX_UPLOAD_SIZE = get_env_config("TABLE_MAX_UPLOAD_SIZE")
    TABLE_MAX_UPLOAD_ROWS = get_env_config("TABLE_MAX_UPLOAD_ROWS")

    # Event Logging
    EVENT_LOGGER_NAME = get_env_config("EVENT_LOGGER_NAME") or "null"

    # Stats Logging
    STATS_LOGGER_NAME = get_env_config("STATS_LOGGER_NAME") or "null"

    # AI Assistant
    AI_ASSISTANT_PROVIDER = get_env_config("AI_ASSISTANT_PROVIDER")
    AI_ASSISTANT_CONFIG = get_env_config("AI_ASSISTANT_CONFIG") or {}

    # LangSmith tracing
    LANGSMITH_TRACING = str(get_env_config("LANGSMITH_TRACING")).lower() == "true"
    LANGSMITH_API_KEY = get_env_config("LANGSMITH_API_KEY")
    LANGSMITH_PROJECT = get_env_config("LANGSMITH_PROJECT")

    VECTOR_STORE_PROVIDER = get_env_config("VECTOR_STORE_PROVIDER")
    VECTOR_STORE_CONFIG = get_env_config("VECTOR_STORE_CONFIG") or {}
    EMBEDDINGS_PROVIDER = get_env_config("EMBEDDINGS_PROVIDER")
    EMBEDDINGS_CONFIG = get_env_config("EMBEDDINGS_CONFIG") or {}

    # Ranger
    RANGER_URL = get_env_config("RANGER_URL")

    # EG Specific
    QUERY_EXECUTION_SEARCH_MIN_ID = int(
        get_env_config("QUERY_EXECUTION_SEARCH_MIN_ID", optional=True) or 0
    )

    # Datadog
    DD_AGENT_HOST = get_env_config("DD_AGENT_HOST", optional=True)
    DD_DOGSTATSD_PORT = int(get_env_config("DD_DOGSTATSD_PORT", optional=True) or 8125)
    DD_PREFIX = get_env_config("DD_PREFIX", optional=True)
    DD_SERVICE = get_env_config("DD_SERVICE", optional=True) or "querybook"
    DD_TAGS = get_env_config("DD_TAGS", optional=True) or []

    # Expedia Custom Endpoints
    ANALYTICS_WORKBENCH_GRAPHQL_ENDPOINT = get_env_config(
        "ANALYTICS_WORKBENCH_GRAPHQL_ENDPOINT"
    )

    # GitHub Integration
    GITHUB_CLIENT_ID = get_env_config("GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET = get_env_config("GITHUB_CLIENT_SECRET")
    GITHUB_REPO_NAME = get_env_config("GITHUB_REPO_NAME")
    GITHUB_BRANCH = get_env_config("GITHUB_BRANCH")
    GITHUB_CRYPTO_SECRET = get_env_config("GITHUB_CRYPTO_SECRET")

    # MCP Server
    MCP_PORT = int(get_env_config("MCP_PORT") or 8771)
    MCP_AUTH_MODE = get_env_config("MCP_AUTH_MODE") or "token"
    MCP_AUTH_SECRET = get_env_config("MCP_AUTH_SECRET")
    MCP_OAUTH_BASE_URL = get_env_config("MCP_OAUTH_BASE_URL")
    MCP_OIDC_CONFIG_URL = get_env_config("MCP_OIDC_CONFIG_URL")
    # Out-of-the-box redirect URIs. Override the full list with
    # MCP_OAUTH_ALLOWED_REDIRECT_URIS, or append deployment-specific entries with
    # MCP_OAUTH_EXTRA_ALLOWED_REDIRECT_URIS (keeps the Vault config small).
    DEFAULT_MCP_OAUTH_REDIRECT_URIS = [
        "http://localhost:*",
        "http://127.0.0.1:*",
        "cursor://anysphere.cursor-mcp/*",
        "https://analytics.expedia.biz/oauth/callback",
        "https://analytics-test.expedia.biz/oauth/callback",
    ]
    # Both vars accept a JSON array, comma-separated string, or YAML list.
    # e.g. '["http://localhost:*"]' or 'http://localhost:*,http://127.0.0.1:*'
    MCP_OAUTH_ALLOWED_REDIRECT_URIS = _resolve_allowed_redirect_uris(
        get_env_config("MCP_OAUTH_ALLOWED_REDIRECT_URIS"),
        get_env_config("MCP_OAUTH_EXTRA_ALLOWED_REDIRECT_URIS"),
        DEFAULT_MCP_OAUTH_REDIRECT_URIS,
    )
    # Per-credential rate limit. 0/unset MAX_REQUESTS disables the limiter.
    MCP_RATE_LIMIT_MAX_REQUESTS = int(
        get_env_config("MCP_RATE_LIMIT_MAX_REQUESTS") or 0
    )
    MCP_RATE_LIMIT_WINDOW_SECONDS = int(
        get_env_config("MCP_RATE_LIMIT_WINDOW_SECONDS") or 60
    )
    if MCP_RATE_LIMIT_MAX_REQUESTS < 0:
        raise ValueError("MCP_RATE_LIMIT_MAX_REQUESTS must not be negative")
    if MCP_RATE_LIMIT_WINDOW_SECONDS <= 0:
        raise ValueError("MCP_RATE_LIMIT_WINDOW_SECONDS must be positive")
    # Free-text tool-arg cap (bytes). 0 disables the guard.
    MCP_MAX_FREETEXT_INPUT_BYTES = int(
        get_env_config("MCP_MAX_FREETEXT_INPUT_BYTES") or 1048576  # 1 MiB
    )
    if MCP_MAX_FREETEXT_INPUT_BYTES < 0:
        raise ValueError("MCP_MAX_FREETEXT_INPUT_BYTES must not be negative")
    # Per-credential failure-burst anomaly detection. 0/unset THRESHOLD
    # disables it. Detection-only: it emits an `anomaly` signal, never blocks.
    MCP_ANOMALY_FAILURE_THRESHOLD = int(
        get_env_config("MCP_ANOMALY_FAILURE_THRESHOLD") or 0
    )
    MCP_ANOMALY_WINDOW_SECONDS = int(
        get_env_config("MCP_ANOMALY_WINDOW_SECONDS") or 300
    )
    if MCP_ANOMALY_FAILURE_THRESHOLD < 0:
        raise ValueError("MCP_ANOMALY_FAILURE_THRESHOLD must not be negative")
    if MCP_ANOMALY_WINDOW_SECONDS <= 0:
        raise ValueError("MCP_ANOMALY_WINDOW_SECONDS must be positive")

    # Cache Control
    CACHE_CONTROL_MAX_AGE = int(
        get_env_config("CACHE_CONTROL_MAX_AGE") or "604800"
    )  # 7 days
    CACHE_CONTROL_STALE_WHILE_REVALIDATE = int(
        get_env_config("CACHE_CONTROL_STALE_WHILE_REVALIDATE") or "86400"
    )  # 1 day
