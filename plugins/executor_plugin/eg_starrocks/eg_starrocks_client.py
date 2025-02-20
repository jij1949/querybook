from lib.logger import get_logger
from lib.query_executor.base_client import CursorBaseClass
from lib.query_executor.clients.sqlalchemy import SqlAlchemyClient, SqlAlchemyCursor
from lib.query_executor.connection_string.sqlalchemy import create_sqlalchemy_engine

LOG = get_logger(__file__)


class EgStarRocksClient(SqlAlchemyClient):
    def __init__(
        self,
        connection_string=None,
        connect_args=[],
        proxy_user=None,
        impersonate=False,
        *args,
        **kwargs,
    ):
        self.proxy_user = proxy_user
        self.impersonate = impersonate
        self._engine = create_sqlalchemy_engine(
            {
                "connection_string": connection_string,
                "connect_args": connect_args,
            }
        )
        super(SqlAlchemyClient, self).__init__()

    def __del__(self):
        self._engine.dispose()

    def cursor(self) -> CursorBaseClass:
        return EgStarRocksCursor(
            engine=self._engine,
            impersonate=self.impersonate,
            proxy_user=self.proxy_user,
        )


class EgStarRocksCursor(SqlAlchemyCursor):
    def __init__(self, engine, impersonate=False, proxy_user=None):
        self._connection = engine.connect()

        # Impersonate the proxy user if needed
        if impersonate and proxy_user:
            try:
                self._connection.execute(f"EXECUTE AS {proxy_user} WITH NO REVERT;")
            except Exception as e:
                LOG.error(f"Failed to impersonate {proxy_user}: {e}")
                raise
