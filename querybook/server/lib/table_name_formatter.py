"""
Utilities for formatting table names based on metastore display settings.
"""
from lib.logger import get_logger
from logic.admin import get_query_metastore_by_id
from app.db import with_session

LOG = get_logger(__file__)


@with_session
def format_table_name_for_display(
    table_name,
    schema_name,
    catalog_name,
    metastore_id,
    session=None
):
    """
    Format a table name for display in UI based on metastore settings.

    Requires BOTH enable_catalog_support AND show_catalog_in_ui to be true
    in order to include catalog in the display name.

    Args:
        table_name: Table name
        schema_name: Schema name
        catalog_name: Catalog name (can be None)
        metastore_id: Metastore ID
        session: Database session

    Returns:
        Formatted table name string
    """
    metastore = get_query_metastore_by_id(metastore_id, session=session)

    if not metastore:
        LOG.warning(
            f"Metastore with ID {metastore_id} not found for formatting table name.")
        # Fallback: show full name if metastore not found
        if catalog_name:
            return f"{catalog_name}.{schema_name}.{table_name}"
        return f"{schema_name}.{table_name}"

    enable_catalog_support = metastore.enable_catalog_support
    show_catalog_in_ui = metastore.show_catalog_in_ui

    # Only show catalog if BOTH settings are true
    if not enable_catalog_support or not show_catalog_in_ui or not catalog_name:
        return f"{schema_name}.{table_name}"

    return f"{catalog_name}.{schema_name}.{table_name}"
