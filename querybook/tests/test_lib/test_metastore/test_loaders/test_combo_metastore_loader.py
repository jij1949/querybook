"""
Tests for ComboMetastoreLoader Stage-1 data-loss fix (EGANP-6149).

Covers:
- Base loader delete_schema_not_in_metastore: full prune (backward compat)
- ComboLoader scoped delete overrides: skip, sibling isolation, owned-catalog prune
- load_child: catalog-less mode skips prune (1b)
- load_child: empty discovery raises ComboChildDegradedError
- load_child: catalog overlap skips prune (1e)
- load(): honest FAILURE status when any child fails or is degraded
- Incident reproduction: child A returns 1-of-N, child B returns 0 →
    data_corp schemas never touched; overall run is FAILURE
"""

import unittest
from unittest.mock import MagicMock, patch

from const.metastore import DataCatalog, DataSchema

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

COMBO_DICT_CATALOG = {
    "id": 14,
    "name": "combo-loader",
    "loader": "ComboMetastoreLoader",
    "metastore_params": {
        "sub_loaders": [
            {"metastore_id": 11, "catalogs": "adhoc"},
            {"metastore_id": 12, "catalogs": "data_corp"},
        ]
    },
    "acl_control": {},
    "catalog_display_config": {"enable_catalog_support": True},
}

COMBO_DICT_CATALOGLESS = {
    "id": 14,
    "name": "combo-loader",
    "loader": "ComboMetastoreLoader",
    "metastore_params": {
        "sub_loaders": [
            {"metastore_id": 11},
            {"metastore_id": 12},
        ]
    },
    "acl_control": {},
    "catalog_display_config": {},
}


def _make_db_schema(schema_id, name, catalog_id=None, tables=None):
    obj = MagicMock()
    obj.id = schema_id
    obj.name = name
    obj.catalog_id = catalog_id
    obj.tables = tables or []
    return obj


def _make_data_schema(name, catalog_name=None):
    catalog = DataCatalog(name=catalog_name) if catalog_name else None
    return DataSchema(name=name, catalog=catalog)


# ---------------------------------------------------------------------------
# Base loader: full prune (no scope)
# ---------------------------------------------------------------------------

_BASE_MOD = "lib.metastore.base_metastore_loader"


class TestDeleteSchemaBaseFullPrune(unittest.TestCase):
    """Base loader delete_schema_not_in_metastore always does a full prune."""

    def _make_loader(self):
        from lib.metastore.loaders.glue_data_catalog_loader import GlueDataCatalogLoader

        return GlueDataCatalogLoader(
            {
                "id": 99,
                "name": "test",
                "loader": "GlueDataCatalogLoader",
                "metastore_params": {"catalog_id": "123", "region": "us-east-1"},
                "acl_control": {},
                "catalog_display_config": {},
            }
        )

    @patch(f"{_BASE_MOD}.get_catalog_by_id")
    @patch(f"{_BASE_MOD}.delete_schema")
    @patch(f"{_BASE_MOD}.delete_table")
    @patch(f"{_BASE_MOD}.delete_es_table_by_id")
    @patch(f"{_BASE_MOD}.iterate_data_schema")
    def test_full_prune_deletes_stale_schemas(
        self,
        mock_iterate,
        mock_delete_es,
        mock_delete_table,
        mock_delete_schema,
        mock_get_catalog,
    ):
        """Base full prune: stale DB schema not in fresh discovery is deleted."""
        loader = self._make_loader()
        session = MagicMock()

        db_schema_a = _make_db_schema(1, "schema_a", catalog_id=None)
        db_schema_b = _make_db_schema(2, "schema_b", catalog_id=None)
        mock_iterate.return_value = iter([db_schema_a, db_schema_b])

        fresh = [_make_data_schema("schema_a")]  # schema_b absent → should be pruned
        loader.delete_schema_not_in_metastore(99, fresh, session=session)

        deleted_ids = {c.kwargs["id"] for c in mock_delete_schema.call_args_list}
        self.assertIn(2, deleted_ids)
        self.assertNotIn(1, deleted_ids)


# ---------------------------------------------------------------------------
# ComboLoader scoped delete overrides
# ---------------------------------------------------------------------------

_COMBO_MOD = "lib.metastore.loaders.combo_metastore_loader"


