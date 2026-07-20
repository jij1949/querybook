import os
import tempfile
from unittest import mock

import pytest
from sqlalchemy import create_engine, event


@pytest.fixture(scope="session")
def monkeysession():
    from _pytest.monkeypatch import MonkeyPatch

    mp = MonkeyPatch()
    yield mp
    mp.undo()


def pytest_configure(config):
    """We can use _called_from_test to disable some checks
    during the test
    """
    import sys

    sys._called_from_test = True


def pytest_unconfigure(config):
    import sys

    del sys._called_from_test


@pytest.fixture(scope="session")
def db_engine(monkeysession):
    from env import QuerybookSettings

    tempfile_path = os.path.join(tempfile.gettempdir(), "test.db")
    database_conn = "sqlite:///" + tempfile_path
    engine = create_engine(
        database_conn, pool_pre_ping=True, encoding="utf-8", echo=True
    )

    # Register a SQLite `concat` UDF so column_property expressions that use
    # func.concat() (e.g. DataDoc.scheduled) can evaluate on the SQLite test DB.
    # Scope: joins non-None args as strings and drops NULL args rather than
    # propagating NULL; sufficient for the current tests, may differ from
    # production DB engines for NULL-valued concat arguments.
    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_conn, connection_record):
        dbapi_conn.create_function(
            "concat",
            -1,
            lambda *args: "".join(str(a) for a in args if a is not None),
        )

    import models

    models.Base.metadata.create_all(engine)

    def mock_get_db_engine(**kwargs):
        return engine

    from app import db

    monkeysession.setattr(db, "get_db_engine", mock_get_db_engine)
    monkeysession.setattr(
        QuerybookSettings, "DATABASE_CONN", database_conn, raising=True
    )

    yield engine

    os.remove(tempfile_path)


@pytest.fixture(scope="session")
def flask_client(db_engine):
    from app.flask_app import flask_app

    flask_app.config["TESTING"] = True
    with flask_app.test_client() as client:
        yield client


@pytest.fixture
def fake_user(monkeypatch):
    import flask_login

    user = mock.MagicMock()
    user.__repr__ = lambda self: "Mr Mocked"
    user.id = 1
    monkeypatch.setattr(flask_login.utils, "_get_user", user)

    return user
