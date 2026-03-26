from lib.query_executor.executors.trino import TrinoQueryExecutor
from executor_plugin.eg_trino.eg_trino_client import EGTrinoClient
from logic import (
    query_execution as qe_logic,
)
from app.db import DBSession
import re
from trino.exceptions import Error, TrinoQueryError
from lib.query_executor.utils import get_parsed_syntax_error
from const.query_execution import QueryExecutionErrorType


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
        self._client_setting = client_setting | \
            {'execution_type': 'execution_type:' + execution_type,
             'query_execution_id': query_execution_id,
             'retries': 'retries:' + str(celery_task.request.retries)}

        self._get_datadoc_info(query_execution_id)

        extra_client_tags = []
        if self._execution_metadata.get("source") == "mcp":
            extra_client_tags.append("ai-tool:querybook-mcp")
        if extra_client_tags:
            self._client_setting = self._client_setting | {'extra_client_tags': extra_client_tags}

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
        return info

    def _run_next_statement(self):
        if self._current_query_index < len(self._statement_ranges):
            self._logger.on_statement_start(self._current_query_index)

            statement_range = self._statement_ranges[self._current_query_index]
            statement_start, statement_end = statement_range

            statement = self._query[statement_start:statement_end]
            self._execute(statement)
            self._current_query_index += 1
        else:
            self._on_query_completion()

    def _get_datadoc_info(self, query_execution_id):
        with DBSession() as session:
            datadoc_info = qe_logic.get_datadoc_info_from_query_execution_id(query_execution_id,
                                                                             session=session)
        if datadoc_info:
            self._datadoc_id, self._data_cell_id, self._data_cell_meta, self._datadoc_title = datadoc_info
            self._datadoc_title = self.simplify_string(self._datadoc_title)
            self._data_cell_title = self.simplify_string(
                self._data_cell_meta.get('title', ''))
            self._client_setting = self._client_setting | \
                {'datadoc_id': 'datadoc_id:' + str(self._datadoc_id),
                 'datadoc_title': 'datadoc_title:' + self._datadoc_title,
                 'data_cell_id': 'data_cell_id:' + str(self._data_cell_id),
                 'data_cell_title': 'data_cell_title:' + self._data_cell_title}
        else:
            return

    def simplify_string(self, title_input):
        # Remove non-ASCII characters and trailing/leading whitespace, newlines, and carriage returns
        title_output = re.sub(
            r'[^\x00-\x7F]', '', title_input).strip().replace('\n', '').replace('\r', '')
        return title_output

    def _parse_exception(self, e):
        error_type = QueryExecutionErrorType.INTERNAL.value
        error_str = str(e)
        error_extracted = None

        if isinstance(e, TrinoQueryError):
            try:
                line_number, column_number = e.error_location
                return get_parsed_syntax_error(
                    e.message, line_number - 1, column_number - 1, e
                )
            except Exception:
                return QueryExecutionErrorType.ENGINE.value, error_str, e.message

        if isinstance(e, Error):
            error_type = QueryExecutionErrorType.ENGINE.value
            try:
                error_dict = get_trino_error_dict(e)
                if error_dict:
                    error_extracted = error_dict.get("message", None)
            except Exception:
                pass
        return error_type, error_str, error_extracted