class TestComboLoaderScopedDelete(unittest.TestCase):
    """ComboLoader overrides scope delete_schema/catalog to owned rows only."""

    def _make_combo(self):
        from lib.metastore.loaders.combo_metastore_loader import ComboMetastoreLoader

        with patch(f"{_COMBO_MOD}.get_metastore_loader"):
            return ComboMetastoreLoader(COMBO_DICT_CATALOG)

    @patch(f"{_COMBO_MOD}.get_catalog_by_id")
    @patch(f"{_COMBO_MOD}.delete_schema")
    @patch(f"{_COMBO_MOD}.delete_table")
    @patch(f"{_COMBO_MOD}.delete_es_table_by_id")
    @patch(f"{_COMBO_MOD}.iterate_data_schema")
    def test_skip_prune_when_scope_is_empty_set(
        self,
        mock_iterate,
        mock_delete_es,
        mock_delete_table,
        mock_delete_schema,
        mock_get_catalog,
    ):
        """_current_prune_scope=set() → skip prune entirely; nothing deleted."""
        combo = self._make_combo()
        session = MagicMock()
        mock_iterate.return_value = iter([_make_db_schema(1, "schema_a")])

        combo._current_prune_scope = set()
        combo.delete_schema_not_in_metastore(14, [], session=session)

        mock_delete_schema.assert_not_called()
        mock_delete_table.assert_not_called()

    @patch(f"{_COMBO_MOD}.get_catalog_by_id")
    @patch(f"{_COMBO_MOD}.delete_schema")
    @patch(f"{_COMBO_MOD}.delete_table")
    @patch(f"{_COMBO_MOD}.delete_es_table_by_id")
    @patch(f"{_COMBO_MOD}.iterate_data_schema")
    def test_scoped_prune_does_not_touch_sibling_schemas(
        self,
        mock_iterate,
        mock_delete_es,
        mock_delete_table,
        mock_delete_schema,
        mock_get_catalog,
    ):
        """Scoped prune: rows NOT in owned scope are never touched (sibling isolation)."""
        combo = self._make_combo()
        session = MagicMock()

        adhoc_cat_id, corp_cat_id = 100, 200

        def catalog_side_effect(catalog_id, session=None):
            m = MagicMock()
            m.name = "adhoc" if catalog_id == adhoc_cat_id else "data_corp"
            return m

        mock_get_catalog.side_effect = catalog_side_effect

        db_adhoc_user = _make_db_schema(1, "user_schema", catalog_id=adhoc_cat_id)
        db_adhoc_info = _make_db_schema(
            2, "information_schema", catalog_id=adhoc_cat_id
        )
        db_corp = _make_db_schema(3, "corp_schema", catalog_id=corp_cat_id)
        mock_iterate.return_value = iter([db_adhoc_user, db_adhoc_info, db_corp])

        fresh = [_make_data_schema("information_schema", catalog_name="adhoc")]
        # Scope is now a Set[str] of catalog names, not schema tuples.
        combo._current_prune_scope = {"adhoc"}
        combo.delete_schema_not_in_metastore(14, fresh, session=session)

        deleted_ids = {c.kwargs["id"] for c in mock_delete_schema.call_args_list}
        self.assertIn(1, deleted_ids, "user_schema (stale, owned) must be pruned")
        self.assertNotIn(3, deleted_ids, "corp_schema (sibling) must never be touched")
        self.assertNotIn(
            2, deleted_ids, "information_schema (still in discovery) must be kept"
        )

    @patch(f"{_COMBO_MOD}.delete_catalog")
    @patch(f"{_COMBO_MOD}.get_all_catalogs")
    def test_skip_catalog_prune_when_scope_is_empty_set(
        self, mock_get_catalogs, mock_delete_catalog
    ):
        """_current_prune_scope=set() → skip catalog prune entirely."""
        combo = self._make_combo()
        session = MagicMock()

        cat = MagicMock()
        cat.id = 10
        cat.name = "adhoc"
        mock_get_catalogs.return_value = [cat]

        combo._current_prune_scope = set()
        combo.delete_catalog_not_in_metastore(14, [], session=session)

        mock_delete_catalog.assert_not_called()

    @patch(f"{_COMBO_MOD}.delete_catalog")
    @patch(f"{_COMBO_MOD}.get_all_catalogs")
    def test_scoped_catalog_prune_ignores_sibling_catalog(
        self, mock_get_catalogs, mock_delete_catalog
    ):
        """Scoped catalog prune: sibling catalog absent from scope is never deleted."""
        combo = self._make_combo()
        session = MagicMock()

        cat_adhoc = MagicMock()
        cat_adhoc.id, cat_adhoc.name = 10, "adhoc"
        cat_corp = MagicMock()
        cat_corp.id, cat_corp.name = 20, "data_corp"
        mock_get_catalogs.return_value = [cat_adhoc, cat_corp]

        fresh = [_make_data_schema("schema_a", catalog_name="adhoc")]
        combo._current_prune_scope = {"adhoc"}
        combo.delete_catalog_not_in_metastore(14, fresh, session=session)

        mock_delete_catalog.assert_not_called()

    @patch(f"{_COMBO_MOD}.delete_catalog")
    @patch(f"{_COMBO_MOD}.get_all_catalogs")
    def test_scoped_catalog_prune_deletes_owned_missing_catalog(
        self, mock_get_catalogs, mock_delete_catalog
    ):
        """Owned catalog absent from discovery is deleted."""
        combo = self._make_combo()
        session = MagicMock()

        cat_adhoc = MagicMock()
        cat_adhoc.id, cat_adhoc.name = 10, "adhoc"
        cat_old = MagicMock()
        cat_old.id, cat_old.name = 11, "adhoc_old"
        mock_get_catalogs.return_value = [cat_adhoc, cat_old]

        fresh = [_make_data_schema("schema_a", catalog_name="adhoc")]
        combo._current_prune_scope = {"adhoc", "adhoc_old"}
        combo.delete_catalog_not_in_metastore(14, fresh, session=session)

        deleted_ids = {
            c.kwargs["catalog_id"] for c in mock_delete_catalog.call_args_list
        }
        self.assertIn(11, deleted_ids)
        self.assertNotIn(10, deleted_ids)


