from typing import Tuple

from app.db import with_session
from logic.admin import get_query_engine_by_id
from lib.query_executor.all_executors import get_executor_class
from lib.query_executor.clients.trino import TrinoClient
from lib.query_executor.connection_string.trino import get_trino_connection_conf
from lib.query_executor.executor_factory import get_client_setting_from_engine

from lib.table_upload.exporter.utils import (
    update_pandas_df_column_name_type,
)
from .base_exporter import BaseTableUploadExporter

from sqlalchemy import create_engine
from trino.auth import BasicAuthentication


default_pandas_to_sql_config = {
    "schema": None,
    "if_exists": "fail",
    "index": False,
    "chunksize": 10000,
}


class TrinoExporter(BaseTableUploadExporter):
    @with_session
    def _get_trino_connection(self, session=None):
        engine = get_query_engine_by_id(self._engine_id, session=session)
        executor = get_executor_class(engine.language, engine.executor)
        executor_params = engine.get_engine_params()
        client = executor._get_client(executor_params)

        if not isinstance(client, TrinoClient):
            raise ValueError(f"Client instance {client} is not Trino Based")

        client_settings = get_client_setting_from_engine(engine, None, session=session)
        trino_conf = get_trino_connection_conf(client_settings["connection_string"])

        host = trino_conf.host
        port = 8080 if not trino_conf.port else trino_conf.port
        catalog = trino_conf.catalog
        username = client_settings["username"]
        pwd = client_settings["password"]

        trino_engine = create_engine(
            f"trino://{username}:{pwd}@{host}:{port}/{catalog}",
            connect_args={
                "auth": BasicAuthentication(username, pwd),
                "http_scheme": "https",
            },
        )

        return trino_engine

    def _get_pandas_to_sql_config(self):
        connection = self._get_trino_connection()

        config = {
            "name": self._table_config["table_name"],
            "schema": self._table_config.get("schema_name", None),
            "con": connection,
            "if_exists": self._table_config.get("if_exists", "fail"),
            "index": False,
            "chunksize": 10000,
        }

        return config

    def _upload(self) -> Tuple[str, str]:
        df = update_pandas_df_column_name_type(
            self._importer.get_pandas_df(), self._table_config["column_name_types"]
        )

        config = self._get_pandas_to_sql_config()

        df.to_sql(**config)
