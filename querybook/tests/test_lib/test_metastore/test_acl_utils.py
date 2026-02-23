from lib.metastore.utils import MetastoreTableACLChecker


class TestCatalogWildcardAllowlist:
    """Test catalog wildcard patterns in allowlist mode"""

    def test_allowlist_catalog_wildcard_allows_all_tables(self):
        """Test that catalog.* in allowlist allows all tables in that catalog"""
        acl_config = {"type": "allowlist", "tables": ["production.*"]}
        checker = MetastoreTableACLChecker(acl_config)

        # Should allow any table in production catalog
        assert checker.is_table_valid("production.sales", "orders")
        assert checker.is_table_valid("production.hr", "employees")
        assert checker.is_table_valid("production.analytics", "events")

        # Should block tables in other catalogs
        assert not checker.is_table_valid("staging.sales", "orders")
        assert not checker.is_table_valid("dev.test", "data")

    def test_allowlist_catalog_wildcard_allows_all_schemas(self):
        """Test that catalog.* in allowlist allows all schemas in that catalog"""
        acl_config = {"type": "allowlist", "tables": ["production.*"]}
        checker = MetastoreTableACLChecker(acl_config)

        # Should allow any schema in production catalog
        assert checker.is_schema_valid("production.sales")
        assert checker.is_schema_valid("production.hr")
        assert checker.is_schema_valid("production.analytics")

        # Should block schemas in other catalogs
        assert not checker.is_schema_valid("staging.sales")
        assert not checker.is_schema_valid("dev.test")

    def test_allowlist_multiple_catalog_wildcards(self):
        """Test multiple catalog wildcards in allowlist"""
        acl_config = {
            "type": "allowlist",
            "tables": ["production.*", "staging.*"],
        }
        checker = MetastoreTableACLChecker(acl_config)

        # Should allow tables in both catalogs
        assert checker.is_table_valid("production.sales", "orders")
        assert checker.is_table_valid("staging.test", "data")

        # Should block tables in other catalogs
        assert not checker.is_table_valid("dev.test", "data")

    def test_allowlist_catalog_wildcard_with_explicit_rules(self):
        """Test catalog wildcard combined with explicit schema rules"""
        acl_config = {
            "type": "allowlist",
            "tables": ["production.*", "staging.analytics.summary_daily"],
        }
        checker = MetastoreTableACLChecker(acl_config)

        # Production catalog wildcard allows all
        assert checker.is_table_valid("production.sales", "orders")
        assert checker.is_table_valid("production.hr", "employees")

        # Explicit rule allows specific table in staging
        assert (
            checker.is_table_valid("staging.analytics", "summary_daily")
        )

        # Other staging tables should be blocked
        assert not checker.is_table_valid("staging.analytics", "events")
        assert not checker.is_table_valid("staging.sales", "orders")

    def test_allowlist_2level_schema_not_affected_by_catalog_wildcard(self):
        """Test that 2-level schema names don't match catalog wildcards"""
        acl_config = {"type": "allowlist", "tables": ["production.*"]}
        checker = MetastoreTableACLChecker(acl_config)

        # 2-level schema should not match catalog wildcard
        assert not checker.is_table_valid("sales", "orders")
        assert not checker.is_schema_valid("sales")


class TestCatalogWildcardDenylist:
    """Test catalog wildcard patterns in denylist mode"""

    def test_denylist_catalog_wildcard_blocks_all_tables(self):
        """Test that catalog.* in denylist blocks all tables in that catalog"""
        acl_config = {"type": "denylist", "tables": ["sensitive.*"]}
        checker = MetastoreTableACLChecker(acl_config)

        # Should block any table in sensitive catalog
        assert not checker.is_table_valid("sensitive.pii", "users")
        assert not checker.is_table_valid("sensitive.financial", "accounts")

        # Should allow tables in other catalogs
        assert checker.is_table_valid("production.sales", "orders")
        assert checker.is_table_valid("staging.test", "data")

    def test_denylist_catalog_wildcard_blocks_all_schemas(self):
        """Test that catalog.* in denylist blocks all schemas in that catalog"""
        acl_config = {"type": "denylist", "tables": ["sensitive.*"]}
        checker = MetastoreTableACLChecker(acl_config)

        # Should block any schema in sensitive catalog
        assert not checker.is_schema_valid("sensitive.pii")
        assert not checker.is_schema_valid("sensitive.financial")

        # Should allow schemas in other catalogs
        assert checker.is_schema_valid("production.sales")
        assert checker.is_schema_valid("staging.test")

    def test_denylist_multiple_catalog_wildcards(self):
        """Test multiple catalog wildcards in denylist"""
        acl_config = {
            "type": "denylist",
            "tables": ["test.*", "dev.*"],
        }
        checker = MetastoreTableACLChecker(acl_config)

        # Should block tables in both catalogs
        assert not checker.is_table_valid("test.schema1", "table1")
        assert not checker.is_table_valid("dev.schema2", "table2")

        # Should allow tables in other catalogs
        assert checker.is_table_valid("production.sales", "orders")


