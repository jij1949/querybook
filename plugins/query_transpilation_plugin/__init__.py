from query_transpilation_plugin.eg_custom.eg_custom_transpiler import (
    EGCustomTrinoTranspiler,
    EGHiveTrinoTranspiler,
)

ALL_PLUGIN_QUERY_TRANSPILERS = [EGCustomTrinoTranspiler(), EGHiveTrinoTranspiler()]
