import json

from lib.query_executor.executors.trino import TrinoQueryExecutor
from executor_plugin.eg_trino.eg_trino_client import EGTrinoClient
from logic import (
    admin as admin_logic,
    query_execution as qe_logic,
)
from logic.metastore import get_table_information_by_table_id, get_table_by_name

from app.db import DBSession


def get_trino_error_dict(e):
    if hasattr(e, "args") and e.args[0] is not None:
        error_arg = e.args[0]
        if type(error_arg) is dict:
            return error_arg
    return None


class EGTrinoQueryExecutor(TrinoQueryExecutor):
    def __init__(
        self,
        query_execution_id: int,
        celery_task,
        query: str,
        statement_ranges,
        client_setting,
        execution_type,
    ):
        super().__init__(
            query_execution_id,
            celery_task,
            query,
            statement_ranges,
            client_setting,
            execution_type,
        )
        self._warning = ""
        self._json_csv_warning_checked = False
        self._client_setting = client_setting | \
                               {'execution_type': 'execution_type:' + execution_type,
                                'query_execution_id': query_execution_id}

        self._get_datadoc_info(query_execution_id)

    @classmethod
    def _get_client(cls, client_setting):
        return EGTrinoClient(**client_setting)

    @classmethod
    def EXECUTOR_NAME(cls):
        return "egtrino"

    @property
    def meta_info(self):
        info = ""
        if self._cursor.tracking_url:
            info += f"Trino Tracking Url: {self._cursor.tracking_url}\n"
        if self.warning != "":
            info += (
                '<Message type="warning" title="Warning">'
                + self.warning
                + "</Message>\n"
            )
            info += "---\nforce_show: true\n---"
        return info

    @property
    def warning(self):
        if self._warning == "" and not self._json_csv_warning_checked:
            self._warning = self._get_warning_message()
        return self._warning

    def _run_next_statement(self):
        if self._current_query_index < len(self._statement_ranges):
            self._logger.on_statement_start(self._current_query_index)

            statement_range = self._statement_ranges[self._current_query_index]
            statement_start, statement_end = statement_range

            statement = self._query[statement_start:statement_end]
            self._execute(statement)
            self._current_query_index += 1
            self._json_csv_warning_checked = False
            self._warning = ""
        else:
            self._on_query_completion()

    def _get_warning_message(self):
        warning = self._get_json_csv_warning()
        return warning

    def _get_json_csv_warning(self):
        info = self._cursor._execution_info
        if info == "" or not self.is_json(info):
            return ""
        json_info = json.loads(info)
        metastore_id = self._get_metastore_id()

        warning = ""
        table_ids = []
        if not json_info["referencedTables"]:
            return ""
        for referenced_table in json_info["referencedTables"]:
            table = get_table_by_name(
                referenced_table["schema"], referenced_table["table"], metastore_id
            )
            if not table:
                continue
            table_id = table.id
            if table_id not in table_ids:
                table_ids.append(table_id)
                meta_info = get_table_information_by_table_id(
                    table_id
                ).hive_metastore_description
                meta_info_json = json.loads(meta_info)
                if (
                    meta_info_json["sd"]["serdeInfo"]["serializationLib"]
                    and "CSV" in meta_info_json["sd"]["serdeInfo"]["serializationLib"]
                ):
                    warning = (
                        warning
                        + "Table `"
                        + referenced_table["schema"]
                        + "."
                        + referenced_table["table"]
                        + "` is using the unoptimized CSV file format.\n"
                    )
                if (
                    meta_info_json["sd"]["serdeInfo"]["serializationLib"]
                    and "json" in meta_info_json["sd"]["serdeInfo"]["serializationLib"]
                ):
                    warning = (
                        warning
                        + "Table `"
                        + referenced_table["schema"]
                        + "."
                        + referenced_table["table"]
                        + "` is using the unoptimized JSON file format.\n"
                    )
        if warning != "":
            warning = (
                warning
                + "Use of non-optimized format can significantly slow down the query. \nMore information at: "
                f"https://confluence.expedia.biz/pages/viewpage.action?spaceKey=DSPKB&title=Parquet+vs+Json+format"
            )
        self._json_csv_warning_checked = True
        return warning

    def _get_metastore_id(self):
        try:
            query_id = self._logger._query_execution_id
            query_execution = qe_logic.get_query_execution_by_id(query_id)
            engine_id = query_execution.engine_id
            query_engine = admin_logic.get_query_engine_by_id(engine_id, session=None)
            metastore_id = query_engine.metastore_id
            return metastore_id
        except:
            return -1

    def _get_datadoc_info(self, query_execution_id):
        with DBSession() as session:
            datadoc_info = qe_logic.get_datadoc_id_and_title_from_query_execution_id(query_execution_id,
                                                                                     session=session)
        if datadoc_info:
            self._datadoc_id, _, self._datadoc_title = datadoc_info
            self._client_setting = self._client_setting | \
                                   {'datadoc_id': 'datadoc_id:' + str(self._datadoc_id),
                                    'datadoc_title': 'datadoc_title:' + self._datadoc_title}
        else:
            return

    def is_json(self, info):
        try:
            dummy = json.loads(info)
        except ValueError as e:
            return False
        return True
