"""
Data lake mapping utilities for catalog-aware metastores.

This module provides catalog-to-data-lake and schema-prefix-to-data-lake mappings
to support both 2-level (HMS) and 3-level (Databricks/Glue) naming conventions.

AWS Glue Configuration:
- Recommended: Set catalog_display_name in metastore config to match CATALOG_TO_DATA_LAKE keys
  (e.g., "data_test", "data_corp"). Display names are case-sensitive.
- Fallback: AWS account ID mappings provide robustness when display name not configured.
- Priority: determine_source_data_lake() checks display name first (line 112), then account ID.
"""
from typing import Optional, Tuple

from app.db import get_session
from env import QuerybookSettings
from lib.logger import get_logger
from logic.admin import get_query_metastore_by_id

LOG = get_logger(__file__)

# Catalog-to-data-lake mapping for 3-level naming systems
# This is used when the catalog name can directly determine the data lake
CATALOG_TO_DATA_LAKE = {
    # Databricks Unity Catalog examples
    # Test Databricks env
    "test_sandbox": "databricks_test_sandbox",
    "eg_internal_test": "databricks_eg_internal_test",
    "test_adhoc": "databricks_test_adhoc",
    # Prod Databricks env
    "sandbox": "databricks_sandbox",
    "adhoc": "databricks_adhoc",
    "analytics": "databricks_analytics",
    "eg_internal_prod": "databricks_eg_internal_prod",

    # AWS Glue Data Catalogs
    "data_corp": "egdataplatform_corp",
    "data_dw": "egdataplatform_dw",
    "data_test": "egdataplatform_test",
    "egdp_stage": "egdp_stage",
    "egdp_test": "egdp_test",
    "egdp_analytics": "egdp_analytics",
    "egdp_classic": "egdp_classic",
    "egdp_prod": "egdp_prod",
    # AWS account ID fallback mappings (used when catalog_display_name not configured)
    "177220994061": "egdataplatform_corp",  # Production AWS account
    "935051678728": "egdataplatform_test",   # Test AWS account
}

# Schema prefix to data lake mapping
# Reused from EG HMS loader - handles federated schemas with prefixes
SCHEMA_PREFIX_TO_DATA_LAKE = {
    "bexg_etl_prod_": "bexg_etl_prod",
    "bexg_etl_test_": "bexg_etl_test",
    "bexg_prod_": "bexg_prod",
    "bexg_test_": "bexg_test",
    "content_prod_": "content_prod",
    "controlplane_prod_": "controlplane_prod",
    "data_corp_": "egdataplatform_corp",
    "data_dw_": "egdataplatform_dw",
    "data_test_": "egdataplatform_test",
    "dspprod_": "dsp_prod",
    "egdp_classic_": "egdp_classic",
    "egdp_analytics_": "egdp_analytics",
    "egdp_dev_": "egdp_dev",
    "egdp_dwh_": "egdp_prod",  # Special case, duplicated prefix
    "egdp_prod_": "egdp_prod",
    "egdp_stage_": "egdp_stage",
    "egdp_test_": "egdp_test",
    "egp_prod_": "egp_prod",
    "eps_prod_": "eps_prod",
    "finance_prod_": "finance_prod",
    "gco_": "gco",
    "gmo_meta_prod_": "gmo_meta_prod",
    "hcom_data_analytics_uw2_": "hcom_data_analytics",
    "hcom_data_lab_uw2_": "hcom_data_lab",
    "hcom_data_prod_uw2_": "hcom_data_prod",
    "hotwire_prod_": "hotwire_prod",
    "marketplacehealth_prod_": "marketplacehealth_prod",
    "perf_": "perf",
    "qubole_meta_": "dsp_prod",
    "vrbo_prod_": "vrbo_prod",
    "vrbo_stage_": "vrbo_stage",
    "vrbo_test_": "vrbo_test",
}


