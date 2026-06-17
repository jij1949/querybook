"""
EG-specific Databricks Unity Catalog metastore loader.

Extends DatabricksMetastoreLoader with Expedia Group-specific enrichment features:
- Governance tags (eg-owner, eg-creator, eg-brand, etc.)
- File format detection and warnings
- Table format detection (Iceberg, Delta Lake, Hudi)
- Sensitivity tags and data elements (column-level classification)
- Source data lake determination (catalog-aware)
- Top tier/trending table support
- AI-generated table descriptions
- Cloverleaf tagging
"""
from typing import Dict, List, Optional, Tuple

from lib.logger import get_logger
from const.metastore import DataCatalog, DataColumn, DataTable
from lib.metastore.loaders.databricks_metastore_loader import DatabricksMetastoreLoader
from metastore_plugin.eg_shared.enrichment_mixin import EgEnrichmentMixin

LOG = get_logger(__name__)


class EgDatabricksMetastoreLoader(EgEnrichmentMixin, DatabricksMetastoreLoader):
    """
    EG-specific Databricks Unity Catalog loader with metadata enrichment.

    This loader combines the base Databricks Unity Catalog functionality with
    Expedia Group-specific metadata enrichment features. It supports 3-level
    naming (catalog.schema.table) and provides comprehensive table metadata
    including governance tags, sensitivity classifications, and data lineage.

    Features:
    - Governance tags from table properties (eg-owner, eg-creator, etc.)
    - File format detection (Parquet, ORC, Avro, CSV, JSON, etc.)
    - Table format detection (Iceberg, Delta Lake, Hudi)
    - Sensitivity tags with data element mapping
    - Catalog-aware source data lake determination
    - Top tier/trending table identification
    - AI-generated table descriptions
    - Cloverleaf managed table tagging
    """

    # Drives the "Catalog Type" tag/icon; see EgEnrichmentMixin.CATALOG_TYPE.
    CATALOG_TYPE = "databricks"

    def __init__(self, *args, **kwargs):
        """
        Initialize the EG Databricks metastore loader.

        Ensures the enrichment mixin's __init__ is called to set up
        the parsed description cache.
        """
        super().__init__(*args, **kwargs)

    def get_catalog_info(self, catalog_name: str) -> Optional[DataCatalog]:
        """Stamp catalog_type='databricks' on catalog properties so the frontend
        can render the Databricks icon on catalog nodes without a hardcoded name map."""
        catalog = super().get_catalog_info(catalog_name)
        if catalog is None:
            return None
        return catalog._replace(
            properties={**(catalog.properties or {}), "catalog_type": self.CATALOG_TYPE}
        )

    def get_table_and_columns(
        self, schema_name: str, table_name: str, catalog_name: str = None
    ) -> Tuple[DataTable, List[DataColumn]]:
        """
        Get table metadata with EG enrichment.

        This method extends the base Databricks loader by adding EG-specific
        metadata enrichment features. It handles both 2-level and 3-level
        naming conventions.

        Args:
            schema_name: Schema name in format "catalog.schema" or just "schema"
                        Examples: "prod.analytics", "main.default"
            table_name: Table name (e.g., "customer_data")

        Returns:
            Tuple of (DataTable, List[DataColumn]) with enriched metadata
            Returns (None, []) if table not found
        """
        LOG.debug(
            f"Getting table and columns for {catalog_name}.{schema_name}.{table_name}")

        # Get base metadata from parent Databricks loader
        table, columns = super().get_table_and_columns(
            schema_name, table_name, catalog_name=catalog_name)

        if not table:
            return None, []

        # Extract data_size_bytes from table properties
        # Databricks stores this in properties['spark.sql.statistics.totalSize']
        # but not all tables have this property, so we need a fallback
        data_size_bytes = self._extract_data_size_bytes(table)
        if data_size_bytes is not None:
            table = table._replace(data_size_bytes=data_size_bytes)

        # Apply EG enrichment features
        table, columns = self._enrich_table_and_columns(
            table=table,
            columns=columns,
            catalog_name=catalog_name,
            schema_name=schema_name,
            table_name=table_name,
            metastore_id=self.metastore_id,
        )

        return table, columns

    def _extract_data_size_bytes(self, table: DataTable) -> int:
        """
        Extract data_size_bytes from Databricks table properties.

        Databricks stores table size in properties['spark.sql.statistics.totalSize'],
        but not all tables have this property (e.g., views, external tables without
        statistics). Returns None if size information is not available.

        Args:
            table: DataTable object with raw_description

        Returns:
            Size in bytes as integer, or None if not available
        """
        description = self._parse_raw_description(table)
        if not description or not isinstance(description, dict):
            return None

        # Try to get from properties (most common location)
        properties = description.get("properties", {})
        if isinstance(properties, dict):
            size_str = properties.get("spark.sql.statistics.totalSize")
            if size_str is not None:
                try:
                    return int(size_str)
                except (ValueError, TypeError):
                    LOG.debug(f"Could not parse size from properties: {size_str}")

        return None
