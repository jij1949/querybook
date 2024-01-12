from engine_status_checker_plugin.trino_connection_checker import TrinoConnectionChecker
from engine_status_checker_plugin.trino_connection_checker2 import (
    TrinoConnectionChecker2,
)


ALL_PLUGIN_ENGINE_STATUS_CHECKERS = [TrinoConnectionChecker, TrinoConnectionChecker2]
