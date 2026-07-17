import sys
from types import ModuleType
from unittest import TestCase
from unittest.mock import MagicMock, patch

# The CI runner doesn't install databricks-sdk. Stub the (third-party) package so
# the real DatabricksMetastoreLoader can be imported by the real-registry tests
# below. Mirrors the stub in test_databricks_client.py; stubs only the absent
# SDK, never first-party querybook modules.
_databricks_stub = ModuleType("databricks")
_databricks_stub.sdk = ModuleType("databricks.sdk")
_databricks_stub.sdk.WorkspaceClient = MagicMock()
_databricks_stub.sdk.core = ModuleType("databricks.sdk.core")
_databricks_stub.sdk.core.Config = MagicMock()
_databricks_stub.sdk.service = ModuleType("databricks.sdk.service")
_databricks_stub.sdk.service.catalog = ModuleType("databricks.sdk.service.catalog")
_databricks_stub.sdk.service.catalog.TableInfo = MagicMock()
sys.modules.setdefault("databricks", _databricks_stub)
sys.modules.setdefault("databricks.sdk", _databricks_stub.sdk)
sys.modules.setdefault("databricks.sdk.core", _databricks_stub.sdk.core)
sys.modules.setdefault("databricks.sdk.service", _databricks_stub.sdk.service)
sys.modules.setdefault(
    "databricks.sdk.service.catalog", _databricks_stub.sdk.service.catalog
)


# ---------------------------------------------------------------------------
# Fake loader classes used in _get_loader_by_name() patches.
# The issubclass detection requires a real class hierarchy:
#   FakeComboMetastoreLoader (the "combo" base)
#   FakeComboSubclass(FakeComboMetastoreLoader)  — exercises combo detection
# ---------------------------------------------------------------------------

class FakeBaseLoader:
    REQUIRES_OIDC_WORKER = False


class FakeDatabricksLoader(FakeBaseLoader):
    REQUIRES_OIDC_WORKER = True


class FakeGlueLoader(FakeBaseLoader):
    REQUIRES_OIDC_WORKER = False


class FakeComboMetastoreLoader(FakeBaseLoader):
    REQUIRES_OIDC_WORKER = False


class FakeComboSubclass(FakeComboMetastoreLoader):
    pass


def _make_metastore(loader_name, metastore_params=None):
    m = MagicMock()
    m.loader = loader_name
    m.metastore_params = metastore_params or {}
    return m


class TestRouteMetastoreTask(TestCase):

    def _call(self, name, args=(), kwargs=None):
        from tasks.routing import route_metastore_task
        return route_metastore_task(name, args, kwargs or {}, {})

    @patch("tasks.routing._metastore_requires_oidc_worker", return_value=True)
    def test_update_metastore_routes_to_k8s_queue(self, _):
        result = self._call("tasks.update_metastore.update_metastore", args=(42,))
        self.assertEqual(result, {"queue": "k8s-only"})

    @patch("tasks.routing._metastore_requires_oidc_worker", return_value=False)
    def test_non_databricks_metastore_returns_none(self, _):
        result = self._call("tasks.update_metastore.update_metastore", args=(42,))
        self.assertIsNone(result)

    @patch("tasks.routing._metastore_requires_oidc_worker", return_value=True)
    def test_update_metastore_child_extracts_combo_id(self, mock_check):
        result = self._call(
            "tasks.update_metastore.update_metastore_child", args=(42, 1)
        )
        self.assertEqual(result, {"queue": "k8s-only"})
        mock_check.assert_called_once_with(42)

    @patch("tasks.routing._metastore_requires_oidc_worker", return_value=True)
    def test_finalize_combo_metastore_routes_to_k8s_queue(self, mock_check):
        """finalize_combo_metastore is now routed (it re-connects to Databricks child)."""
        result = self._call(
            "tasks.update_metastore.finalize_combo_metastore", args=(42,)
        )
        self.assertEqual(result, {"queue": "k8s-only"})
        mock_check.assert_called_once_with(42)

    @patch("tasks.routing._metastore_requires_oidc_worker", return_value=False)
    def test_finalize_combo_non_databricks_returns_none(self, mock_check):
        result = self._call(
            "tasks.update_metastore.finalize_combo_metastore", args=(42,)
        )
        self.assertIsNone(result)

    def test_unrelated_task_returns_none(self):
        result = self._call("tasks.some_other_task.run", args=(1,))
        self.assertIsNone(result)

    @patch("tasks.routing._metastore_requires_oidc_worker", return_value=True)
    def test_metastore_id_extracted_from_kwargs(self, mock_check):
        result = self._call(
            "tasks.update_metastore.update_metastore", args=(), kwargs={"id": 99}
        )
        self.assertEqual(result, {"queue": "k8s-only"})
        mock_check.assert_called_once_with(99)

    @patch("tasks.routing._metastore_requires_oidc_worker")
    def test_missing_metastore_id_returns_none(self, mock_check):
        result = self._call(
            "tasks.update_metastore.update_metastore", args=(), kwargs={}
        )
        self.assertIsNone(result)
        mock_check.assert_not_called()

    @patch(
        "tasks.routing._metastore_requires_oidc_worker",
        side_effect=RuntimeError("transient DB error"),
    )
    def test_routing_lookup_error_falls_back_to_default(self, _):
        # A lookup failure at dispatch time must not propagate out of the router
        # (which Celery calls synchronously at task-publish time) and break
        # dispatch; it falls back to the default queue.
        result = self._call("tasks.update_metastore.update_metastore", args=(42,))
        self.assertIsNone(result)

    @patch("tasks.routing._metastore_requires_oidc_worker", return_value=True)
    def test_metastore_id_zero_is_not_treated_as_missing(self, mock_check):
        # id=0 is a valid id, not a "missing id" — it must still be routed.
        result = self._call("tasks.update_metastore.update_metastore", args=(0,))
        self.assertEqual(result, {"queue": "k8s-only"})
        mock_check.assert_called_once_with(0)


