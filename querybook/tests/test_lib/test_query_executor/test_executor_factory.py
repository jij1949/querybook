from unittest import TestCase
from unittest.mock import Mock, patch
from lib.query_executor.executor_factory import _assert_safe_query
from lib.query_executor.exc import InvalidQueryExecution


class ExecutorFactoryACLTestCase(TestCase):
    """Test ACL validation in executor_factory with 2-level and 3-level table names"""

    @patch("lib.query_executor.executor_factory.process_query")
    @patch("lib.query_executor.executor_factory.admin_logic")
    def test_assert_safe_query_with_2level_table_names(
        self, mock_admin_logic, mock_process_query
    ):
        """Test ACL validation works with 2-level table names (schema.table)"""
        # Mock query parser to return 2-level table names
        mock_process_query.return_value = (
            [["sales.orders", "sales.customers"]],  # table_per_statement
            [],  # lineage
        )

        # Mock query engine and metastore
        mock_query_engine = Mock()
        mock_query_engine.metastore_id = 1

        mock_metastore = Mock()
        mock_metastore.acl_control = {
            "type": "allowlist",
            "tables": ["sales.*"],
        }

        mock_admin_logic.get_query_engine_by_id.return_value = mock_query_engine
        mock_admin_logic.get_query_metastore_by_id.return_value = mock_metastore

        # Should not raise an exception
        try:
            _assert_safe_query("SELECT * FROM sales.orders", engine_id=1)
        except InvalidQueryExecution:
            self.fail("2-level table names should be allowed")

    @patch("lib.query_executor.executor_factory.process_query")
    @patch("lib.query_executor.executor_factory.admin_logic")
    def test_assert_safe_query_with_3level_table_names(
        self, mock_admin_logic, mock_process_query
    ):
        """Test ACL validation works with 3-level table names (catalog.schema.table)"""
        # Mock query parser to return 3-level table names
        mock_process_query.return_value = (
            [["production.sales.orders", "production.sales.customers"]],
            [],
        )

        # Mock query engine and metastore
        mock_query_engine = Mock()
        mock_query_engine.metastore_id = 1

        mock_metastore = Mock()
        mock_metastore.acl_control = {
            "type": "allowlist",
            "tables": ["production.sales.*"],
        }

        mock_admin_logic.get_query_engine_by_id.return_value = mock_query_engine
        mock_admin_logic.get_query_metastore_by_id.return_value = mock_metastore

        # Should not raise an exception
        try:
            _assert_safe_query(
                "SELECT * FROM production.sales.orders", engine_id=1
            )
        except InvalidQueryExecution:
            self.fail("3-level table names should be allowed")

    @patch("lib.query_executor.executor_factory.process_query")
    @patch("lib.query_executor.executor_factory.admin_logic")
    def test_assert_safe_query_blocks_unauthorized_2level_table(
        self, mock_admin_logic, mock_process_query
    ):
        """Test ACL blocks unauthorized tables with 2-level naming"""
        # Mock query parser
        mock_process_query.return_value = (
            [["hr.employees"]],  # Unauthorized table
            [],
        )

        # Mock query engine and metastore
        mock_query_engine = Mock()
        mock_query_engine.metastore_id = 1

        mock_metastore = Mock()
        mock_metastore.acl_control = {
            "type": "allowlist",
            "tables": ["sales.*"],  # Only sales schema allowed
        }

        mock_admin_logic.get_query_engine_by_id.return_value = mock_query_engine
        mock_admin_logic.get_query_metastore_by_id.return_value = mock_metastore

        # Should raise InvalidQueryExecution
        with self.assertRaises(InvalidQueryExecution) as context:
            _assert_safe_query("SELECT * FROM hr.employees", engine_id=1)

        self.assertIn("not allowed", str(context.exception))

    @patch("lib.query_executor.executor_factory.process_query")
    @patch("lib.query_executor.executor_factory.admin_logic")
    def test_assert_safe_query_blocks_unauthorized_3level_table(
        self, mock_admin_logic, mock_process_query
    ):
        """Test ACL blocks unauthorized tables with 3-level naming"""
        # Mock query parser
        mock_process_query.return_value = (
            [["staging.test.data"]],  # Unauthorized catalog
            [],
        )

        # Mock query engine and metastore
        mock_query_engine = Mock()
        mock_query_engine.metastore_id = 1

        mock_metastore = Mock()
        mock_metastore.acl_control = {
            "type": "allowlist",
            "tables": ["production.*"],  # Only production catalog allowed
        }

        mock_admin_logic.get_query_engine_by_id.return_value = mock_query_engine
        mock_admin_logic.get_query_metastore_by_id.return_value = mock_metastore

        # Should raise InvalidQueryExecution
        with self.assertRaises(InvalidQueryExecution) as context:
            _assert_safe_query("SELECT * FROM staging.test.data", engine_id=1)

        self.assertIn("not allowed", str(context.exception))

    @patch("lib.query_executor.executor_factory.process_query")
    @patch("lib.query_executor.executor_factory.admin_logic")
    def test_assert_safe_query_with_mixed_2level_and_3level_tables(
        self, mock_admin_logic, mock_process_query
    ):
        """Test ACL validation handles mixed 2-level and 3-level table names"""
        # Mock query parser to return both formats
        mock_process_query.return_value = (
            [
                [
                    "default.users",  # 2-level
                    "production.sales.orders",  # 3-level
                ]
            ],
            [],
        )

        # Mock query engine and metastore
        mock_query_engine = Mock()
        mock_query_engine.metastore_id = 1

        mock_metastore = Mock()
        mock_metastore.acl_control = {
            "type": "allowlist",
            "tables": [
                "default.*",  # 2-level wildcard
                "production.sales.*",  # 3-level wildcard
            ],
        }

        mock_admin_logic.get_query_engine_by_id.return_value = mock_query_engine
        mock_admin_logic.get_query_metastore_by_id.return_value = mock_metastore

        # Should not raise an exception
        try:
            _assert_safe_query(
                "SELECT * FROM default.users JOIN production.sales.orders",
                engine_id=1,
            )
        except InvalidQueryExecution:
            self.fail("Mixed 2-level and 3-level table names should be allowed")

    @patch("lib.query_executor.executor_factory.process_query")
    @patch("lib.query_executor.executor_factory.admin_logic")
    def test_assert_safe_query_with_catalog_wildcard(
        self, mock_admin_logic, mock_process_query
    ):
        """Test ACL validation with catalog-level wildcards"""
        # Mock query parser
        mock_process_query.return_value = (
            [
                [
                    "production.sales.orders",
                    "production.hr.employees",
                ]
            ],
            [],
        )

        # Mock query engine and metastore
        mock_query_engine = Mock()
        mock_query_engine.metastore_id = 1

        mock_metastore = Mock()
        mock_metastore.acl_control = {
            "type": "allowlist",
            "tables": ["production.*"],  # Catalog wildcard
        }

        mock_admin_logic.get_query_engine_by_id.return_value = mock_query_engine
        mock_admin_logic.get_query_metastore_by_id.return_value = mock_metastore

        # Should not raise an exception
        try:
            _assert_safe_query(
                "SELECT * FROM production.sales.orders JOIN production.hr.employees",
                engine_id=1,
            )
        except InvalidQueryExecution:
            self.fail("Catalog wildcard should allow all tables in catalog")

    @patch("lib.query_executor.executor_factory.process_query")
    @patch("lib.query_executor.executor_factory.admin_logic")
    def test_assert_safe_query_with_denylist(
        self, mock_admin_logic, mock_process_query
    ):
        """Test ACL validation with denylist mode"""
        # Mock query parser
        mock_process_query.return_value = (
            [["production.pii.users"]],  # Blocked table
            [],
        )

        # Mock query engine and metastore
        mock_query_engine = Mock()
        mock_query_engine.metastore_id = 1

        mock_metastore = Mock()
        mock_metastore.acl_control = {
            "type": "denylist",
            "tables": ["production.pii.*"],  # Block PII schema
        }

        mock_admin_logic.get_query_engine_by_id.return_value = mock_query_engine
        mock_admin_logic.get_query_metastore_by_id.return_value = mock_metastore

        # Should raise InvalidQueryExecution
        with self.assertRaises(InvalidQueryExecution) as context:
            _assert_safe_query("SELECT * FROM production.pii.users", engine_id=1)

        self.assertIn("not allowed", str(context.exception))

    @patch("lib.query_executor.executor_factory.process_query")
    @patch("lib.query_executor.executor_factory.admin_logic")
    def test_assert_safe_query_with_invalid_table_format(
        self, mock_admin_logic, mock_process_query
    ):
        """Test ACL validation rejects invalid table name formats"""
        # Mock query parser to return invalid format (single part)
        mock_process_query.return_value = (
            [["orders"]],  # Invalid: no schema
            [],
        )

        # Mock query engine and metastore
        mock_query_engine = Mock()
        mock_query_engine.metastore_id = 1

        mock_metastore = Mock()
        mock_metastore.acl_control = {
            "type": "allowlist",
            "tables": ["*"],
        }

        mock_admin_logic.get_query_engine_by_id.return_value = mock_query_engine
        mock_admin_logic.get_query_metastore_by_id.return_value = mock_metastore

        # Should raise InvalidQueryExecution for invalid format
        with self.assertRaises(InvalidQueryExecution) as context:
            _assert_safe_query("SELECT * FROM orders", engine_id=1)

        self.assertIn("Invalid table name format", str(context.exception))

    @patch("lib.query_executor.executor_factory.process_query")
    @patch("lib.query_executor.executor_factory.admin_logic")
    def test_assert_safe_query_skips_when_no_metastore(
        self, mock_admin_logic, mock_process_query
    ):
        """Test ACL validation is skipped when query engine has no metastore"""
        # Mock query parser
        mock_process_query.return_value = (
            [["sales.orders"]],
            [],
        )

        # Mock query engine without metastore
        mock_query_engine = Mock()
        mock_query_engine.metastore_id = None

        mock_admin_logic.get_query_engine_by_id.return_value = mock_query_engine

        # Should not raise an exception (ACL check skipped)
        try:
            _assert_safe_query("SELECT * FROM sales.orders", engine_id=1)
        except InvalidQueryExecution:
            self.fail("Should skip ACL validation when no metastore")

    @patch("lib.query_executor.executor_factory.process_query")
    @patch("lib.query_executor.executor_factory.admin_logic")
    def test_assert_safe_query_backward_compatibility(
        self, mock_admin_logic, mock_process_query
    ):
        """Test that 2-level ACL rules match 3-level qualified names (backward compat)"""
        # Mock query parser to return 3-level table names
        mock_process_query.return_value = (
            [["production.sales.orders"]],  # 3-level name
            [],
        )

        # Mock query engine and metastore
        mock_query_engine = Mock()
        mock_query_engine.metastore_id = 1

        mock_metastore = Mock()
        mock_metastore.acl_control = {
            "type": "allowlist",
            "tables": ["sales.*"],  # 2-level rule
        }

        mock_admin_logic.get_query_engine_by_id.return_value = mock_query_engine
        mock_admin_logic.get_query_metastore_by_id.return_value = mock_metastore

        # Should not raise an exception (backward compatibility)
        try:
            _assert_safe_query(
                "SELECT * FROM production.sales.orders", engine_id=1
            )
        except InvalidQueryExecution:
            self.fail(
                "2-level ACL rules should match 3-level names via backward compat"
            )
