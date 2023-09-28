import requests
import trino
from trino.exceptions import TrinoUserError

from os import environ
from lib.query_executor.clients.trino import TrinoClient, TrinoCursor
from lib.query_executor.connection_string.trino import get_trino_connection_conf
from logic.user import get_user_by_name


class EGTrinoClient(TrinoClient):
    def __init__(
        self,
        connection_string,
        username=None,
        password=None,
        proxy_user=None,
        execution_type=None,
        query_execution_id=None,
        *args,
        **kwargs,
    ):
        self._username = username
        self._password = password

        trino_conf = get_trino_connection_conf(connection_string)

        host = trino_conf.host
        port = 8080 if not trino_conf.port else trino_conf.port

        auth = trino.auth.BasicAuthentication(username, password)

        connection = trino.dbapi.connect(
            host=host,
            port=port,
            catalog=trino_conf.catalog,
            schema=trino_conf.schema,
            auth=auth,
            user=proxy_user if proxy_user else username,
            http_scheme=trino_conf.protocol,
            client_tags=[execution_type] if execution_type else None,
            http_headers={
                "X-Trino-Trace-Token": f"querybookExecutionId:{query_execution_id}"
            }
            if query_execution_id
            else None,
            source="querybook",
        )
        self._connection = connection
        super(TrinoClient, self).__init__()

    def cursor(self):
        return EGTrinoCursor(
            cursor=self._connection.cursor(),
            username=self._username,
            password=self._password,
        )


class EGTrinoCursor(TrinoCursor):
    def __init__(self, cursor, username, password):
        self._cursor = cursor
        self.rows = []
        self._init_query_state_vars()
        self._request = cursor._request
        self._execution_info = ""
        self._user = username
        self._password = password

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

        except TrinoUserError as e:
            # Catch the error and update the tracking url
            poll_result = {"queryId": e.query_id}
            self._update_tracking_url(poll_result)

            raise e

        return completed

    @property
    def execution_info(self):
        return self._execution_info

    def _update_execution_info(self, poll_result):
        execution_info = self.get_execution_info(poll_result)
        self._execution_info = execution_info

    def get_execution_info(self, poll_result):
        if not self.tracking_url:
            return ""
        info_url = f"{self._request._http_scheme}://{self._request._host}:{self._request._port}/ui/api/query/{poll_result['queryId']}"
        login_url = f"{self._request._http_scheme}://{self._request._host}:{self._request._port}/ui/login"
        payload = {"username": self._user, "password": self._password}
        with requests.session() as s:
            r = s.post(login_url, data=payload)
            if r.status_code != 200:
                return ""
            r = s.get(info_url)
            return r.text