class TestBackwardCompatibility:
    """Test that existing patterns still work correctly"""

    def test_2level_exact_match(self):
        """Test 2-level exact table match still works"""
        acl_config = {
            "type": "allowlist",
            "tables": ["analytics.events"],
        }
        checker = MetastoreTableACLChecker(acl_config)

        assert checker.is_table_valid("analytics", "events")
        assert not checker.is_table_valid("analytics", "users")

    def test_2level_schema_wildcard(self):
        """Test 2-level schema wildcard still works"""
        acl_config = {
            "type": "allowlist",
            "tables": ["public.*"],
        }
        checker = MetastoreTableACLChecker(acl_config)

        assert checker.is_table_valid("public", "users")
        assert checker.is_table_valid("public", "orders")
        assert not checker.is_table_valid("private", "data")

    def test_3level_exact_match(self):
        """Test 3-level exact table match still works"""
        acl_config = {
            "type": "allowlist",
            "tables": ["production.sales.orders"],
        }
        checker = MetastoreTableACLChecker(acl_config)

        assert checker.is_table_valid("production.sales", "orders")
        assert not checker.is_table_valid("production.sales", "customers")

    def test_3level_schema_wildcard(self):
        """Test 3-level schema wildcard (catalog.schema.*) still works"""
        acl_config = {
            "type": "allowlist",
            "tables": ["production.sales.*"],
        }
        checker = MetastoreTableACLChecker(acl_config)

        assert checker.is_table_valid("production.sales", "orders")
        assert checker.is_table_valid("production.sales", "customers")
        assert not checker.is_table_valid("production.hr", "employees")

    def test_prefix_wildcard(self):
        """Test prefix wildcard still works"""
        acl_config = {
            "type": "allowlist",
            "tables": ["public.user_*"],
        }
        checker = MetastoreTableACLChecker(acl_config)

        assert checker.is_table_valid("public", "user_profiles")
        assert checker.is_table_valid("public", "user_settings")
        assert not checker.is_table_valid("public", "orders")


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_empty_acl_allows_everything(self):
        """Test that empty ACL config allows everything"""
        acl_config = {"type": "allowlist", "tables": []}
        checker = MetastoreTableACLChecker(acl_config)

        # Empty allowlist blocks everything
        assert not checker.is_table_valid("production.sales", "orders")

        # Empty denylist allows everything
        acl_config = {"type": "denylist", "tables": []}
        checker = MetastoreTableACLChecker(acl_config)
        assert checker.is_table_valid("production.sales", "orders")

    def test_no_acl_type_allows_everything(self):
        """Test that missing ACL type allows everything"""
        acl_config = {}
        checker = MetastoreTableACLChecker(acl_config)

        assert checker.is_table_valid("production.sales", "orders")
        assert checker.is_schema_valid("production.sales")

    def test_catalog_wildcard_with_schema_wildcard(self):
        """Test overlapping catalog and schema wildcards"""
        acl_config = {
            "type": "allowlist",
            "tables": ["production.*", "production.sales.*"],
        }
        checker = MetastoreTableACLChecker(acl_config)

        # Both rules allow the table (catalog wildcard takes precedence)
        assert checker.is_table_valid("production.sales", "orders")
        assert checker.is_table_valid("production.hr", "employees")

    def test_single_part_table_name(self):
        """Test single part table name defaults to 'default' schema"""
        acl_config = {
            "type": "allowlist",
            "tables": ["users"],
        }
        checker = MetastoreTableACLChecker(acl_config)

        # Single part should be treated as default.users
        assert checker.is_table_valid("default", "users")
        assert not checker.is_table_valid("public", "users")

    def test_catalog_wildcard_case_sensitivity(self):
        """Test catalog wildcard case sensitivity"""
        acl_config = {
            "type": "allowlist",
            "tables": ["Production.*"],
        }
        checker = MetastoreTableACLChecker(acl_config)

        # Case must match exactly
        assert checker.is_table_valid("Production.sales", "orders")
        assert not checker.is_table_valid("production.sales", "orders")


