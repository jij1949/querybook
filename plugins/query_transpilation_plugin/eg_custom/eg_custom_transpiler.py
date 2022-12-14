import sqlglot
from typing import List
from lib.logger import get_logger
from lib.query_analysis.transpilation.base_query_transpiler import BaseQueryTranspiler
from query_transpilation_plugin.eg_custom.date_function_util import (
    function_list,
)


LOG = get_logger(__file__)


def apply(f, value):
    return f(value)


def statements_to_query(statements: List[str]):
    return "\n".join(statement + ";" for statement in statements)


#
# Custom Presto transpiler converting various Hive functions
# This is supported by BEX Qubole Presto
#
# Does not run through SQLGlot because it doesn't support Hive functions,
# and Presto is almost identical to Trino.
#
class EGPrestoTrinoTranspiler(BaseQueryTranspiler):
    def name(self) -> str:
        return "EGPrestoTrinoTranspiler"

    def from_languages(self) -> List[str]:
        return ["presto"]

    def to_languages(self) -> List[str]:
        return ["trino"]

    def transpile(self, query: str, from_language: str, to_language: str):

        transpiledQuery = query

        # Apply custom functions first
        for f in function_list:
            transpiledQuery = apply(f, transpiledQuery)

        return {"transpiled_query": transpiledQuery, "original_query": query}


#
# Custom Hive transpiler extending SQLGlot
#
class EGHiveTrinoTranspiler(BaseQueryTranspiler):
    def name(self) -> str:
        return "EGHiveTrinoTranspiler"

    def from_languages(self) -> List[str]:
        return ["hive"]

    def to_languages(self) -> List[str]:
        return ["trino"]

    def transpile(self, query: str, from_language: str, to_language: str):
        # Run through SQLGlot first
        transpiled_statements = sqlglot.transpile(
            query,
            read="hive",
            write="trino",
            pretty=True,
        )

        transpiledQuery = statements_to_query(transpiled_statements)

        # Apply custom functions
        for f in function_list:
            transpiledQuery = apply(f, transpiledQuery)

        return {"transpiled_query": transpiledQuery, "original_query": query}
