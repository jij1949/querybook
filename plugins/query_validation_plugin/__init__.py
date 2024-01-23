from lib.query_analysis.validation.validators.presto_optimizing_validator import (
    PrestoOptimizingValidator,
)
from query_validation_plugin.trino_sqlglot_validator.trino_sqlglot_validator import (
    TrinoSqlglotValidator,
)


ALL_PLUGIN_QUERY_VALIDATORS_BY_NAME = {
    "PrestoOptimizingValidator": PrestoOptimizingValidator("PrestoOptimizingValidator"),
    "TrinoSqlglotValidator": TrinoSqlglotValidator("TrinoSqlglotValidator"),
}
