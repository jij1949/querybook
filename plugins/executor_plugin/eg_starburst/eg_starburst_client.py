import requests
from typing import Any, Dict

from executor_plugin.eg_trino.eg_trino_client import EGTrinoClient, EGTrinoCursor
from lib.logger import get_logger
from trino.exceptions import TrinoUserError

LOG = get_logger(__file__)


class EGStarburstClient(EGTrinoClient):
    def __init__(
        self,
        connection_string,
        username=None,
        password=None,
        proxy_user=None,
        execution_type=None,
        query_execution_id=None,
        datadoc_id=None,
        datadoc_title=None,
        *args,
        **kwargs,
    ):
        self._username = username
        self._password = password
        super(EGStarburstClient, self).__init__(
            connection_string, username, password, proxy_user, execution_type, query_execution_id, datadoc_id,
            datadoc_title, args, kwargs
        )

    def cursor(self):
        return EGStarburstCursor(
            cursor=self._connection.cursor(),
            username=self._username,
            password=self._password,
        )


class EGStarburstCursor(EGTrinoCursor):
    _starburst_tracking_url = None

    def _init_query_state_vars(self) -> None:
        self.rows = []
        self._tracking_url = None
        self._starburst_tracking_url = None
        self._percent_complete = 0

    def poll(self):
        try:
            self.rows.extend(self._cursor._query.fetch())
            self._cursor._iterator = iter(self.rows)
            poll_result = self._cursor.stats
            completed = self._cursor._query._finished
            if poll_result:
                self._update_percent_complete(poll_result)
                self._update_execution_info(poll_result)
                self._update_tracking_url(poll_result)
                self._update_starburst_tracking_url(poll_result)

        except TrinoUserError as e:
            # Catch the error and update the tracking url
            poll_result = {"queryId": e.query_id}
            self._update_tracking_url(poll_result)
            self._update_starburst_tracking_url(poll_result)

            raise e

        return completed

    @property
    def starburst_tracking_url(self):
        return self._starburst_tracking_url

    def _update_starburst_tracking_url(self, poll_result: Dict[str, Any]):
        if self._starburst_tracking_url is None:
            self._starburst_tracking_url = f"{self._request._http_scheme}://{self._request._host}:{self._request._port}/ui/insights/query/{poll_result['queryId']}"
