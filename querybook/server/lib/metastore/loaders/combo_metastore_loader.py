from typing import Dict, List, Optional, Set, Tuple
from const.metastore import (
    DataCatalog,
    DataColumn,
    DataSchema,
    DataTable,
    MetadataMode,
    MetadataType,
    MetastoreLoaderConfig,
)
from app.db import DBSession, with_session
from lib.form import ExpandableFormField, FormField, FormFieldType, StructFormField
from lib.metastore.base_metastore_loader import BaseMetastoreLoader
from lib.metastore import get_metastore_loader
from lib.logger import get_logger
from logic.elasticsearch import delete_es_table_by_id
from logic.metastore import (
    delete_catalog,
    delete_schema,
    delete_table,
    get_all_catalogs,
    get_catalog_by_id,
    iterate_data_schema,
)

LOG = get_logger(__name__)


class ComboChildDegradedError(RuntimeError):
    """Raised by ``load_child`` when upserts ran but the prune was skipped for a
    reason that requires investigation: **empty discovery** (0 schemas returned —
    possible permission failure) or **runtime catalog overlap** (a discovered catalog
    is claimed by another child).

    Silent prune skips — catalog-less mode and no-catalog-config — do *not* raise
    this error; they are expected operational states and the run continues normally.
    """

    pass


