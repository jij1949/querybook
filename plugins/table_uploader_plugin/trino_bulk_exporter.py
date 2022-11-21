import pandas as pd

from app.db import with_session
from logic import user as logic
from logic.admin import get_query_engine_by_id
from lib.logger import get_logger
from lib.query_executor.all_executors import get_executor_class
from lib.query_executor.clients.trino import TrinoClient
from lib.query_executor.connection_string.trino import get_trino_connection_conf
from lib.query_executor.executor_factory import get_client_setting_from_engine
from lib.table_upload.exporter.base_exporter import BaseTableUploadExporter
from lib.table_upload.exporter.utils import update_pandas_df_column_name_type
from table_uploader_plugin.trino_bulk_insert import TrinoBulkInsert
from typing import Tuple
from sqlalchemy import create_engine

LOG = get_logger(__file__)


class TrinoBulkExporter(BaseTableUploadExporter):
    @with_session
    def _get_trino_connection(self, session=None):
        user_info = logic.get_user_by_id(self._uid, session=session)
        impersonate_user = user_info.username

        engine = get_query_engine_by_id(self._engine_id, session=session)
        executor = get_executor_class(engine.language, engine.executor)
        executor_params = engine.get_engine_params()
        client = executor._get_client(executor_params)

        if not isinstance(client, TrinoClient):
            raise ValueError(f"Client instance {client} is not Trino Based")

        feature_params = engine.feature_params or {}
        maxStringLength = feature_params.get('trino_bulk_exporter_maxStringLength', None)
        batchSize = feature_params.get('trino_bulk_exporter_batchSize', None)

        client_settings = get_client_setting_from_engine(engine, None, session=session)
        trino_conf = get_trino_connection_conf(client_settings["connection_string"])

        host = trino_conf.host
        port = 8080 if not trino_conf.port else trino_conf.port
        catalog = trino_conf.catalog
        username = client_settings["username"]
        pwd = client_settings["password"]

        connection_config = {
            "host": host,
            "port": port,
            "username": username,
            "password": pwd,
            "impersonate_user": impersonate_user,
            "catalog": catalog,
            "schema": self._table_config.get("schema_name", None),
            "table": self._table_config["table_name"],
            "if_exists": self._table_config.get("if_exists", "fail"),
            "batchSize": batchSize,
            "maxStringLength": maxStringLength
        }
        return connection_config

    def _get_create_table_statement(self, df, table_name):
        return pd.io.sql.get_schema(df, table_name, con=create_engine(f"trino://"))

    @with_session
    def _upload(self, session=None) -> Tuple[str, str]:
        column_name_types = self._table_config["column_name_types"]
        df = update_pandas_df_column_name_type(
            self._importer.get_pandas_df(), column_name_types)

        connection = self._get_trino_connection()

        bulk_insert = TrinoBulkInsert()
        bulk_insert.setVerbose(True)
        bulk_insert.setBatchSize(connection['batchSize'])
        bulk_insert.setMaxStringLength(connection['maxStringLength'])
        bulk_insert.setConnection(
            host=connection["host"],
            port=connection["port"],
            username=connection["username"],
            password=connection["password"],
            impersonate_user=connection["impersonate_user"],
            catalog=connection["catalog"],
            schema=connection["schema"],
            https=True
        )
        # Set table column names and data types
        bulk_insert.setTableColumns(columns=dict(column_name_types))

        # Check if table exists via metastore call
        table_exists = self._check_if_table_exists(session=session)
        LOG.info(f'Table Exists: {table_exists}')

        # Get create table statement using pandas
        create_statement = self._get_create_table_statement(df, connection['table'])

        # Call create table with if_exists to handle different scenarios
        bulk_insert.createTable(
            tableName=f"{connection['schema']}.{connection['table']}",
            tableExists=table_exists,
            ifExists=self._table_config.get("if_exists", "fail"),
            createStatement=create_statement
        )

        # Insert rows
        LOG.info('*** Inserting Rows ***')
        for row in df.to_dict(orient='records'):
            bulk_insert.addRow(row.values())

        bulk_insert.flushConnection()
