from typing import List
from lib.logger import get_logger

from lib.query_analysis.validation.base_query_validator import (
    BaseQueryValidator,
    QueryValidationResult,
)
from lib.query_analysis.validation.validators.presto_optimizing_validator import (
    ApproxDistinctValidator,
    RegexpLikeValidator,
    UnionAllValidator,
)

LOG = get_logger(__file__)


# No-op decorator
class NoopQueryValidator(BaseQueryValidator):
    def languages(self):
        return ["trino"]

    def validate(
        self, query: str, uid: int, engine_id: int, **kwargs
    ) -> List[QueryValidationResult]:
        return []


class TrinoSqlglotValidator(BaseQueryValidator):
    ###
    # Modified version of PrestoOptimizingValidator that
    # doesn't use the PrestoExplainValidator as a base -- this has
    # been replaced with the NoopQueryValidator
    #
    # This Validator does all linting via SQLGlot
    ###

    def languages(self):
        return ["trino"]

    def _get_decorated_validator(self) -> BaseQueryValidator:
        return UnionAllValidator(
            ApproxDistinctValidator(RegexpLikeValidator(NoopQueryValidator("noop")))
        )

    def validate(
        self, query: str, uid: int, engine_id: int, **kwargs
    ) -> List[QueryValidationResult]:
        validator = self._get_decorated_validator()
        return validator.validate(query, uid, engine_id)