class TestMixedPatterns:
    """Test combinations of different pattern types"""

    def test_mixed_2level_and_3level_allowlist(self):
        """Test mixing 2-level and 3-level patterns in allowlist"""
        acl_config = {
            "type": "allowlist",
            "tables": [
                "public.*",  # 2-level schema wildcard
                "production.sales.*",  # 3-level schema wildcard
                "staging.analytics.events",  # 3-level exact table
            ],
        }
        checker = MetastoreTableACLChecker(acl_config)

        # 2-level pattern
        assert checker.is_table_valid("public", "users")

        # 3-level schema wildcard
        assert checker.is_table_valid("production.sales", "orders")

        # 3-level exact table
        assert checker.is_table_valid("staging.analytics", "events")
        assert not checker.is_table_valid("staging.analytics", "logs")

    def test_mixed_catalog_wildcard_with_specific_overrides(self):
        """Test catalog wildcard with specific table overrides"""
        acl_config = {
            "type": "allowlist",
            "tables": [
                "production.*",  # Allow all production
                "staging.reports.summary_daily",  # Allow specific staging table
            ],
        }
        checker = MetastoreTableACLChecker(acl_config)

        # Production catalog wildcard allows all
        assert checker.is_table_valid("production.sales", "orders")
        assert checker.is_table_valid("production.hr", "employees")

        # Specific staging table allowed
        assert checker.is_table_valid("staging.reports", "summary_daily")

        # Other staging tables blocked
        assert not checker.is_table_valid("staging.reports", "summary_weekly")
        assert not checker.is_table_valid("staging.sales", "orders")

    def test_denylist_with_catalog_and_schema_patterns(self):
        """Test denylist with mixed catalog and schema patterns"""
        acl_config = {
            "type": "denylist",
            "tables": [
                "test.*",  # Block entire test catalog
                "production.sensitive.*",  # Block sensitive schema in production
            ],
        }
        checker = MetastoreTableACLChecker(acl_config)

        # Test catalog completely blocked
        assert not checker.is_table_valid("test.any", "table")

        # Sensitive schema in production blocked
        assert not checker.is_table_valid("production.sensitive", "data")

        # Other production tables allowed
        assert checker.is_table_valid("production.sales", "orders")


class TestSchemaValidation:
    """Test schema-level validation with catalog wildcards"""

    def test_schema_valid_with_catalog_wildcard(self):
        """Test is_schema_valid with catalog wildcards"""
        acl_config = {
            "type": "allowlist",
            "tables": ["production.*"],
        }
        checker = MetastoreTableACLChecker(acl_config)

        # Schemas in production should be valid
        assert checker.is_schema_valid("production.sales")
        assert checker.is_schema_valid("production.hr")

        # Schemas in other catalogs should be invalid
        assert not checker.is_schema_valid("staging.sales")

    def test_schema_valid_backward_compatibility(self):
        """Test is_schema_valid backward compatibility check"""
        acl_config = {
            "type": "allowlist",
            "tables": ["sales.*"],  # 2-level pattern
        }
        checker = MetastoreTableACLChecker(acl_config)

        # 2-level schema should work
        assert checker.is_schema_valid("sales")

        # 3-level with matching schema name should also work (backward compat)
        assert checker.is_schema_valid("production.sales")


