"""
EG-specific AWS Glue Data Catalog metastore loader.

Extends GlueDataCatalogLoader with Expedia Group-specific enrichment features:
- Governance tags (eg-owner, eg-creator, eg-brand, etc.)
- File format detection and warnings
- Table format detection (Iceberg, Delta Lake, Hudi)
- Sensitivity tags and data elements (column-level classification)
- Source data lake determination (catalog-aware)
- Top tier/trending table support
- AI-generated table descriptions
- Cloverleaf tagging
"""
import re
from typing import Dict, List, Tuple

from lib.logger import get_logger
from const.metastore import (
    DataColumn,
    DataSchema,
    DataTable,
)
from lib.metastore.loaders.glue_data_catalog_loader import GlueDataCatalogLoader
from metastore_plugin.eg_shared.enrichment_mixin import EgEnrichmentMixin

LOG = get_logger(__name__)


class EgGlueMetastoreLoader(EgEnrichmentMixin, GlueDataCatalogLoader):
    """
    EG-specific AWS Glue Data Catalog loader with metadata enrichment.

    This loader combines the base Glue Data Catalog functionality with
    Expedia Group-specific metadata enrichment features. It supports 3-level
    naming (catalog.schema.table) and provides comprehensive table metadata
    including governance tags, sensitivity classifications, and data lineage.

    Features:
    - Governance tags from table parameters (eg-owner, eg-creator, etc.)
    - File format detection (Parquet, ORC, Avro, CSV, JSON, etc.)
    - Table format detection (Iceberg, Delta Lake, Hudi)
    - Sensitivity tags with data element mapping
    - Catalog-aware source data lake determination
    - Top tier/trending table identification
    - AI-generated table descriptions
    - Cloverleaf managed table tagging
    """

    # Drives the "Catalog Type" tag/icon; see EgEnrichmentMixin.CATALOG_TYPE.
    CATALOG_TYPE = "glue"

    def __init__(self, *args, **kwargs):
        """
        Initialize the EG Glue metastore loader.

        Ensures the enrichment mixin's __init__ is called to set up
        the parsed description cache.
        """
        super().__init__(*args, **kwargs)

    def normalize_description_key(self, key: str) -> str:
        """
        Normalize Glue's CamelCase keys to snake_case format.

        Glue uses capital-letter keys that need normalization:
        - TableType → table_type
        - ViewOriginalText → view_original_text
        - StorageDescriptor → storage_descriptor

        Recursive dict traversal is handled by the parent mixin's
        _normalize_key_value() method.

        Args:
            key: Original CamelCase key

        Returns:
            snake_case key name
        """
        return self._camel_to_snake(key)

    def _camel_to_snake(self, name: str) -> str:
        """
        Convert CamelCase to snake_case.

        Examples:
            TableType → table_type
            ViewOriginalText → view_original_text
            StorageDescriptor → storage_descriptor
            SerializationLibrary → serialization_library

        Args:
            name: CamelCase string

        Returns:
            snake_case string
        """
        # Insert underscore before uppercase letters, then lowercase
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def _extract_parameters(self, table) -> Dict[str, str]:
        """
        Extract table parameters from Glue table format.

        Glue stores parameters in "Parameters" (capital P) key, which is
        normalized to "parameters" (lowercase) by normalize_description_key().

        Args:
            table: DataTable object with raw_description containing Glue table dict

        Returns:
            Dictionary of table parameters
        """
        description = self._parse_raw_description(table)
        if not description or not isinstance(description, dict):
            return {}

        params = {}

        # Glue format: "parameters" key (normalized from "Parameters")
        if "parameters" in description:
            params = dict(description["parameters"])

        # Add table_type from root level (only if not already present in parameters)
        # Root table_type is already normalized to lowercase by _parse_raw_description()
        # Parameters table_type takes precedence (e.g., "ICEBERG") over root table_type (e.g., "EXTERNAL_TABLE")
        if "table_type" in description and "table_type" not in params:
            params["table_type"] = description["table_type"]

        return params

    def get_all_schema_names(self) -> List[DataSchema]:
        """Stamp catalog_type='glue' on each catalog's properties so the frontend
        can render the AWS Glue icon on catalog nodes without a hardcoded name map."""
        schemas = super().get_all_schema_names()
        return [
            schema._replace(
                catalog=schema.catalog._replace(
                    properties={**(schema.catalog.properties or {}), "catalog_type": self.CATALOG_TYPE}
                )
            )
            if schema.catalog
            else schema
            for schema in schemas
        ]

    def get_table_and_columns(
        self, schema_name: str, table_name: str, catalog_name: str = None
    ) -> Tuple[DataTable, List[DataColumn]]:
        """
        Get table metadata with EG enrichment.

        This method extends the base Glue loader by adding EG-specific
        metadata enrichment features. It handles both 2-level and 3-level
        naming conventions.

        Args:
            schema_name: Database/schema name (e.g., "analytics", "default")
            table_name: Table name (e.g., "customer_data")
            catalog_name: Optional catalog name for 3-level naming
                         (AWS account ID or display name)

        Returns:
            Tuple of (DataTable, List[DataColumn]) with enriched metadata
            Returns (None, []) if table not found
        """
        LOG.debug(
            f"Getting table {schema_name}.{table_name} with catalog {catalog_name}")

        # Get base metadata from parent Glue loader
        table, columns = super().get_table_and_columns(schema_name, table_name)

        if not table:
            return None, []

        # Extract data_size_bytes from Glue table Parameters
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
        Extract data_size_bytes from Glue table Parameters.

        AWS Glue stores table size in Parameters.totalSize (as a string).
        The "Parameters" key is normalized to "parameters" by normalize_description_key().

        Args:
            table: DataTable object with raw_description

        Returns:
            Size in bytes as integer, or None if not available
        """
        description = self._parse_raw_description(table)
        if not description or not isinstance(description, dict):
            return None

        # Glue stores parameters in "parameters" key (normalized from "Parameters")
        # Note: nested keys like "totalSize" are also normalized to "total_size"
        parameters = description.get("parameters", {})
        if isinstance(parameters, dict):
            # Try both normalized and original key names for compatibility
            size_str = parameters.get("total_size") or parameters.get("totalSize")
            if size_str is not None:
                try:
                    return int(size_str)
                except (ValueError, TypeError):
                    LOG.debug(f"Could not parse totalSize from parameters: {size_str}")

        return None
