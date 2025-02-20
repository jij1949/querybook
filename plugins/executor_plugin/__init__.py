from executor_plugin.eg_trino.eg_trino_executor import EGTrinoQueryExecutor
from executor_plugin.eg_starburst.eg_starburst_executor import EGStarburstQueryExecutor
from executor_plugin.eg_starrocks.eg_starrocks_executor import EgStarRocksQueryExecutor


ALL_PLUGIN_EXECUTORS = [
    EGTrinoQueryExecutor,
    EGStarburstQueryExecutor,
    EgStarRocksQueryExecutor,
]