class ComboMetastoreLoader(BaseMetastoreLoader):
    """
    Aggregates multiple metastore loaders under a single logical metastore.

    This loader must be configured with multiple sub-loaders, each pointing to a different metastore.
    It then implements the BaseMetastoreLoader interface by delegating calls to the appropriate sub-loader(s).

    This doesn't require catalog support, but if catalogs are enabled, they must not be overlapping across sub-loaders or the behavior is undefined.
    Schemas cannot conflict across sub-loaders unless catalogs are used to disambiguate.

    Catalog mappings for sub-loaders are only for optimization and are not strictly required.
    The loader will dynamically discover and map schemas to sub-loaders on demand, but this is not persistent.

    Configuration format:
    {
      "sub_loaders": [
        {"metastore_id": 2, "catalogs": ["main", "analytics"]},  # explicit mapping
        {"metastore_id": 3}  # dynamic discovery
      ]
    }
    """

    # Enable external metadata loading (tags, owners, data elements) from sub-loaders
    # This allows the combo loader to save enriched metadata returned by sub-loaders
    loader_config: MetastoreLoaderConfig = MetastoreLoaderConfig(
        {
            MetadataType.TAG: MetadataMode.WRITE_BACK,
            MetadataType.DATA_ELEMENT: MetadataMode.WRITE_BACK,
            MetadataType.OWNER: MetadataMode.WRITE_BACK,
        }
    )

    def __init__(self, metastore_dict: Dict):
        super().__init__(metastore_dict)

        # Parse configuration from UI-friendly format
        sub_loaders_raw = metastore_dict.get("metastore_params", {}).get(
            "sub_loaders", []
        )

        # Convert from UI format (list of dicts with comma-separated catalogs string)
        # to internal format (list of dicts with catalogs as list)
        self.sub_loader_configs = []
        for config in sub_loaders_raw:
            metastore_id = config.get("metastore_id")
            if not metastore_id:
                continue

            # Parse comma-separated catalogs string into list
            catalogs_str = config.get("catalogs", "")
            if catalogs_str and isinstance(catalogs_str, str):
                # Split by comma and strip whitespace
                catalogs = [c.strip() for c in catalogs_str.split(",") if c.strip()]
            else:
                catalogs = []

            loader_config = {"metastore_id": metastore_id}
            if catalogs:
                loader_config["catalogs"] = catalogs

            self.sub_loader_configs.append(loader_config)

        # Validate configuration
        self._validate_config()

        # Build optional catalog routing map: catalog_name → metastore_id
        # Only populated for explicitly mapped catalogs
        self._catalog_to_metastore_id: Dict[str, int] = {}

        # Track all metastore IDs for unmapped catalog fallback
        self._all_metastore_ids: List[int] = []

        # Lazy-loaded loader instances
        self._loader_cache: Dict[int, BaseMetastoreLoader] = {}

        # Schema routing cache: (catalog_name, schema_name) → metastore_id
        # Populated during get_all_schema_names() for direct routing in subsequent calls
        self._schema_to_metastore_id: Dict[Tuple[Optional[str], str], int] = {}

        # Scoped prune context: set by _load_scoped before calling base prune methods.
        # None = full prune (delegates to base); set() = skip prune entirely;
        # non-empty Set[str] = owned catalog names — only schemas/catalogs within
        # these catalogs are eligible for deletion.
        self._current_prune_scope: Optional[Set[str]] = None

        for config in self.sub_loader_configs:
            metastore_id = config["metastore_id"]
            self._all_metastore_ids.append(metastore_id)

            # Build catalog → metastore_id lookup for explicitly mapped catalogs
            if "catalogs" in config and config["catalogs"]:
                for catalog_name in config["catalogs"]:
                    self._catalog_to_metastore_id[catalog_name] = metastore_id

        mapped_count = len(self._catalog_to_metastore_id)
        total_loaders = len(self.sub_loader_configs)
        LOG.debug(
            f"ComboMetastoreLoader initialized: {mapped_count} mapped catalogs, {total_loaders} sub-loaders"
        )

    def _validate_config(self):
        """Validate sub_loaders configuration"""
        if not self.sub_loader_configs:
            raise ValueError("ComboMetastoreLoader requires at least one sub_loader")

        if not isinstance(self.sub_loader_configs, list):
            raise ValueError("sub_loaders must be a list")

        # Validate each config and check for duplicate catalog names
        seen_catalogs = set()
        seen_metastore_ids = set()

        for config in self.sub_loader_configs:
            # Validate required fields
            if "metastore_id" not in config:
                raise ValueError("Each sub_loader must have 'metastore_id'")

            metastore_id = config["metastore_id"]

            # Validate types
            if not isinstance(metastore_id, int):
                raise ValueError(
                    f"metastore_id must be an integer, got {type(metastore_id)}"
                )

            # Check for duplicate metastore_ids
            if metastore_id in seen_metastore_ids:
                raise ValueError(f"Duplicate metastore_id: {metastore_id}")
            seen_metastore_ids.add(metastore_id)

            # Validate catalogs if provided (optional field)
            if "catalogs" in config:
                catalogs = config["catalogs"]
                if not isinstance(catalogs, list):
                    raise ValueError(f"catalogs must be a list, got {type(catalogs)}")

                # Check for duplicate catalog names across all sub-loaders
                for catalog_name in catalogs:
                    if catalog_name in seen_catalogs:
                        raise ValueError(f"Duplicate catalog name: {catalog_name}")
                    seen_catalogs.add(catalog_name)

    def _get_loader_by_metastore_id(self, metastore_id: int) -> BaseMetastoreLoader:
        """Get loader instance for a metastore ID (lazy initialization)"""
        if metastore_id not in self._loader_cache:
            loader = get_metastore_loader(metastore_id)
            self._loader_cache[metastore_id] = loader
            LOG.debug(f"Lazy-loaded sub-loader for metastore_id={metastore_id}")
        return self._loader_cache[metastore_id]

    def _get_loader_for_catalog(self, catalog_name: str) -> Optional[int]:
        """
        Get metastore_id for a catalog name using hybrid routing:
        1. If catalog is mapped → return specific metastore_id (fast O(1) lookup)
        2. If catalog is unmapped → return None (caller will try all loaders)
        """
        return self._catalog_to_metastore_id.get(catalog_name)

    def _resolve_metastore_id(
        self, schema_name: str, catalog_name: Optional[str] = None
    ) -> int:
        """
        Resolve which sub-loader owns a schema using three routing layers:
        1. Schema cache (populated during get_all_schema_names)
        2. Catalog mapping (from config)
        3. Slow path fallback (try all sub-loaders)
        """
        # 1. Schema cache: most reliable, populated during schema discovery
        cached = self._schema_to_metastore_id.get((catalog_name, schema_name))
        if cached is not None:
            return cached

        # 2. Catalog mapping: from explicit config
        if catalog_name:
            mapped = self._get_loader_for_catalog(catalog_name)
            if mapped is not None:
                return mapped

        # 3. Slow path: try all sub-loaders (should rarely be needed)
        LOG.debug(
            f"Schema '{schema_name}' (catalog={catalog_name}) not in cache, trying all sub-loaders"
        )
        for metastore_id in self._all_metastore_ids:
            loader = self._get_loader_by_metastore_id(metastore_id)
            try:
                if loader._method_accepts_param(
                    "get_all_table_names_in_schema", "catalog_name"
                ):
                    loader.get_all_table_names_in_schema(schema_name, catalog_name)
                else:
                    loader.get_all_table_names_in_schema(schema_name)
                # Success — cache it for future calls
                self._schema_to_metastore_id[(catalog_name, schema_name)] = metastore_id
                LOG.info(
                    f"Discovered schema '{schema_name}' in metastore_id={metastore_id}"
                )
                return metastore_id
            except Exception:
                continue

        catalog_msg = f" (catalog={catalog_name})" if catalog_name else ""
        raise ValueError(
            f"Schema '{schema_name}'{catalog_msg} not found in any sub-loader"
        )

    def get_all_schema_names(self) -> List[DataSchema]:
        """
        Aggregate schemas from all sub-loaders.
        Each sub-loader applies its own ACL filtering before returning results.
        ComboLoader's ACL (if configured) provides an additional filtering layer.
        """
        result = []

        for metastore_id in self._all_metastore_ids:
            try:
                loader = self._get_loader_by_metastore_id(metastore_id)
                # Get ACL-filtered schemas from sub-loader
                schemas = loader._get_all_filtered_schemas()

                # _get_all_filtered_schemas() already returns DataSchema objects
                for schema in schemas:
                    result.append(schema)
                    # Cache schema → metastore_id for direct routing in subsequent calls
                    cache_key = (
                        schema.catalog.name if schema.catalog else None,
                        schema.name,
                    )
                    self._schema_to_metastore_id[cache_key] = metastore_id

                LOG.info(
                    f"Loaded {len(schemas)} schemas from sub-loader metastore_id={metastore_id}"
                )

            except Exception as e:
                LOG.error(
                    f"Error loading schemas from metastore_id={metastore_id}: {e}"
                )
                # Continue with other sub-loaders (partial success)

        LOG.info(
            f"ComboLoader aggregated {len(result)} total schemas from {len(self._all_metastore_ids)} sub-loaders"
        )

        return result

    def get_all_table_names_in_schema(
        self, schema_name: str, catalog_name: Optional[str] = None
    ) -> List[str]:
        """
        Get table names using hybrid routing.
        Delegates to sub-loader's _get_all_filtered_table_names() so each
        sub-loader applies its own ACL filtering. ComboLoader's ACL is then
        applied by the inherited base _get_all_filtered_table_names().
        """
        schema = DataSchema(
            name=schema_name,
            catalog=DataCatalog(name=catalog_name) if catalog_name else None,
        )

        metastore_id = self._resolve_metastore_id(schema_name, catalog_name)
        loader = self._get_loader_by_metastore_id(metastore_id)
        return loader._get_all_filtered_table_names(schema)

    def get_table_and_columns(
        self, schema_name: str, table_name: str, catalog_name: Optional[str] = None
    ) -> Tuple[DataTable, List[DataColumn]]:
        """Get table metadata using hybrid routing"""
        metastore_id = self._resolve_metastore_id(schema_name, catalog_name)
        loader = self._get_loader_by_metastore_id(metastore_id)

        if loader._method_accepts_param("get_table_and_columns", "catalog_name"):
            return loader.get_table_and_columns(
                schema_name, table_name, catalog_name=catalog_name
            )
        return loader.get_table_and_columns(schema_name, table_name)

    # ------------------------------------------------------------------ #
    #  Stage 1: data-loss fix (EGANP-6149)                               #
    # ------------------------------------------------------------------ #

    def _get_child_owned_catalog_names(self, child_id: int) -> Set[str]:
        """Return catalog names explicitly configured for *child_id* in the combo config."""
        return {
            cat_name
            for cat_name, owner_id in self._catalog_to_metastore_id.items()
            if owner_id == child_id
        }

    def _check_catalog_ownership_overlap(
        self, child_id: int, discovered_schemas: List["DataSchema"]
    ) -> bool:
        """Return True if any of *discovered_schemas* belongs to a catalog that is
        configured for a **different** child in ``_catalog_to_metastore_id``.

        This is the runtime complement to the config-time ``_validate_config`` check.
        When True the caller must skip the prune to prevent cross-child data loss.
        """
        for schema in discovered_schemas:
            cat_name = schema.catalog.name if schema.catalog else None
            if cat_name is None:
                continue
            owner = self._catalog_to_metastore_id.get(cat_name)
            if owner is not None and owner != child_id:
                LOG.error(
                    f"[combo_child_sync] child_id={child_id}: catalog '{cat_name}' is "
                    f"configured for child_id={owner}. Refusing prune."
                )
                return True
        return False

    def _load_scoped(self, schemas, owned_catalog_names=None):
        """Override: stash the prune scope so our delete overrides can read it.

        ``owned_catalog_names`` is a ``Set[str]`` of catalog names this child owns:
        * ``None``     — full prune (delegate to base; used for non-combo paths).
        * ``set()``    — skip prune entirely (catalog-less / empty-detection / overlap).
        * non-empty    — scoped prune: only schemas/catalogs in these catalogs are eligible.
        """
        self._current_prune_scope = owned_catalog_names
        try:
            super()._load_scoped(schemas)
        finally:
            self._current_prune_scope = None

    @with_session
    def delete_schema_not_in_metastore(self, metastore_id, schemas, session=None):
        """Scoped prune: only delete rows within ``_current_prune_scope``.

        * ``None``      — delegate to base (full prune).
        * ``set()``     — skip prune entirely (catalog-less / empty-detection / overlap).
        * ``Set[str]``  — delete only schemas whose catalog is in the owned set AND
                          absent from the fresh discovery.  Siblings in other catalogs
                          are never visited.
        """
        owned_catalog_names = self._current_prune_scope

        if owned_catalog_names is None:
            return super().delete_schema_not_in_metastore(
                metastore_id, schemas, session=session
            )
        if not owned_catalog_names:
            return  # empty set → skip prune entirely

        expected_schemas = {
            (s.catalog.name if s.catalog else None, s.name) for s in schemas
        }
        for data_schema in iterate_data_schema(metastore_id, session=session):
            catalog_name = None
            if data_schema.catalog_id:
                db_catalog = get_catalog_by_id(data_schema.catalog_id, session=session)
                catalog_name = db_catalog.name if db_catalog else None

            # Scope guard: only touch schemas in catalogs this child owns.
            if catalog_name not in owned_catalog_names:
                continue  # sibling catalog — leave untouched

            schema_key = (catalog_name, data_schema.name)
            if schema_key not in expected_schemas:
                for table in data_schema.tables:
                    delete_table(table_id=table.id, commit=False, session=session)
                    delete_es_table_by_id(table.id)
                delete_schema(id=data_schema.id, commit=False, session=session)
                LOG.info(f"Deleted schema {data_schema.name} ({data_schema.id})")

        session.commit()

    @with_session
    def delete_catalog_not_in_metastore(self, metastore_id, schemas, session=None):
        """Scoped prune: only delete catalogs within ``_current_prune_scope``."""
        owned_catalog_names = self._current_prune_scope

        if owned_catalog_names is None:
            return super().delete_catalog_not_in_metastore(
                metastore_id, schemas, session=session
            )
        if not owned_catalog_names:
            return  # empty set → skip prune entirely

        expected_catalogs = {s.catalog.name for s in schemas if s.catalog is not None}
        for db_catalog in get_all_catalogs(metastore_id, session=session):
            if db_catalog.name not in owned_catalog_names:
                continue  # not our catalog
            if db_catalog.name not in expected_catalogs:
                delete_catalog(catalog_id=db_catalog.id, commit=False, session=session)
                LOG.info(
                    f"Deleted orphaned catalog {db_catalog.name} ({db_catalog.id})"
                )

        session.commit()

    def load_child(self, child_id: int) -> List["DataSchema"]:
        """Sync one child metastore. All writes land under ``self.metastore_id`` (combo id).

        Returns the ACL-filtered schemas that were upserted, so ``load()`` can
        accumulate the full combo-level discovery for a final cleanup pass.

        Safety guards (all contained within ComboLoader):
        * Catalog-less mode → skip prune (no per-row provenance).
        * No catalog config for this child → skip per-child prune; combo-level
          full prune is handled by ``load()`` after all children succeed.
        * Runtime catalog overlap → skip prune (another child owns that catalog).
        * Empty discovery → skip prune and raise FAILURE (likely permission failure).
        * Normal → scoped prune via ``_current_prune_scope`` overrides.
        """
        loader = self._get_loader_by_metastore_id(child_id)

        # Fetch raw schemas from child.
        raw_schemas = loader.get_all_schema_names()

        # Apply child's ACL first so allowlists configured on the child metastore
        # are honoured, then apply combo's catalog settings + ACL on top.
        child_acl_schemas = [
            s
            for s in (
                DataSchema(name=s, catalog=None) if isinstance(s, str) else s
                for s in raw_schemas
            )
            if loader.acl_checker.is_schema_valid(
                f"{s.catalog.name}.{s.name}" if s.catalog else s.name
            )
        ]
        combo_schemas = self._filter_schemas(child_acl_schemas)

        # Update schema routing cache for subsequent table-name lookups.
        for schema in combo_schemas:
            cache_key = (schema.catalog.name if schema.catalog else None, schema.name)
            self._schema_to_metastore_id[cache_key] = child_id

        LOG.info(
            f"[combo_child_sync] child_id={child_id} "
            f"raw_schemas={len(raw_schemas)} combo_schemas={len(combo_schemas)}"
        )

        owned_catalog_names = self._get_child_owned_catalog_names(child_id)
        # prune_scope: None = full prune, set() = skip, Set[str] = scoped to these catalogs.
        prune_scope: Optional[Set[str]] = set()  # default: skip prune
        prune_status = "applied"
        prune_skipped_reason: Optional[str] = None

        if len(combo_schemas) == 0:
            # Empty discovery: could be a permission failure or a genuine empty metastore.
            # Skip prune and raise so the run is marked FAILURE — forces investigation.
            prune_status = "skipped-empty"
            prune_skipped_reason = (
                "child returned 0 schemas — possible permission or discovery failure"
            )

        elif not self.enable_catalog_support:
            # Catalog-less mode: all schemas share catalog=None, can't scope per child.
            prune_status = "skipped-catalogless"

        elif not owned_catalog_names:
            # No catalog config for this child — can't scope safely without ownership boundary.
            prune_status = "skipped-no-catalog-config"

        elif self._check_catalog_ownership_overlap(child_id, combo_schemas):
            # A discovered catalog is claimed by another child at runtime.
            prune_status = "skipped-overlap"
            prune_skipped_reason = "catalog ownership overlap detected at runtime"

        else:
            # Scoped prune: pass owned catalog names as the ownership boundary.
            # The delete overrides use catalog name membership (not fresh-discovery tuples)
            # to determine which DB rows are eligible for deletion — stale schemas within
            # owned catalogs will be correctly removed.
            prune_scope = owned_catalog_names

            # Warn if this child discovered schemas in catalogs it doesn't own.
            # Those schemas will be upserted now and deleted by _delete_unclaimed_schemas
            # on the same run (write-then-delete churn).  This usually means the child's
            # ACL allowlist is broader than its configured catalog ownership — tighten one
            # or the other to eliminate the churn.
            unowned = {
                s.catalog.name if s.catalog else None
                for s in combo_schemas
                if (s.catalog.name if s.catalog else None) not in owned_catalog_names
            }
            if unowned:
                LOG.warning(
                    f"[combo_child_sync] child_id={child_id} discovered schemas in "
                    f"catalogs not configured as owned: {unowned}. These will be "
                    f"upserted then removed by cleanup (write-then-delete churn). "
                    f"Consider tightening the child's ACL or catalog ownership config."
                )

        # Upsert under combo's metastore_id; prune scoped to owned catalogs only.
        self._load_scoped(combo_schemas, owned_catalog_names=prune_scope)

        LOG.info(
            f"[combo_child_sync] child_id={child_id} "
            f"schemas_found={len(combo_schemas)} "
            f"prune_status={prune_status} "
            f"result={'degraded' if prune_skipped_reason else 'success'}"
        )

        if prune_skipped_reason:
            raise ComboChildDegradedError(
                f"child_id={child_id} prune skipped: {prune_skipped_reason}"
            )

        return combo_schemas

    def load(self) -> None:
        """Sequential per-child sync with honest combo-level status.

        **Orchestration note:** there are two paths that drive combo syncs:

        1. **This method** — the synchronous direct-call path.  Used when
           ``update_metastore`` detects ``len(get_sync_units()) == 1`` (single-unit
           combo or any non-combo loader), and in tests/scripts that call the loader
           directly.  Runs all children in-process, sequentially, and performs cleanup
           before returning.

        2. **Stage 2 Celery chain** — the async fan-out path.  Used by
           ``update_metastore`` for multi-unit combos (``len(units) > 1``).  Dispatches
           one ``update_metastore_child`` task per unit, followed by
           ``finalize_combo_metastore``.  Cleanup is driven by
           ``run_finalize_sync → _run_cleanup_after_sync``.

        Both paths must stay consistent in their safety semantics.  Changes to
        ``load_child`` or the cleanup methods affect both.

        Each child runs independently so a failure in one does not abort siblings.
        After all children succeed, runs a cleanup pass to remove stale data:
        * With explicit catalog ownership → scoped cleanup via ``_delete_unclaimed_schemas``
        * Without catalog ownership → combo-level full prune using the union of all
          children's ACL-filtered schemas (restores pre-Stage-1 cleanup behaviour).
        Raises ``RuntimeError`` if any child raises an exception or a
        ``ComboChildDegradedError`` (empty discovery or runtime catalog overlap).
        Silent prune skips (catalog-less mode, no-catalog-config) do not raise.
        """
        child_errors: Dict[int, Exception] = {}
        all_discovered_schemas: List["DataSchema"] = []

        for child_id in self._all_metastore_ids:
            try:
                child_schemas = self.load_child(child_id)
                all_discovered_schemas.extend(child_schemas)
            except ComboChildDegradedError as e:
                LOG.error(f"[combo_load] child_id={child_id} degraded: {e}")
                child_errors[child_id] = e
            except Exception as e:
                LOG.error(
                    f"[combo_load] child_id={child_id} failed: {e}", exc_info=True
                )
                child_errors[child_id] = e

        if not child_errors:
            # Only use catalog-scoped cleanup when EVERY child has explicit ownership.
            # If any child is unmapped, _delete_unclaimed_schemas would treat its
            # catalogs as unclaimed and delete them — fall back to full prune instead.
            children_with_catalogs = set(self._catalog_to_metastore_id.values())
            if children_with_catalogs == set(self._all_metastore_ids):
                self._delete_unclaimed_schemas()
            else:
                self._combo_full_prune(all_discovered_schemas)

        if child_errors:
            failed_ids = ", ".join(str(cid) for cid in child_errors)
            raise RuntimeError(
                f"ComboLoader sync degraded: child metastore_id(s) [{failed_ids}] "
                f"failed or had prune skipped. Schemas have been preserved. "
                f"Check [combo_child_sync] log lines for per-child details."
            )

    def get_sync_units(self) -> List[int]:
        return list(self._all_metastore_ids)

    def load_unit(self, unit_id: int) -> None:
        self.load_child(unit_id)

    # ------------------------------------------------------------------ #
    #  Stage 2: Celery task helpers (thin-wrapper targets)                #
    # ------------------------------------------------------------------ #

    _CHILD_LOCK_TTL = 7200  # 2 hours — exceeds any expected child runtime

    # NOTE (Redlock safety): the lock value is a static "1" and the finally block
    # deletes it unconditionally.  If a sync exceeds _CHILD_LOCK_TTL, the TTL
    # expires, another run acquires a new lock, and the original run's finally
    # deletes the new lock — leaving the next run unguarded.  A fully safe
    # implementation would store a unique token as the lock value and use a
    # compare-and-delete Lua script for release.  The 2 h TTL makes this
    # scenario low-probability in practice, so left as a known limitation.

    def run_child_sync(
        self,
        celery_task,
        child_id: int,
        parent_record_id: Optional[int] = None,
    ) -> None:
        """Run one child sync from a Celery task.  Handles the TaskRunRecord lifecycle
        and a Redis SETNX lock to prevent overlapping runs for the same child.

        ``parent_record_id`` is the combo-level TaskRunRecord created by the dispatcher.
        When provided, a Redis key ``combo_child_record:{combo_id}:{child_id}:{parent_record_id}``
        is written so that ``run_finalize_sync`` can look up *this run's* child record by ID
        rather than by name — avoiding a race where a concurrent dispatch's newer record (with
        the same name) is mistaken for this run's result.

        Exceptions from ``load_unit`` are caught and recorded as FAILURE without
        re-raising so the Celery chain continues to remaining children.
        """
        from clients.redis_client import get_redis
        from const.schedule import TaskRunStatus
        from logic.schedule import (
            create_task_run_record_for_celery_task,
            update_task_run_record,
        )

        record_id = create_task_run_record_for_celery_task(celery_task)
        lock_key = f"combo_child_sync_lock:{self.metastore_id}:{child_id}"
        redis_conn = get_redis()

        # Store a correlation key so finalize can retrieve this exact record by ID,
        # avoiding the latest-by-name race condition under concurrent dispatches.
        if parent_record_id is not None:
            redis_conn.set(
                f"combo_child_record:{self.metastore_id}:{child_id}:{parent_record_id}",
                str(record_id),
                ex=self._CHILD_LOCK_TTL,
            )

        acquired = redis_conn.set(lock_key, "1", nx=True, ex=self._CHILD_LOCK_TTL)

        if not acquired:
            LOG.warning(
                f"[combo_child_sync] combo_id={self.metastore_id} child_id={child_id}: "
                "lock already held — skipping (another run is still in progress)"
            )
            update_task_run_record(
                id=record_id,
                error_message=(
                    f"skipped: lock already held for combo_id={self.metastore_id} "
                    f"child_id={child_id} — another run is still in progress"
                ),
                status=TaskRunStatus.FAILURE,
            )
            return

        try:
            self.load_unit(child_id)
            update_task_run_record(id=record_id, status=TaskRunStatus.SUCCESS)
        except Exception as e:
            LOG.error(
                f"[combo_child_sync] combo_id={self.metastore_id} child_id={child_id} "
                f"failed: {e}",
                exc_info=True,
            )
            update_task_run_record(
                id=record_id, error_message=str(e), status=TaskRunStatus.FAILURE
            )
            # Do NOT re-raise — chain must continue to remaining children.
        finally:
            redis_conn.delete(lock_key)

    def run_finalize_sync(
        self, unit_ids: List[int], record_id: Optional[int] = None
    ) -> None:
        """Terminal callback for the combo Celery chain.  Checks each child's
        TaskRunRecord and updates the combo record (created by the dispatcher)
        to SUCCESS or FAILURE.  On success, runs the combo-level cleanup.

        Child records are looked up via a Redis correlation key written by
        ``run_child_sync``, ensuring we read *this run's* records even when a
        concurrent dispatch's child wrote a newer record with the same name.
        Falls back to name-based lookup if the key is absent (first run or TTL
        expired).
        """
        from clients.redis_client import get_redis
        from const.schedule import TaskRunStatus
        from logic.schedule import (
            get_task_run_record,
            get_task_run_record_run_by_name,
            update_task_run_record,
        )

        redis_conn = get_redis()
        failed = []
        for child_id in unit_ids:
            child_record = None

            # Prefer per-run correlation key to avoid reading a concurrent run's record.
            redis_key = f"combo_child_record:{self.metastore_id}:{child_id}:{record_id}"
            raw = redis_conn.get(redis_key)
            if raw:
                child_record = get_task_run_record(int(raw))

            if child_record is None:
                child_shadow = f"update_metastore_{self.metastore_id}_child_{child_id}"
                records, _ = get_task_run_record_run_by_name(child_shadow, limit=1)
                child_record = records[0] if records else None

            if child_record is None:
                failed.append(f"child_id={child_id}: no run record found")
            elif child_record.status != TaskRunStatus.SUCCESS:
                failed.append(
                    f"child_id={child_id} status={child_record.status.name} "
                    f"error={child_record.error_message}"
                )

        if failed:
            error_msg = f"combo_id={self.metastore_id} — " + "; ".join(failed)
            if record_id is not None:
                update_task_run_record(
                    id=record_id, error_message=error_msg, status=TaskRunStatus.FAILURE
                )
            raise RuntimeError(error_msg)

        self._run_cleanup_after_sync()
        LOG.info(
            f"[finalize_combo] combo_id={self.metastore_id} SUCCESS: "
            f"all {len(unit_ids)} children passed"
        )
        if record_id is not None:
            update_task_run_record(id=record_id, status=TaskRunStatus.SUCCESS)

    def _run_cleanup_after_sync(self) -> None:
        """Run the appropriate combo-level cleanup after all children succeed.

        * Catalog-ownership configured → ``_delete_unclaimed_schemas`` (no re-discovery needed;
          it operates on DB state directly).
        * No catalog ownership → ``_combo_full_prune`` with re-discovered union; an empty result
          from any child is treated as a potential transient failure and aborts the prune to
          prevent data loss.
        """
        children_with_catalogs = set(self._catalog_to_metastore_id.values())
        if children_with_catalogs == set(self._all_metastore_ids):
            # Every child has explicit catalog ownership — safe to use scoped cleanup.
            # Re-discovery not needed: _delete_unclaimed_schemas works from the DB catalog list.
            self._delete_unclaimed_schemas()
            return

        # Catalog-less: re-discover from all children and prune against the union.
        all_schemas: List["DataSchema"] = []
        for child_id in self._all_metastore_ids:
            loader = self._get_loader_by_metastore_id(child_id)
            raw_schemas = loader.get_all_schema_names()
            child_acl_schemas = [
                s
                for s in (
                    DataSchema(name=s, catalog=None) if isinstance(s, str) else s
                    for s in raw_schemas
                )
                if loader.acl_checker.is_schema_valid(
                    f"{s.catalog.name}.{s.name}" if s.catalog else s.name
                )
            ]
            child_combo_schemas = self._filter_schemas(child_acl_schemas)
            if not child_combo_schemas:
                # Treat empty re-discovery as a potential transient failure — skip the full
                # prune rather than risk deleting live schemas with an incomplete expected set.
                LOG.error(
                    f"[combo_cleanup] child_id={child_id} returned 0 schemas during "
                    f"re-discovery — skipping full prune to prevent data loss"
                )
                return
            all_schemas.extend(child_combo_schemas)

        self._combo_full_prune(all_schemas)

    def _combo_full_prune(self, all_discovered_schemas: List["DataSchema"]) -> None:
        """Combo-level full prune: delete any schema/catalog under the combo metastore
        that is absent from the union of all children's ACL-filtered discoveries.

        Used when no explicit catalog ownership is configured in the combo's sub_loaders.
        Restores the pre-Stage-1 cleanup behaviour while keeping child ACL filtering.
        Setting ``_current_prune_scope = None`` causes our delete overrides to delegate
        to the base class full-prune implementation.
        """
        LOG.info(
            f"[combo_cleanup] running combo-level full prune "
            f"(no catalog ownership configured); "
            f"expected_schemas={len(all_discovered_schemas)}"
        )
        self._current_prune_scope = None
        try:
            self.delete_schema_not_in_metastore(
                self.metastore_id, all_discovered_schemas
            )
            self.delete_catalog_not_in_metastore(
                self.metastore_id, all_discovered_schemas
            )
        finally:
            self._current_prune_scope = None

    def _delete_unclaimed_schemas(self) -> None:
        """Remove catalogs and schemas under the combo metastore that are not
        claimed by any child's configured catalog ownership.

        This restores the cleanup behaviour that the pre-Stage-1 full prune
        provided: stale catalogs written by old syncs (e.g. before an ACL was
        applied) are removed once all children have synced cleanly.

        Only runs when catalog support is enabled and at least one child has
        explicit catalog ownership configured — without that we have no reliable
        ownership boundary and cannot safely delete anything.
        """
        all_owned_catalogs: Set[str] = set(self._catalog_to_metastore_id.keys())

        if not self.enable_catalog_support or not all_owned_catalogs:
            LOG.debug("[combo_cleanup] skipped — no catalog ownership configured")
            return

        with DBSession() as session:
            # Pre-group schemas by catalog_id in one pass (O(N_schemas)) so the
            # per-catalog delete loop below is O(N_catalogs) rather than O(N×M).
            schemas_by_catalog_id: Dict[int, list] = {}
            for data_schema in iterate_data_schema(self.metastore_id, session=session):
                schemas_by_catalog_id.setdefault(data_schema.catalog_id, []).append(
                    data_schema
                )

            catalogs_deleted = 0
            for db_catalog in get_all_catalogs(self.metastore_id, session=session):
                if db_catalog.name in all_owned_catalogs:
                    continue  # claimed by a child — leave it alone

                # Orphaned catalog: delete all its schemas/tables then the catalog row.
                LOG.info(
                    f"[combo_cleanup] removing unclaimed catalog '{db_catalog.name}' "
                    f"(not owned by any configured child)"
                )
                for data_schema in schemas_by_catalog_id.get(db_catalog.id, []):
                    for table in data_schema.tables:
                        delete_table(table_id=table.id, commit=False, session=session)
                        delete_es_table_by_id(table.id)
                    delete_schema(id=data_schema.id, commit=False, session=session)

                delete_catalog(catalog_id=db_catalog.id, commit=False, session=session)
                catalogs_deleted += 1

            session.commit()

        LOG.info(
            f"[combo_cleanup] removed {catalogs_deleted} unclaimed catalog(s) "
            f"from metastore_id={self.metastore_id}"
        )

    @classmethod
    def get_sandbox_catalog_names(cls, metastore_dict: Dict) -> List[str]:
        """Aggregate sandbox catalog names from all child metastores."""
        from logic import admin as admin_logic

        names: Set[str] = set()
        params = metastore_dict.get("metastore_params") or {}
        for sub in params.get("sub_loaders", []):
            child_id = sub.get("metastore_id")
            if child_id:
                child = admin_logic.get_query_metastore_by_id(child_id)
                if child:
                    child_dict = child.to_dict_admin()
                    from lib.metastore import get_metastore_loader_class_by_name

                    child_cls = get_metastore_loader_class_by_name(child_dict["loader"])
                    names.update(child_cls.get_sandbox_catalog_names(child_dict))
        return list(names)

    @classmethod
    def get_metastore_params_template(cls):
        """Define the configuration form for ComboMetastoreLoader"""
        return StructFormField(
            (
                "sub_loaders",
                ExpandableFormField(
                    of=StructFormField(
                        (
                            "metastore_id",
                            FormField(
                                required=True,
                                description="Metastore ID",
                                field_type=FormFieldType.Number,
                                helper="The ID of an existing metastore to include in this combo loader",
                            ),
                        ),
                        (
                            "catalogs",
                            FormField(
                                required=False,
                                description="Catalog names (comma-separated)",
                                field_type=FormFieldType.String,
                                helper="Optional: Comma-separated list of catalogs for fast routing (e.g., 'hive,analytics'). Leave empty for dynamic discovery.",
                            ),
                        ),
                    ),
                    min=1,
                ),
            )
        )
