from executor_plugin.eg_starburst.eg_starburst_client import EGStarburstClient
from executor_plugin.eg_trino.eg_trino_executor import EGTrinoQueryExecutor


class EGStarburstQueryExecutor(EGTrinoQueryExecutor):
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

    @classmethod
    def _get_client(cls, client_setting):
        return EGStarburstClient(**client_setting)

    @classmethod
    def EXECUTOR_NAME(cls):
        return "egstarburst"

    @property
    def meta_info(self):
        info = ""
        if self._cursor.starburst_tracking_url:
            info += f"Starburst Tracking Url: {self._cursor.starburst_tracking_url}\n"
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
