from lib.query_executor.executors.sqlalchemy import SqlAlchemyQueryExecutor
from executor_plugin.eg_starrocks.eg_starrocks_client import EgStarRocksClient


class EgStarRocksQueryExecutor(SqlAlchemyQueryExecutor):

    @classmethod
    def EXECUTOR_NAME(cls):
        return "eg_starrocks"

    @classmethod
    def EXECUTOR_LANGUAGE(cls):
        return "starrocks"

    @classmethod
    def _get_client(cls, client_setting):
        return EgStarRocksClient(**client_setting)
