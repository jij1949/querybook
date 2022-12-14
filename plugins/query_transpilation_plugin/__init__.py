from query_transpilation_plugin.eg_custom.eg_custom_transpiler import (
    EGHiveTrinoTranspiler,
    EGPrestoTrinoTranspiler,
)

ALL_PLUGIN_QUERY_TRANSPILERS = [EGHiveTrinoTranspiler(), EGPrestoTrinoTranspiler()]