# ---------------------------------------------------------------------------
# ComboMetastoreLoader load_child and load() Stage-1 logic
# ---------------------------------------------------------------------------


class TestComboMetastoreLoaderStage1(unittest.TestCase):

    def _make_combo(self, metastore_dict=None):
        from lib.metastore.loaders.combo_metastore_loader import ComboMetastoreLoader

        with patch(f"{_COMBO_MOD}.get_metastore_loader"):
            return ComboMetastoreLoader(metastore_dict or COMBO_DICT_CATALOG)

    def _make_child_loader(self, schema_names, catalog_name="adhoc"):
        child = MagicMock()
        child.get_all_schema_names.return_value = [
            _make_data_schema(name, catalog_name=catalog_name) for name in schema_names
        ]
        return child

    # ------------------------------------------------------------------
    # 1b: catalog-less mode skips prune
    # ------------------------------------------------------------------

    def test_load_child_catalogless_skips_prune(self):
        """In catalog-less mode load_child passes set() (skip) to _load_scoped."""
        combo = self._make_combo(COMBO_DICT_CATALOGLESS)
        combo._loader_cache[11] = self._make_child_loader(
            ["schema_a", "schema_b"], catalog_name=None
        )

        captured = []

        def mock_load_scoped(schemas, owned_catalog_names=None):
            captured.append(owned_catalog_names)

        combo._load_scoped = mock_load_scoped
        combo.load_child(11)

        self.assertEqual(len(captured), 1)
        self.assertIsNotNone(captured[0])
        self.assertEqual(
            len(captured[0]), 0, "catalog-less mode must pass empty owned keys"
        )

    # ------------------------------------------------------------------
    # Empty discovery detection
    # ------------------------------------------------------------------

    def test_load_child_empty_discovery_raises(self):
        """Child returning 0 schemas must skip prune and raise ComboChildDegradedError."""
        from lib.metastore.loaders.combo_metastore_loader import ComboChildDegradedError

        combo = self._make_combo()
        combo._loader_cache[11] = self._make_child_loader([], catalog_name="adhoc")

        captured = []

        def mock_load_scoped(schemas, owned_catalog_names=None):
            captured.append(owned_catalog_names)

        combo._load_scoped = mock_load_scoped

        with self.assertRaises(ComboChildDegradedError) as ctx:
            combo.load_child(11)

        self.assertEqual(len(captured), 1, "upsert must still run")
        self.assertEqual(
            len(captured[0]), 0, "empty discovery must produce empty scope"
        )
        self.assertIn("0 schemas", str(ctx.exception))

    @patch(f"{_COMBO_MOD}.get_catalog_by_id")
    @patch(f"{_COMBO_MOD}.delete_schema")
    @patch(f"{_COMBO_MOD}.delete_table")
    @patch(f"{_COMBO_MOD}.delete_es_table_by_id")
    @patch(f"{_COMBO_MOD}.iterate_data_schema")
    def test_load_child_scoped_prune_deletes_stale_owned_schema(
        self,
        mock_iterate,
        mock_delete_es,
        mock_delete_table,
        mock_delete_schema,
        mock_get_catalog,
    ):
        """REGRESSION (Fix #1): scoped prune must delete stale schemas within owned catalogs.

        Previously owned_schema_keys was built from fresh discovery, making the delete
        condition (key in scope AND key not in expected) unsatisfiable — stale schemas
        within owned catalogs were never pruned.
        """
        combo = self._make_combo()  # child 11 owns "adhoc"
        # Fresh discovery: only schema_a survived; schema_stale was decommissioned.
        combo._loader_cache[11] = self._make_child_loader(
            ["schema_a"], catalog_name="adhoc"
        )

        adhoc_cat_id = 100

        def catalog_side_effect(catalog_id, session=None):
            m = MagicMock()
            m.name = "adhoc"
            return m

        mock_get_catalog.side_effect = catalog_side_effect

        # DB has both schema_a (still exists) and schema_stale (decommissioned)
        db_schema_a = _make_db_schema(1, "schema_a", catalog_id=adhoc_cat_id)
        db_schema_stale = _make_db_schema(2, "schema_stale", catalog_id=adhoc_cat_id)
        mock_iterate.return_value = iter([db_schema_a, db_schema_stale])

        combo.load_child(11)  # must not raise

        # schema_stale (id=2) is in an owned catalog but absent from fresh discovery → delete
        deleted_ids = {c.kwargs["id"] for c in mock_delete_schema.call_args_list}
        self.assertIn(2, deleted_ids, "stale schema in owned catalog must be pruned")
        self.assertNotIn(1, deleted_ids, "schema_a still in discovery must be kept")

    def test_load_child_healthy_discovery_applies_scoped_prune(self):
        """Normal discovery passes owned catalog names as the prune scope."""
        combo = self._make_combo()
        schema_names = [f"schema_{i}" for i in range(5)]
        combo._loader_cache[11] = self._make_child_loader(
            schema_names, catalog_name="adhoc"
        )

        captured = []

        def mock_load_scoped(schemas, owned_catalog_names=None):
            captured.append(owned_catalog_names)

        combo._load_scoped = mock_load_scoped
        combo.load_child(11)  # must not raise

        self.assertEqual(len(captured), 1)
        # Scope is now Set[str] of owned catalog names, not schema tuples.
        self.assertEqual(
            captured[0], {"adhoc"}, "prune scope must be the owned catalog name set"
        )

    # ------------------------------------------------------------------
    # 1e: catalog overlap gate
    # ------------------------------------------------------------------

    def test_load_child_catalog_overlap_skips_prune(self):
        """If a discovered catalog belongs to another child, prune is skipped."""
        from lib.metastore.loaders.combo_metastore_loader import ComboChildDegradedError

        combo = self._make_combo()
        combo._loader_cache[11] = self._make_child_loader(
            ["corp_schema"], catalog_name="data_corp"
        )

        captured = []

        def mock_load_scoped(schemas, owned_catalog_names=None):
            captured.append(owned_catalog_names)

        combo._load_scoped = mock_load_scoped

        with self.assertRaises(ComboChildDegradedError) as ctx:
            combo.load_child(11)

        self.assertEqual(
            len(captured), 1, "upserts must run even when overlap detected"
        )
        self.assertEqual(len(captured[0]), 0, "overlap must produce empty owned scope")
        self.assertIn("overlap", str(ctx.exception))

    # ------------------------------------------------------------------
    # load() honest status
    # ------------------------------------------------------------------

    def test_load_raises_when_child_discovery_fails(self):
        """load() raises RuntimeError when any child's sync throws; siblings still run."""
        combo = self._make_combo()
        call_order = []

        def load_child_side_effect(child_id):
            call_order.append(child_id)
            if child_id == 11:
                raise RuntimeError("connection timeout")
            return []  # child 12 succeeds

        combo.load_child = MagicMock(side_effect=load_child_side_effect)

        with self.assertRaises(RuntimeError) as ctx:
            combo.load()

        self.assertIn(11, call_order)
        self.assertIn(12, call_order)
        self.assertIn("11", str(ctx.exception))

    def test_load_raises_when_child_is_degraded(self):
        """load() raises (FAILURE) even when only a child's prune was skipped."""
        from lib.metastore.loaders.combo_metastore_loader import ComboChildDegradedError

        combo = self._make_combo()
        call_order = []

        def load_child_side_effect(child_id):
            call_order.append(child_id)
            if child_id == 11:
                raise ComboChildDegradedError("prune skipped: 0 schemas")
            return []

        combo.load_child = MagicMock(side_effect=load_child_side_effect)

        with self.assertRaises(RuntimeError) as ctx:
            combo.load()

        self.assertIn(11, call_order)
        self.assertIn(12, call_order)
        self.assertIn("11", str(ctx.exception))

    def test_load_succeeds_when_all_children_ok(self):
        """load() does not raise when all children sync cleanly."""
        combo = self._make_combo()
        combo.load_child = MagicMock(return_value=[])
        # COMBO_DICT_CATALOG has explicit catalog ownership → _delete_unclaimed_schemas branch
        combo._delete_unclaimed_schemas = MagicMock()
        combo.load()

    # ------------------------------------------------------------------
    # Incident reproduction (regression)
    # ------------------------------------------------------------------

    def test_incident_sibling_isolation_and_run_is_failure(self):
        """REGRESSION (2026-06-05): child 11 returns 1-of-N schemas (truncated),
        child 12 returns 0 schemas.

        Guarantees:
        - data_corp schemas (child 12's catalog) are NEVER touched by child 11's prune
        - child 12's empty discovery raises ComboChildDegradedError
        - overall run is FAILURE
        """
        combo = (
            self._make_combo()
        )  # catalog-enabled, child 11→adhoc, child 12→data_corp

        # Child 11: 1 schema only (truncated discovery)
        child_11 = self._make_child_loader(["information_schema"], catalog_name="adhoc")
        # Child 12: 0 schemas (permission lapse)
        child_12 = self._make_child_loader([], catalog_name="data_corp")

        combo._loader_cache[11] = child_11
        combo._loader_cache[12] = child_12

        load_scoped_calls = []  # (child schemas, owned_catalog_names) per call

        def mock_load_scoped(schemas, owned_catalog_names=None):
            load_scoped_calls.append((schemas, owned_catalog_names))

        combo._load_scoped = mock_load_scoped

        with self.assertRaises(RuntimeError) as ctx:
            combo.load()

        # Both children must have had their upserts attempted
        self.assertEqual(len(load_scoped_calls), 2, "both children must run upserts")

        # Child 11 (1 schema): scope is Set[str] of owned catalog names — "adhoc" only.
        # data_corp is never in this set, so child 11 can never prune data_corp rows.
        _, child_11_scope = load_scoped_calls[0]
        if child_11_scope:
            self.assertNotIn(
                "data_corp", child_11_scope, "child 11 must not own data_corp catalog"
            )

        # Child 12 (0 schemas): empty scope → prune skipped
        _, child_12_scope = load_scoped_calls[1]
        self.assertIsNotNone(child_12_scope)
        self.assertEqual(
            len(child_12_scope), 0, "empty discovery must produce empty scope"
        )

        # Overall run must be FAILURE
        err_msg = str(ctx.exception)
        self.assertIn("12", err_msg)


