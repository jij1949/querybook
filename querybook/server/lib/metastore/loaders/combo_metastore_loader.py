from typing import Dict, List, Optional, Tuple
from const.metastore import (
    DataCatalog,
    DataColumn,
    DataSchema,
    DataTable,
    MetadataMode,
    MetadataType,
    MetastoreLoaderConfig,
)
from lib.form import ExpandableFormField, FormField, FormFieldType, StructFormField
from lib.metastore.base_metastore_loader import BaseMetastoreLoader
from lib.metastore import get_metastore_loader
from lib.logger import get_logger

LOG = get_logger(__name__)


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
