from executor_plugin.eg_trino.eg_trino_executor import EGTrinoQueryExecutor
from executor_plugin.eg_starburst.eg_starburst_executor import EGStarburstQueryExecutor


ALL_PLUGIN_EXECUTORS = [
    EGTrinoQueryExecutor,
    EGStarburstQueryExecutor
]