def determine_source_data_lake(
    catalog_name: Optional[str],
    schema_name: str,
    location: Optional[str],
    metastore_id: int,
) -> Tuple[Optional[str], str]:
    """
    Determine the source data lake and schema name for a table.

    Priority order:
    1. Catalog-level mapping (if catalog_name is provided)
    2. Schema prefix mapping (for federated schemas)
    3. Location-based heuristics (parse S3 bucket name)
    4. Metastore-level mapping (based on metastore name)
    5. Fallback: catalog_name as data lake

    Args:
        catalog_name: Catalog name (None for 2-level naming)
        schema_name: Schema name (without catalog prefix)
        location: Table storage location (e.g., S3 path)
        metastore_id: Metastore ID for metastore-level mapping

    Returns:
        Tuple of (source_data_lake, source_schema_name)
        source_data_lake may be None if cannot be determined
    """

    LOG.debug(
        f"Determining source data lake for {catalog_name}.{schema_name} with location {location}")

    # Priority 1: Catalog-level mapping
    if catalog_name and catalog_name in CATALOG_TO_DATA_LAKE:
        return (CATALOG_TO_DATA_LAKE[catalog_name], schema_name)

    # Priority 2: Schema prefix mapping (for federated schemas)
    for prefix, data_lake in SCHEMA_PREFIX_TO_DATA_LAKE.items():
        if schema_name.startswith(prefix):
            # Remove the prefix from schema_name to get source_schema_name
            source_schema_name = schema_name[len(prefix):]
            return (data_lake, source_schema_name)

    # Priority 3: Location-based heuristics
    # Try to parse data lake from S3 bucket name or path
    if location:
        data_lake_from_location = _parse_data_lake_from_location(location)
        if data_lake_from_location:
            return (data_lake_from_location, schema_name)

    # Priority 4: Metastore-level mapping
    # This is a fallback for metastores that don't use catalogs or prefixes
    data_lake_from_metastore = _get_data_lake_from_metastore(metastore_id)
    if data_lake_from_metastore:
        return (data_lake_from_metastore, schema_name)

    # Priority 5: Fallback - use catalog as data lake if available
    if catalog_name:
        return (catalog_name, schema_name)

    # Could not determine data lake
    return (None, schema_name)


def _parse_data_lake_from_location(location: str) -> Optional[str]:
    """
    Parse data lake name from storage location.

    Tries to extract data lake from S3 bucket name or path patterns.

    Args:
        location: Storage location (e.g., s3://bucket-name/path/to/table)

    Returns:
        Data lake name or None if cannot be determined
    """
    if not location:
        return None

    try:
        # S3 path format: s3://bucket-name/path/to/data
        # ADLS path format: abfss://container@account.dfs.core.windows.net/path
        # HDFS path format: hdfs://namenode:port/path/to/data

        if location.startswith("s3://") or location.startswith("s3a://"):
            # Extract bucket name
            # Example: s3://egdp-prod-raw/schema/table -> egdp-prod
            bucket_part = location.split("/")[2]  # egdp-prod-raw

            # Try to match bucket name patterns to data lakes
            # Common patterns: {data_lake}-{tier}, {data_lake}_{tier}
            for data_lake in set(SCHEMA_PREFIX_TO_DATA_LAKE.values()):
                if bucket_part.startswith(data_lake.replace("_", "-")):
                    return data_lake
                if bucket_part.startswith(data_lake):
                    return data_lake

        elif location.startswith("abfss://"):
            # Azure ADLS Gen2 path
            # Example: abfss://container@egdpprod.dfs.core.windows.net/path
            # container@egdpprod.dfs.core.windows.net
            container_account = location.split("/")[2]
            account_name = container_account.split("@")[1].split(".")[0]  # egdpprod

            # Try to match account name to data lakes
            for data_lake in set(SCHEMA_PREFIX_TO_DATA_LAKE.values()):
                if account_name.replace("_", "").lower() in data_lake.replace("_", "").lower():
                    return data_lake

    except Exception as e:
        LOG.debug(f"Error parsing data lake from location {location}: {e}")

    return None


def _get_data_lake_from_metastore(metastore_id: int) -> Optional[str]:
    """
    Get data lake based on metastore configuration.

    This is a fallback for metastores without catalog or prefix information.

    Args:
        metastore_id: Metastore ID

    Returns:
        Data lake name or None if cannot be determined
    """
    try:
        metastore = get_query_metastore_by_id(metastore_id, session=get_session())
        querybook_instance = (
            "prod"
            if QuerybookSettings.PUBLIC_URL == "https://querybook.expedia.biz"
            else "test"
        )

        # Metastore name-based mapping (from EG HMS loader).
        # Both the legacy `*-waggledance` names and the newer
        # `waggledance-glue-read-*` names are accepted for backward compatibility.
        metastore_name_mapping = {
            "egdp-analytics-waggledance": "egdp_analytics",
            "waggledance-glue-read-egdp-analytics": "egdp_analytics",
            "egdp-test-waggledance": "egdp_test_analytics",
            "data-corp-waggledance": "egdataplatform_corp",
            "waggledance-glue-read-data-corp": "egdataplatform_corp",
            "data-test-waggledance": "egdataplatform_test",
            "waggledance-glue-read-data-test": "egdataplatform_test",
            "egdp-waggledance": "egdp_analytics",
        }

        # Check if metastore name has a direct mapping
        if metastore.name in metastore_name_mapping:
            return metastore_name_mapping[metastore.name]

        # Handle environment-specific metastores
        if metastore.name == "bex-waggledance":
            return "bexg_prod" if querybook_instance == "prod" else "bexg_test"
        if metastore.name == "vrbo-waggledance":
            return "vrbo_prod" if querybook_instance == "prod" else "vrbo_test"

    except Exception as e:
        LOG.debug(f"Error getting data lake from metastore {metastore_id}: {e}")

    return None
