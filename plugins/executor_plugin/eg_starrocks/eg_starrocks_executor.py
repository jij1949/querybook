from lib.query_executor.executors.sqlalchemy import SqlAlchemyQueryExecutor


class EgStarRocksQueryExecutor(SqlAlchemyQueryExecutor):

    @classmethod
    def EXECUTOR_NAME(cls):
        return "eg_starrocks"

    @classmethod
    def EXECUTOR_LANGUAGE(cls):
        return "starrocks"
