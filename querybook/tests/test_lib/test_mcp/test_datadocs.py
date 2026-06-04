from unittest import TestCase, mock

from lib.mcp.lib.datadocs import (
    validate_query_cell_engine,
    validate_query_cells_engines,
)


class ValidateQueryCellEngineTestCase(TestCase):
    def test_non_query_cell_skips_engine_validation(self):
        with mock.patch(
            "lib.mcp.lib.datadocs.admin_logic.get_query_engine_by_id"
        ) as mock_get_engine:
            validate_query_cell_engine(
                "text", {}, uid=1, session=mock.MagicMock(), environment_id=1
            )

        mock_get_engine.assert_not_called()

    def test_query_cell_requires_engine(self):
        with self.assertRaisesRegex(
            ValueError, "Query cell at index 2 has no engine selected."
        ):
            validate_query_cell_engine(
                "query",
                {},
                uid=1,
                session=mock.MagicMock(),
                environment_id=1,
                index=2,
            )

    def test_query_cell_rejects_invalid_engine_type(self):
        with self.assertRaisesRegex(
            ValueError, "Query cell has invalid query engine id '1'."
        ):
            validate_query_cell_engine(
                "query",
                {"engine": "1"},
                uid=1,
                session=mock.MagicMock(),
                environment_id=1,
            )

    def test_query_cell_rejects_missing_engine(self):
        with mock.patch(
            "lib.mcp.lib.datadocs.admin_logic.get_query_engine_by_id",
            return_value=None,
        ):
            with self.assertRaisesRegex(
                ValueError, "Query cell uses query engine 7, which does not exist."
            ):
                validate_query_cell_engine(
                    "query",
                    {"engine": 7},
                    uid=1,
                    session=mock.MagicMock(),
                    environment_id=1,
                )

    def test_query_cell_rejects_inaccessible_engine(self):
        with mock.patch(
            "lib.mcp.lib.datadocs.admin_logic.get_query_engine_by_id",
            return_value=mock.MagicMock(),
        ):
            with self.assertRaisesRegex(
                ValueError,
                "Query cell uses query engine 7, but you do not have access to it.",
            ):
                validate_query_cell_engine(
                    "query",
                    {"engine": 7},
                    uid=1,
                    session=mock.MagicMock(),
                    environment_id=1,
                    accessible_engine_ids={3},
                )

    def test_query_cell_rejects_engine_from_other_environment(self):
        with mock.patch(
            "lib.mcp.lib.datadocs.admin_logic.get_query_engine_by_id",
            return_value=mock.MagicMock(),
        ):
            with self.assertRaisesRegex(
                ValueError,
                "Query cell uses query engine 7, which is not available in this "
                "DataDoc's environment.",
            ):
                validate_query_cell_engine(
                    "query",
                    {"engine": 7},
                    uid=1,
                    session=mock.MagicMock(),
                    environment_id=1,
                    accessible_engine_ids={7},
                    environment_engine_ids={3},
                )

    def test_query_cell_accepts_accessible_engine_in_environment(self):
        with mock.patch(
            "lib.mcp.lib.datadocs.admin_logic.get_query_engine_by_id",
            return_value=mock.MagicMock(),
        ):
            validate_query_cell_engine(
                "query",
                {"engine": 7},
                uid=1,
                session=mock.MagicMock(),
                environment_id=1,
                accessible_engine_ids={7},
                environment_engine_ids={7},
            )

    def test_batch_validation_fetches_lookups_once(self):
        with mock.patch(
            "lib.mcp.lib.datadocs.admin_logic.get_query_engine_by_id",
            return_value=mock.MagicMock(),
        ), mock.patch(
            "lib.mcp.lib.datadocs.admin_logic.get_all_accessible_query_engine_ids_by_uid",
            return_value=[7, 8],
        ) as mock_get_accessible, mock.patch(
            "lib.mcp.lib.datadocs.admin_logic.get_query_engines_by_environment",
            return_value=[mock.MagicMock(id=7), mock.MagicMock(id=8)],
        ) as mock_get_env_engines:
            validate_query_cells_engines(
                [
                    {"cell_type": "text", "meta": {}},
                    {"cell_type": "query", "meta": {"engine": 7}},
                    {"cell_type": "query", "meta": {"engine": 8}},
                ],
                uid=1,
                environment_id=1,
                session=mock.MagicMock(),
            )

        mock_get_accessible.assert_called_once()
        mock_get_env_engines.assert_called_once()
