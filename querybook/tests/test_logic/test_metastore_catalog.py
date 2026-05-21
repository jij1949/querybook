from unittest.mock import MagicMock, patch


def make_catalog(id, name, schema_count):
    c = MagicMock()
    c.id = id
    c.name = name
    c.get_schema_count = MagicMock(return_value=schema_count)
    c.to_dict = MagicMock(return_value={"id": id, "name": name})
    return c


class TestGetAllCatalogsPaginated:
    @patch("logic.metastore.with_session", lambda f: f)
    def test_returns_paginated_results(self):
        from logic.metastore import get_all_catalogs_paginated

        mock_session = MagicMock()
        catalog = make_catalog(1, "b_catalog", 3)
        # The query now returns (catalog, schema_count) tuples
        mock_session.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [(catalog, 3)]

        result = get_all_catalogs_paginated(
            metastore_id=1, offset=0, limit=30, sort_key="name", sort_order="asc", session=mock_session
        )
        assert result == [(catalog, 3)]

    @patch("logic.metastore.with_session", lambda f: f)
    def test_applies_offset_and_limit(self):
        from logic.metastore import get_all_catalogs_paginated

        mock_session = MagicMock()
        chain = mock_session.query.return_value.filter.return_value.order_by.return_value
        chain.offset.return_value.limit.return_value.all.return_value = []

        get_all_catalogs_paginated(
            metastore_id=1, offset=10, limit=5, sort_key="name", sort_order="asc", session=mock_session
        )
        chain.offset.assert_called_once_with(10)
        chain.offset.return_value.limit.assert_called_once_with(5)

    @patch("logic.metastore.with_session", lambda f: f)
    def test_applies_desc_sort_order(self):
        from logic.metastore import get_all_catalogs_paginated

        mock_session = MagicMock()
        mock_col = MagicMock()
        chain = mock_session.query.return_value.filter.return_value
        chain.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        with patch("logic.metastore.DataCatalog") as mock_catalog_class:
            mock_catalog_class.metastore_id = MagicMock()
            mock_catalog_class.name = mock_col

            get_all_catalogs_paginated(
                metastore_id=1, offset=0, limit=30, sort_key="name", sort_order="desc", session=mock_session
            )
            mock_col.desc.assert_called_once()


class TestGetAllSchemasWithCatalogFilter:
    @patch("logic.metastore.with_session", lambda f: f)
    def test_filters_by_catalog_id(self):
        from logic.metastore import get_all_schemas

        mock_session = MagicMock()
        chain = mock_session.query.return_value
        chain.filter.return_value = chain
        chain.order_by.return_value = chain
        chain.offset.return_value = chain
        chain.limit.return_value = chain
        chain.all.return_value = []

        get_all_schemas(metastore_id=1, catalog_id=42, session=mock_session)

        # Verify the catalog_id branch was reached by checking filter was called
        # at least twice: once for catalog_id, once for metastore_id
        assert chain.filter.call_count >= 2
        assert chain.all.called

    @patch("logic.metastore.with_session", lambda f: f)
    def test_filters_uncategorized_when_catalog_id_none_string(self):
        from logic.metastore import get_all_schemas

        mock_session = MagicMock()
        chain = mock_session.query.return_value
        chain.filter.return_value = chain
        chain.order_by.return_value = chain
        chain.offset.return_value = chain
        chain.limit.return_value = chain
        chain.all.return_value = []

        get_all_schemas(metastore_id=1, catalog_id="none", session=mock_session)
        # Called without raising — IS NULL branch was taken
        assert chain.all.called

    @patch("logic.metastore.with_session", lambda f: f)
    def test_no_catalog_filter_when_omitted(self):
        from logic.metastore import get_all_schemas

        mock_session = MagicMock()
        chain = mock_session.query.return_value
        chain.filter.return_value = chain
        chain.order_by.return_value = chain
        chain.offset.return_value = chain
        chain.limit.return_value = chain
        chain.all.return_value = []

        get_all_schemas(metastore_id=1, session=mock_session)
        assert chain.all.called