class TestQualifiedSchemaNames:
    """Test ACL checking with qualified schema names (catalog.schema format)"""

    def test_3level_acl_pattern_with_qualified_schema_name(self):
        """Test that 3-level ACL patterns work when qualified schema name is passed"""
        acl_config = {
            "type": "allowlist",
            "tables": ["production.sales.*"]
        }
        checker = MetastoreTableACLChecker(acl_config)

        # Should work with qualified schema name (catalog.schema)
        assert checker.is_table_valid("production.sales", "orders")
        assert checker.is_table_valid("production.sales", "customers")

        # Should NOT work with just schema name
        assert not checker.is_table_valid("sales", "orders")

        # Should NOT work with different catalog
        assert not checker.is_table_valid("staging.sales", "orders")

    def test_3level_exact_table_with_qualified_schema_name(self):
        """Test exact 3-level table match with qualified schema name"""
        acl_config = {
            "type": "allowlist",
            "tables": ["production.sales.orders"]
        }
        checker = MetastoreTableACLChecker(acl_config)

        # Should work with qualified schema name
        assert checker.is_table_valid("production.sales", "orders")

        # Should NOT work with different table
        assert not checker.is_table_valid("production.sales", "customers")

        # Should NOT work with just schema name
        assert not checker.is_table_valid("sales", "orders")

    def test_2level_acl_with_qualified_schema_backward_compat(self):
        """Test that 2-level ACL rules work with qualified schema names via backward compat"""
        acl_config = {
            "type": "allowlist",
            "tables": ["sales.*"]  # 2-level rule
        }
        checker = MetastoreTableACLChecker(acl_config)

        # Should work with qualified schema via backward compat check
        assert checker.is_table_valid("production.sales", "orders")
        assert checker.is_table_valid("staging.sales", "orders")

        # Should also work with just schema name
        assert checker.is_table_valid("sales", "orders")

        # Should NOT work with different schema
        assert not checker.is_table_valid("production.hr", "employees")

    def test_catalog_wildcard_with_qualified_schema_name(self):
        """Test catalog wildcard patterns with qualified schema names"""
        acl_config = {
            "type": "allowlist",
            "tables": ["production.*"]  # Catalog wildcard
        }
        checker = MetastoreTableACLChecker(acl_config)

        # Should work for any schema in production catalog
        assert checker.is_table_valid("production.sales", "orders")
        assert checker.is_table_valid("production.hr", "employees")
        assert checker.is_table_valid("production.analytics", "events")

        # Should NOT work for other catalogs
        assert not checker.is_table_valid("staging.sales", "orders")
        assert not checker.is_table_valid("dev.test", "data")

    def test_mixed_2level_and_3level_patterns_with_qualified_names(self):
        """Test mixing 2-level and 3-level patterns with qualified schema names"""
        acl_config = {
            "type": "allowlist",
            "tables": [
                "production.sales.*",  # 3-level
                "default.*",            # 2-level (can be catalog or schema)
                "staging.analytics.events"  # 3-level exact
            ]
        }
        checker = MetastoreTableACLChecker(acl_config)

        # 3-level wildcard should work with qualified name
        assert checker.is_table_valid("production.sales", "orders")

        # 2-level pattern should work as both schema and catalog wildcard
        assert checker.is_table_valid("default", "users")
        assert checker.is_table_valid("default.public", "users")

        # 3-level exact match should work with qualified name
        assert checker.is_table_valid("staging.analytics", "events")
        assert not checker.is_table_valid("staging.analytics", "logs")

    def test_denylist_with_qualified_schema_names(self):
        """Test denylist mode with qualified schema names"""
        acl_config = {
            "type": "denylist",
            "tables": ["production.pii.*"]
        }
        checker = MetastoreTableACLChecker(acl_config)

        # Should block tables in production.pii
        assert not checker.is_table_valid("production.pii", "users")
        assert not checker.is_table_valid("production.pii", "ssn")

        # Should allow tables in other schemas
        assert checker.is_table_valid("production.sales", "orders")
        assert checker.is_table_valid("staging.pii", "users")


