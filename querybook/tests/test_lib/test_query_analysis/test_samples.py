import json
from unittest import mock
import pytest

from lib.query_analysis.samples import make_samples_query, SamplesError


@pytest.fixture
def fake_table():
    _fake_table = mock.MagicMock()
    _fake_table.name = "session_data"
    _fake_table.data_schema.name = "data"
    _fake_table.data_schema.catalog = None  # No catalog by default
    _fake_table.data_schema.metastore_id = 1

    fake_column_dt = mock.MagicMock()
    fake_column_dt.name = "dt"
    fake_column_dt.type = "string"

    fake_column_id = mock.MagicMock()
    fake_column_id.name = "id"
    fake_column_id.type = "bigint"

    _fake_table.columns = [fake_column_dt, fake_column_id]
    _fake_table.information.to_dict.return_value = {
        "latest_partitions": json.dumps(["dt=2019-11-08", "dt=2019-11-09"])
    }
    return _fake_table


@pytest.fixture
def fake_table_with_catalog():
    """Fixture for table with catalog support"""
    _fake_table = mock.MagicMock()
    _fake_table.name = "session_data"
    _fake_table.data_schema.name = "data"
    _fake_table.data_schema.catalog.name = "production"
    _fake_table.data_schema.metastore_id = 1

    fake_column_dt = mock.MagicMock()
    fake_column_dt.name = "dt"
    fake_column_dt.type = "string"

    fake_column_id = mock.MagicMock()
    fake_column_id.name = "id"
    fake_column_id.type = "bigint"

    _fake_table.columns = [fake_column_dt, fake_column_id]
    _fake_table.information.to_dict.return_value = {
        "latest_partitions": json.dumps(["dt=2019-11-08", "dt=2019-11-09"])
    }
    return _fake_table


@mock.patch("lib.query_analysis.samples.format_table_name_for_display")
@mock.patch("lib.query_analysis.samples.get_table_by_id")
def test_basic(get_table_by_id_mock, format_table_name_mock, db_engine, fake_table):
    get_table_by_id_mock.return_value = fake_table
    format_table_name_mock.return_value = "data.session_data"

    assert """
SELECT
    *
FROM data.session_data
WHERE
dt='2019-11-09'

LIMIT 1""" == make_samples_query(
        table_id=1234, limit=1
    )

    # Verify format_table_name_for_display was called correctly
    format_table_name_mock.assert_called_with(
        table_name="session_data",
        schema_name="data",
        catalog_name=None,
        metastore_id=1
    )

    format_table_name_mock.reset_mock()
    assert """
SELECT
    *
FROM data.session_data
WHERE
dt='2019-11-08'

LIMIT 2""" == make_samples_query(
        table_id=1234, limit=2, partition="dt=2019-11-08"
    )

    format_table_name_mock.reset_mock()
    assert """
SELECT
    *
FROM data.session_data
WHERE
dt='2019-11-09'
ORDER BY id ASC
LIMIT 3""" == make_samples_query(
        table_id=1234, limit=3, order_by="id"
    )


@mock.patch("lib.query_analysis.samples.format_table_name_for_display")
@mock.patch("lib.query_analysis.samples.get_table_by_id")
def test_where_filter(get_table_by_id_mock, format_table_name_mock, db_engine, fake_table):
    get_table_by_id_mock.return_value = fake_table
    format_table_name_mock.return_value = "data.session_data"
    assert """
SELECT
    *
FROM data.session_data
WHERE
dt='2019-11-09' AND id = 5

LIMIT 4""" == make_samples_query(
        table_id=1234, limit=4, where=[["id", "=", "5"]]
    )

    assert """
SELECT
    *
FROM data.session_data
WHERE
dt='2019-11-09' AND id = 5 AND id IS NOT NULL

LIMIT 4""" == make_samples_query(
        table_id=1234, limit=4, where=[["id", "=", "5"], ["id", "IS NOT NULL", ""]]
    )


@mock.patch("lib.query_analysis.samples.format_table_name_for_display")
@mock.patch("lib.query_analysis.samples.get_table_by_id")
def test_exception(get_table_by_id_mock, format_table_name_mock, db_engine, fake_table):
    get_table_by_id_mock.return_value = fake_table
    format_table_name_mock.return_value = "data.session_data"

    # Invalid order by column
    with pytest.raises(SamplesError):
        make_samples_query(table_id=1234, limit=1001, order_by="employee_id")

    # Invalid partition
    with pytest.raises(SamplesError):
        make_samples_query(table_id=1234, limit=1001, partition="dt=1000-01-01")

    # Invalid filter column
    with pytest.raises(SamplesError):
        make_samples_query(table_id=1234, limit=1001, where=[["employee_id", "=", "5"]])
    # Invalid filter op
    with pytest.raises(SamplesError):
        make_samples_query(table_id=1234, limit=1001, where=[["id", "==", "5"]])
    # Invalid filter value
    with pytest.raises(AttributeError):
        make_samples_query(table_id=1234, limit=1001, where=[["id", "=", 5]])


@mock.patch("lib.query_analysis.samples.format_table_name_for_display")
@mock.patch("lib.query_analysis.samples.get_table_by_id")
def test_catalog_support_3_part_name(get_table_by_id_mock, format_table_name_mock, db_engine, fake_table_with_catalog):
    """Test that 3-part table names work when catalog is present and show_catalog_in_ui=true"""
    get_table_by_id_mock.return_value = fake_table_with_catalog
    format_table_name_mock.return_value = "production.data.session_data"

    query = make_samples_query(table_id=1234, limit=1)

    # Verify format_table_name_for_display was called with catalog
    format_table_name_mock.assert_called_with(
        table_name="session_data",
        schema_name="data",
        catalog_name="production",
        metastore_id=1
    )

    # Verify the query uses the 3-part name
    assert "FROM production.data.session_data" in query


@mock.patch("lib.query_analysis.samples.format_table_name_for_display")
@mock.patch("lib.query_analysis.samples.get_table_by_id")
def test_catalog_support_2_part_name_when_hidden(get_table_by_id_mock, format_table_name_mock, db_engine, fake_table_with_catalog):
    """Test that 2-part table names work when catalog exists but show_catalog_in_ui=false"""
    get_table_by_id_mock.return_value = fake_table_with_catalog
    # Simulate format_table_name_for_display returning 2-part name when show_catalog_in_ui=false
    format_table_name_mock.return_value = "data.session_data"

    query = make_samples_query(table_id=1234, limit=1)

    # Verify format_table_name_for_display was called with catalog (even though it returns 2-part)
    format_table_name_mock.assert_called_with(
        table_name="session_data",
        schema_name="data",
        catalog_name="production",
        metastore_id=1
    )

    # Verify the query uses the 2-part name (as returned by the formatter)
    assert "FROM data.session_data" in query
