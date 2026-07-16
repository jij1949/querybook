from env import QuerybookSettings
from lib.stats_logger.all_stats_loggers import get_stats_logger_class


# metrics name
API_REQUESTS = "api.requests"
WS_CONNECTIONS = "ws.connections"
SQL_SESSION_FAILURES = "sql_session.failures"
TASK_FAILURES = "task.failures"
TASK_SUCCESSES = "task.successes"
TASK_RECEIVED = "task.received"
REDIS_OPERATIONS = "redis.operations"
QUERY_EXECUTIONS = "query.executions"
ACTIVE_WORKERS = "celery.active_workers"
ACTIVE_TASKS = "celery.active_tasks"

# MCP audit metrics (emitted from lib/mcp/audit/router.py::_emit_metric)
MCP_TOOL_CALL = "mcp.tool.call"
MCP_TOOL_ERROR = "mcp.tool.error"
MCP_AUTH_FAILURE = "mcp.auth.failure"
MCP_AUTHZ_DENY = "mcp.authz.deny"
MCP_REJECTED = "mcp.rejected"
MCP_RATE_LIMIT = "mcp.rate_limit"
# Per-credential security anomaly (e.g. a burst of auth/authz/rejected
# failures from one credential). Tagged by `reason` so a single metric can
# carry multiple anomaly types, mirroring `mcp.rejected`.
MCP_ANOMALY = "mcp.anomaly"
# Incremented directly by rate_limit.py on Redis backend faults — the one
# exception to the single-emitter rule, since a backend fault produces no
# audit envelope to key a metric off of.
MCP_RATE_LIMIT_BACKEND_ERROR = "mcp.rate_limit.backend_error"


logger_name = QuerybookSettings.STATS_LOGGER_NAME
stats_logger = get_stats_logger_class(logger_name)