class TestMetastoreRequiresOidcWorker(TestCase):

    def setUp(self):
        # Patch the QueryMetastore the resolver imports locally, and the lazy
        # loader-registry accessor. These are per-test (auto-restored) patches,
        # so they don't leak across tests. (The module-level databricks-SDK stub
        # at the top of this file IS a deliberate process-global sys.modules
        # stub, but it only stubs the absent third-party SDK, never first-party
        # querybook modules.)
        qm_patcher = patch("models.admin.QueryMetastore")
        self.mock_qm = qm_patcher.start()
        self.addCleanup(qm_patcher.stop)

    def _patch_loaders(self, loader_map):
        p = patch("tasks.routing._get_loader_by_name", return_value=loader_map)
        p.start()
        self.addCleanup(p.stop)

    # ------------------------------------------------------------------
    # Standalone loaders
    # ------------------------------------------------------------------

    def test_standalone_databricks_returns_true(self):
        self.mock_qm.get.return_value = _make_metastore("DatabricksMetastoreLoader")
        self._patch_loaders(
            {
                "DatabricksMetastoreLoader": FakeDatabricksLoader,
                "ComboMetastoreLoader": FakeComboMetastoreLoader,
            }
        )
        from tasks.routing import _metastore_requires_oidc_worker
        self.assertTrue(_metastore_requires_oidc_worker(1))

    def test_standalone_non_oidc_loader_returns_false(self):
        self.mock_qm.get.return_value = _make_metastore("GlueDataCatalogLoader")
        self._patch_loaders(
            {
                "GlueDataCatalogLoader": FakeGlueLoader,
                "ComboMetastoreLoader": FakeComboMetastoreLoader,
            }
        )
        from tasks.routing import _metastore_requires_oidc_worker
        self.assertFalse(_metastore_requires_oidc_worker(1))

    def test_metastore_not_found_returns_false(self):
        self.mock_qm.get.return_value = None
        self._patch_loaders({"ComboMetastoreLoader": FakeComboMetastoreLoader})
        from tasks.routing import _metastore_requires_oidc_worker
        self.assertFalse(_metastore_requires_oidc_worker(999))

    def test_unknown_loader_name_returns_false(self):
        self.mock_qm.get.return_value = _make_metastore("UnknownLoader")
        self._patch_loaders({"ComboMetastoreLoader": FakeComboMetastoreLoader})
        from tasks.routing import _metastore_requires_oidc_worker
        self.assertFalse(_metastore_requires_oidc_worker(1))

    # ------------------------------------------------------------------
    # Combo cases
    # ------------------------------------------------------------------

    def _setup_combo_get(self, combo_id, child_ids_and_loaders):
        """
        Stub QueryMetastore.get to return:
          - combo_id  → ComboMetastoreLoader with sub_loaders listing child_ids
          - each child_id → the loader class name given in child_ids_and_loaders
        """
        sub_loaders = [{"metastore_id": cid} for cid in child_ids_and_loaders]
        combo_metastore = _make_metastore(
            "ComboMetastoreLoader",
            metastore_params={"sub_loaders": sub_loaders},
        )

        def fake_get(id):
            if id == combo_id:
                return combo_metastore
            loader_name = child_ids_and_loaders.get(id)
            if loader_name:
                return _make_metastore(loader_name)
            return None

        self.mock_qm.get.side_effect = fake_get

    def test_combo_with_databricks_child_returns_true(self):
        # combo id=14, children: 11=Databricks, 12=Glue, 13=Glue
        self._setup_combo_get(
            14,
            {
                11: "DatabricksMetastoreLoader",
                12: "GlueDataCatalogLoader",
                13: "GlueDataCatalogLoader",
            },
        )
        self._patch_loaders(
            {
                "ComboMetastoreLoader": FakeComboMetastoreLoader,
                "DatabricksMetastoreLoader": FakeDatabricksLoader,
                "GlueDataCatalogLoader": FakeGlueLoader,
            }
        )
        from tasks.routing import _metastore_requires_oidc_worker
        self.assertTrue(_metastore_requires_oidc_worker(14))

    def test_combo_without_databricks_child_returns_false(self):
        self._setup_combo_get(
            14, {12: "GlueDataCatalogLoader", 13: "GlueDataCatalogLoader"}
        )
        self._patch_loaders(
            {
                "ComboMetastoreLoader": FakeComboMetastoreLoader,
                "GlueDataCatalogLoader": FakeGlueLoader,
            }
        )
        from tasks.routing import _metastore_requires_oidc_worker
        self.assertFalse(_metastore_requires_oidc_worker(14))

    def test_combo_child_id_zero_is_not_skipped(self):
        # A combo child with metastore_id=0 is a valid id and must be recursed
        # into, not skipped by a truthiness check.
        self._setup_combo_get(14, {0: "DatabricksMetastoreLoader"})
        self._patch_loaders(
            {
                "ComboMetastoreLoader": FakeComboMetastoreLoader,
                "DatabricksMetastoreLoader": FakeDatabricksLoader,
            }
        )
        from tasks.routing import _metastore_requires_oidc_worker
        self.assertTrue(_metastore_requires_oidc_worker(14))

    def test_combo_databricks_routes_all_three_tasks(self):
        """All three task names for a Databricks combo should route to k8s-only."""
        self._setup_combo_get(14, {11: "DatabricksMetastoreLoader"})
        self._patch_loaders(
            {
                "ComboMetastoreLoader": FakeComboMetastoreLoader,
                "DatabricksMetastoreLoader": FakeDatabricksLoader,
            }
        )
        from tasks.routing import route_metastore_task
        task_names = [
            "tasks.update_metastore.update_metastore",
            "tasks.update_metastore.update_metastore_child",
            "tasks.update_metastore.finalize_combo_metastore",
        ]
        for task_name in task_names:
            result = route_metastore_task(task_name, (14,), {}, {})
            self.assertEqual(
                result,
                {"queue": "k8s-only"},
                f"Expected k8s-only routing for task {task_name}",
            )

    def test_nested_combo_terminates_via_seen_guard(self):
        """A cyclic combo (id 1 references itself) must terminate and return False."""
        cyclic = _make_metastore(
            "ComboMetastoreLoader",
            metastore_params={"sub_loaders": [{"metastore_id": 1}]},
        )
        self.mock_qm.get.return_value = cyclic
        self._patch_loaders({"ComboMetastoreLoader": FakeComboMetastoreLoader})
        from tasks.routing import _metastore_requires_oidc_worker
        self.assertFalse(_metastore_requires_oidc_worker(1))

    def test_combo_no_sub_loaders_key_returns_false(self):
        """Combo metastore with no sub_loaders in params returns False."""
        self.mock_qm.get.return_value = _make_metastore(
            "ComboMetastoreLoader", metastore_params={}
        )
        self._patch_loaders({"ComboMetastoreLoader": FakeComboMetastoreLoader})
        from tasks.routing import _metastore_requires_oidc_worker
        self.assertFalse(_metastore_requires_oidc_worker(1))

    def test_combo_subclass_with_databricks_child_returns_true(self):
        """A subclass of ComboMetastoreLoader is detected as a combo via issubclass."""
        combo_metastore = _make_metastore(
            "FakeComboSubclass",
            metastore_params={"sub_loaders": [{"metastore_id": 21}]},
        )

        def fake_get(id):
            if id == 20:
                return combo_metastore
            if id == 21:
                return _make_metastore("DatabricksMetastoreLoader")
            return None

        self.mock_qm.get.side_effect = fake_get
        self._patch_loaders(
            {
                "ComboMetastoreLoader": FakeComboMetastoreLoader,
                "FakeComboSubclass": FakeComboSubclass,
                "DatabricksMetastoreLoader": FakeDatabricksLoader,
            }
        )
        from tasks.routing import route_metastore_task
        result = route_metastore_task(
            "tasks.update_metastore.update_metastore", (), {"id": 20}, {}
        )
        self.assertEqual(result, {"queue": "k8s-only"})


class TestRealLoaderRegistry(TestCase):
    """Exercise the REAL loader classes (not Fake stand-ins), so a regression in
    the actual REQUIRES_OIDC_WORKER declaration is caught — the Fake-based tests
    above would not catch a revert of the flag on the real Databricks loader.

    Note: we intentionally do NOT assert registry membership
    (ALL_METASTORE_LOADERS) here — the Databricks loader is conditionally
    registered based on the optional databricks-sdk dependency, which is absent
    in the CI test image, so its presence in the registry is environment-
    dependent and not a stable assertion target."""

    def test_real_loader_classes_declare_oidc_requirement(self):
        # A revert of the flag on the real Databricks loader would fail here.
        from lib.metastore.base_metastore_loader import BaseMetastoreLoader
        from lib.metastore.loaders.databricks_metastore_loader import (
            DatabricksMetastoreLoader,
        )

        self.assertFalse(BaseMetastoreLoader.REQUIRES_OIDC_WORKER)
        self.assertTrue(DatabricksMetastoreLoader.REQUIRES_OIDC_WORKER)