# ---------------------------------------------------------------------------
# Stage 2: run_child_sync / run_finalize_sync unit tests
# ---------------------------------------------------------------------------

# These functions are imported inside methods (delayed imports), so we must
# patch them at their SOURCE module, not at the combo loader module level.
_REDIS_MOD = "clients.redis_client"
_SCHEDULE_MOD = "logic.schedule"


class TestComboMetastoreLoaderStage2(unittest.TestCase):
    """Unit tests for the Stage 2 Celery task helpers."""

    def _make_combo(self):
        from lib.metastore.loaders.combo_metastore_loader import ComboMetastoreLoader

        with patch(f"{_COMBO_MOD}.get_metastore_loader"):
            return ComboMetastoreLoader(COMBO_DICT_CATALOG)

    def _make_celery_task(self, shadow="update_metastore_14_child_11"):
        task = MagicMock()
        task.request.get = MagicMock(
            side_effect=lambda k, default=None: shadow if k == "shadow" else default
        )
        task.name = shadow
        return task

    # ------------------------------------------------------------------
    # run_child_sync: lock contention path
    # ------------------------------------------------------------------

    @patch(f"{_REDIS_MOD}.get_redis")
    def test_run_child_sync_lock_held_marks_failure(self, mock_get_redis):
        """When the Redis lock is already held, child record is FAILURE and load_unit is not called."""
        from const.schedule import TaskRunStatus

        combo = self._make_combo()
        celery_task = self._make_celery_task()

        redis_conn = MagicMock()
        redis_conn.set.return_value = None  # lock NOT acquired
        mock_get_redis.return_value = redis_conn

        record_id = 42
        updated_records = []

        with patch(
            f"{_SCHEDULE_MOD}.create_task_run_record_for_celery_task",
            return_value=record_id,
        ), patch(
            f"{_SCHEDULE_MOD}.update_task_run_record",
            side_effect=lambda **kwargs: updated_records.append(kwargs),
        ):
            combo.load_unit = MagicMock()
            combo.run_child_sync(celery_task, child_id=11)

        # load_unit must NOT have been called
        combo.load_unit.assert_not_called()

        # Record must be marked FAILURE with an informative message
        self.assertEqual(len(updated_records), 1)
        self.assertEqual(updated_records[0]["status"], TaskRunStatus.FAILURE)
        self.assertIn("lock already held", updated_records[0]["error_message"])
        self.assertIn("11", updated_records[0]["error_message"])

    # ------------------------------------------------------------------
    # run_finalize_sync: correlation-key lookup
    # ------------------------------------------------------------------

    @patch(f"{_REDIS_MOD}.get_redis")
    def test_run_finalize_sync_uses_redis_correlation_key(self, mock_get_redis):
        """Finalize resolves child records via the Redis correlation key, not name lookup."""
        from const.schedule import TaskRunStatus

        combo = self._make_combo()
        parent_record_id = 100
        child_record_id = 55

        redis_conn = MagicMock()
        redis_conn.get.side_effect = lambda key: (
            str(child_record_id).encode()
            if f"combo_child_record:{combo.metastore_id}:11:{parent_record_id}" in key
            else None
        )
        mock_get_redis.return_value = redis_conn

        child_record = MagicMock()
        child_record.status = TaskRunStatus.SUCCESS

        with patch(
            f"{_SCHEDULE_MOD}.get_task_run_record",
            return_value=child_record,
        ) as mock_get_by_id, patch(
            f"{_SCHEDULE_MOD}.get_task_run_record_run_by_name",
            return_value=([child_record], 1),
        ), patch(
            f"{_SCHEDULE_MOD}.update_task_run_record"
        ), patch.object(
            combo, "_run_cleanup_after_sync"
        ):
            combo.run_finalize_sync([11], record_id=parent_record_id)

        # Should have used get_task_run_record (by ID), not name-based lookup
        mock_get_by_id.assert_called_once_with(child_record_id)

    # ------------------------------------------------------------------
    # run_finalize_sync: SUCCESS path triggers cleanup
    # ------------------------------------------------------------------

    @patch(f"{_REDIS_MOD}.get_redis")
    def test_run_finalize_sync_success_triggers_cleanup(self, mock_get_redis):
        """When all children succeed, finalize runs cleanup and marks combo SUCCESS."""
        from const.schedule import TaskRunStatus

        combo = self._make_combo()
        parent_record_id = 200

        redis_conn = MagicMock()
        redis_conn.get.return_value = None  # no correlation key → name-based fallback
        mock_get_redis.return_value = redis_conn

        child_record = MagicMock()
        child_record.status = TaskRunStatus.SUCCESS

        updated_records = []

        with patch(
            f"{_SCHEDULE_MOD}.get_task_run_record_run_by_name",
            return_value=([child_record], 1),
        ), patch(
            f"{_SCHEDULE_MOD}.update_task_run_record",
            side_effect=lambda **kwargs: updated_records.append(kwargs),
        ), patch.object(
            combo, "_run_cleanup_after_sync"
        ) as mock_cleanup:
            combo.run_finalize_sync([11, 12], record_id=parent_record_id)

        # Cleanup must have fired
        mock_cleanup.assert_called_once()

        # Combo record must be marked SUCCESS
        success_updates = [
            r for r in updated_records if r.get("status") == TaskRunStatus.SUCCESS
        ]
        self.assertEqual(len(success_updates), 1)
        self.assertEqual(success_updates[0]["id"], parent_record_id)


if __name__ == "__main__":
    unittest.main()