class TestThreeLevelPrefixPatterns:
    """Test 3-level prefix patterns (catalog.schema.prefix_*)"""

    def test_allowlist_3level_prefix_basic(self):
        """Test basic 3-level prefix pattern in allowlist"""
        acl_config = {
            "type": "allowlist",
            "tables": ["production.sales.orders_*"]
        }
        checker = MetastoreTableACLChecker(acl_config)

        # Should allow tables matching the prefix
        assert checker.is_table_valid("production.sales", "orders_daily")
        assert checker.is_table_valid("production.sales", "orders_monthly")
        assert checker.is_table_valid("production.sales", "orders_summary")

        # Should block tables not matching the prefix
        assert not checker.is_table_valid("production.sales", "orders")
        assert not checker.is_table_valid("production.sales", "customers")
        assert not checker.is_table_valid("production.sales", "invoice_daily")

    def test_allowlist_3level_prefix_different_catalog(self):
        """Test that 3-level prefix is catalog-specific"""
        acl_config = {
            "type": "allowlist",
            "tables": ["production.sales.orders_*"]
        }
        checker = MetastoreTableACLChecker(acl_config)

        # Should block same prefix in different catalog
        assert not checker.is_table_valid("staging.sales", "orders_daily")
        assert not checker.is_table_valid("dev.sales", "orders_monthly")

    def test_allowlist_3level_prefix_different_schema(self):
        """Test that 3-level prefix is schema-specific"""
        acl_config = {
            "type": "allowlist",
            "tables": ["production.sales.orders_*"]
        }
        checker = MetastoreTableACLChecker(acl_config)

        # Should block same prefix in different schema
        assert not checker.is_table_valid("production.hr", "orders_daily")
        assert not checker.is_table_valid("production.analytics", "orders_monthly")

    def test_allowlist_multiple_3level_prefixes(self):
        """Test multiple 3-level prefix patterns"""
        acl_config = {
            "type": "allowlist",
            "tables": [
                "production.sales.orders_*",
                "production.sales.invoice_*",
                "staging.analytics.events_*"
            ]
        }
        checker = MetastoreTableACLChecker(acl_config)

        # Should allow all matching prefixes in production.sales
        assert checker.is_table_valid("production.sales", "orders_daily")
        assert checker.is_table_valid("production.sales", "invoice_summary")

        # Should allow matching prefix in staging.analytics
        assert checker.is_table_valid("staging.analytics", "events_raw")
        assert checker.is_table_valid("staging.analytics", "events_processed")

        # Should block non-matching tables
        assert not checker.is_table_valid("production.sales", "customers")
        assert not checker.is_table_valid("staging.analytics", "users")

    def test_allowlist_3level_prefix_with_schema_wildcard(self):
        """Test 3-level prefix combined with schema wildcard"""
        acl_config = {
            "type": "allowlist",
            "tables": [
                "production.sales.*",
                "staging.analytics.temp_*"
            ]
        }
        checker = MetastoreTableACLChecker(acl_config)

        # Schema wildcard allows all tables in production.sales
        assert checker.is_table_valid("production.sales", "orders")
        assert checker.is_table_valid("production.sales", "customers")
        assert checker.is_table_valid("production.sales", "temp_data")

        # Prefix pattern allows only matching tables in staging.analytics
        assert checker.is_table_valid("staging.analytics", "temp_data")
        assert checker.is_table_valid("staging.analytics", "temp_cache")
        assert not checker.is_table_valid("staging.analytics", "events")

    def test_allowlist_3level_prefix_with_catalog_wildcard(self):
        """Test 3-level prefix combined with catalog wildcard"""
        acl_config = {
            "type": "allowlist",
            "tables": [
                "production.*",
                "staging.analytics.temp_*"
            ]
        }
        checker = MetastoreTableACLChecker(acl_config)

        # Catalog wildcard allows all tables in production
        assert checker.is_table_valid("production.sales", "orders")
        assert checker.is_table_valid("production.hr", "employees")

        # Prefix pattern allows only matching tables in staging.analytics
        assert checker.is_table_valid("staging.analytics", "temp_data")
        assert not checker.is_table_valid("staging.analytics", "events")
        assert not checker.is_table_valid("staging.sales", "temp_data")

    def test_denylist_3level_prefix_basic(self):
        """Test basic 3-level prefix pattern in denylist"""
        acl_config = {
            "type": "denylist",
            "tables": ["production.sales.temp_*"]
        }
        checker = MetastoreTableACLChecker(acl_config)

        # Should block tables matching the prefix
        assert not checker.is_table_valid("production.sales", "temp_data")
        assert not checker.is_table_valid("production.sales", "temp_cache")
        assert not checker.is_table_valid("production.sales", "temp_staging")

        # Should allow tables not matching the prefix
        assert checker.is_table_valid("production.sales", "orders")
        assert checker.is_table_valid("production.sales", "customers")
        assert checker.is_table_valid("production.sales", "temp")

    def test_denylist_3level_prefix_different_locations(self):
        """Test that denylist 3-level prefix only blocks specific location"""
        acl_config = {
            "type": "denylist",
            "tables": ["production.sales.temp_*"]
        }
        checker = MetastoreTableACLChecker(acl_config)

        # Should allow same prefix in different catalog or schema
        assert checker.is_table_valid("staging.sales", "temp_data")
        assert checker.is_table_valid("production.hr", "temp_cache")
        assert checker.is_table_valid("dev.analytics", "temp_staging")

    def test_denylist_multiple_3level_prefixes(self):
        """Test multiple 3-level prefix patterns in denylist"""
        acl_config = {
            "type": "denylist",
            "tables": [
                "production.sales.temp_*",
                "production.analytics.staging_*",
                "dev.testing.test_*"
            ]
        }
        checker = MetastoreTableACLChecker(acl_config)

        # Should block all matching prefixes
        assert not checker.is_table_valid("production.sales", "temp_data")
        assert not checker.is_table_valid("production.analytics", "staging_raw")
        assert not checker.is_table_valid("dev.testing", "test_table")

        # Should allow non-matching tables
        assert checker.is_table_valid("production.sales", "orders")
        assert checker.is_table_valid("production.analytics", "events")
        assert checker.is_table_valid("staging.sales", "orders")

    def test_3level_prefix_empty_prefix_match(self):
        """Test that prefix pattern with wildcard matches zero or more characters"""
        acl_config = {
            "type": "allowlist",
            "tables": ["production.sales.orders_*"]
        }
        checker = MetastoreTableACLChecker(acl_config)

        # Should not match table without the prefix
        assert not checker.is_table_valid("production.sales", "orders")

        # Wildcard * matches zero or more characters, so orders_ is valid
        assert checker.is_table_valid("production.sales", "orders_")
        assert checker.is_table_valid("production.sales", "orders_1")
        assert checker.is_table_valid("production.sales", "orders_a")
        assert checker.is_table_valid("production.sales", "orders_daily")

    def test_3level_prefix_case_sensitivity(self):
        """Test that 3-level prefix patterns are case-sensitive"""
        acl_config = {
            "type": "allowlist",
            "tables": ["production.sales.Orders_*"]
        }
        checker = MetastoreTableACLChecker(acl_config)

        # Case must match exactly
        assert checker.is_table_valid("production.sales", "Orders_Daily")
        assert not checker.is_table_valid("production.sales", "orders_daily")
        assert not checker.is_table_valid("production.sales", "ORDERS_DAILY")

    def test_3level_prefix_special_characters(self):
        """Test 3-level prefix with special characters in prefix"""
        acl_config = {
            "type": "allowlist",
            "tables": ["production.sales.v2_orders_*"]
        }
        checker = MetastoreTableACLChecker(acl_config)

        # Should match prefix with special characters
        assert checker.is_table_valid("production.sales", "v2_orders_daily")
        assert checker.is_table_valid("production.sales", "v2_orders_monthly")

        # Should not match similar but different prefixes
        assert not checker.is_table_valid("production.sales", "v1_orders_daily")
        assert not checker.is_table_valid("production.sales", "v2_invoices_daily")

    def test_3level_prefix_underscore_in_catalog_or_schema(self):
        """Test 3-level prefix with underscores in catalog or schema names"""
        acl_config = {
            "type": "allowlist",
            "tables": ["prod_east.sales_us.orders_*"]
        }
        checker = MetastoreTableACLChecker(acl_config)

        # Should correctly parse catalog and schema with underscores
        assert checker.is_table_valid("prod_east.sales_us", "orders_daily")
        assert checker.is_table_valid("prod_east.sales_us", "orders_monthly")

        # Should not match different catalog/schema
        assert not checker.is_table_valid("prod_west.sales_us", "orders_daily")
        assert not checker.is_table_valid("prod_east.sales_eu", "orders_daily")

    def test_mixed_2level_and_3level_prefix_patterns(self):
        """Test mixing 2-level and 3-level prefix patterns"""
        acl_config = {
            "type": "allowlist",
            "tables": [
                "public.temp_*",  # 2-level prefix
                "production.sales.orders_*"  # 3-level prefix
            ]
        }
        checker = MetastoreTableACLChecker(acl_config)

        # 2-level prefix should work
        assert checker.is_table_valid("public", "temp_data")
        assert checker.is_table_valid("public", "temp_cache")

        # 3-level prefix should work
        assert checker.is_table_valid("production.sales", "orders_daily")
        assert checker.is_table_valid("production.sales", "orders_monthly")

        # Non-matching tables should be blocked
        assert not checker.is_table_valid("public", "users")
        assert not checker.is_table_valid("production.sales", "customers")

    def test_3level_prefix_backward_compatibility_check(self):
        """Test that 3-level prefix doesn't incorrectly match 2-level names"""
        acl_config = {
            "type": "allowlist",
            "tables": ["production.sales.orders_*"]
        }
        checker = MetastoreTableACLChecker(acl_config)

        # Should not match 2-level table name even if last part matches
        assert not checker.is_table_valid("sales", "orders_daily")
        assert not checker.is_table_valid("orders_daily", "some_table")

        # Should only match the full 3-level pattern
        assert checker.is_table_valid("production.sales", "orders_daily")

    def test_3level_prefix_with_exact_table_match(self):
        """Test 3-level prefix combined with exact table matches"""
        acl_config = {
            "type": "allowlist",
            "tables": [
                "production.sales.orders_*",
                "production.sales.customers"  # Exact match
            ]
        }
        checker = MetastoreTableACLChecker(acl_config)

        # Prefix pattern should match
        assert checker.is_table_valid("production.sales", "orders_daily")
        assert checker.is_table_valid("production.sales", "orders_monthly")

        # Exact match should work
        assert checker.is_table_valid("production.sales", "customers")

        # Non-matching tables should be blocked
        assert not checker.is_table_valid("production.sales", "orders")
        assert not checker.is_table_valid("production.sales", "invoices")

    def test_denylist_3level_prefix_with_allowlist_patterns(self):
        """Test that denylist 3-level prefix blocks correctly with other allows"""
        acl_config = {
            "type": "denylist",
            "tables": [
                "production.sales.temp_*",
                "staging.analytics.test_*"
            ]
        }
        checker = MetastoreTableACLChecker(acl_config)

        # Denylist should block matching prefixes
        assert not checker.is_table_valid("production.sales", "temp_data")
        assert not checker.is_table_valid("staging.analytics", "test_data")

        # Everything else should be allowed (denylist default)
        assert checker.is_table_valid("production.sales", "orders")
        assert checker.is_table_valid("production.sales", "customers")
        assert checker.is_table_valid("staging.analytics", "events")
        assert checker.is_table_valid("dev.test", "anything")

    def test_3level_prefix_complex_scenario(self):
        """Test complex real-world scenario with multiple pattern types"""
        acl_config = {
            "type": "allowlist",
            "tables": [
                "production.*",  # Allow all production
                "staging.analytics.*",  # Allow all staging.analytics
                "staging.sales.approved_*",  # But only approved tables in staging.sales
                "dev.testing.experiment_*"  # And only experiment tables in dev.testing
            ]
        }
        checker = MetastoreTableACLChecker(acl_config)

        # Production - everything allowed
        assert checker.is_table_valid("production.sales", "orders")
        assert checker.is_table_valid("production.hr", "employees")

        # Staging analytics - everything allowed
        assert checker.is_table_valid("staging.analytics", "events")
        assert checker.is_table_valid("staging.analytics", "metrics")

        # Staging sales - only approved prefix
        assert checker.is_table_valid("staging.sales", "approved_orders")
        assert checker.is_table_valid("staging.sales", "approved_invoices")
        assert not checker.is_table_valid("staging.sales", "orders")
        assert not checker.is_table_valid("staging.sales", "temp_data")

        # Dev testing - only experiment prefix
        assert checker.is_table_valid("dev.testing", "experiment_a")
        assert checker.is_table_valid("dev.testing", "experiment_results")
        assert not checker.is_table_valid("dev.testing", "other_data")

        # Other locations - blocked
        assert not checker.is_table_valid("dev.sales", "orders")
