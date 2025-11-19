"""
Databricks Unity Catalog Client
This client wraps the Databricks SDK to fetch metadata about schemas, tables, and columns.
"""
from typing import Dict, List, Optional
from lib.logger import get_logger

from databricks.sdk import WorkspaceClient
from databricks.sdk.core import Config
from databricks.sdk.service.catalog import TableInfo

from databricks.sdk import AccountClient

LOG = get_logger(__name__)


class DatabricksUnityCatalogClient:
    """Client for interacting with Databricks Unity Catalog using the Databricks SDK."""

    def __init__(self, workspace_url: str, token: str, catalog_name: Optional[str] = None, warehouse_id: Optional[str] = None):
        """
        Initialize the Databricks Unity Catalog client.

        Args:
            workspace_url: The Databricks workspace URL
            token: Personal access token or service principal token for authentication
            catalog_name: Optional catalog name to use. If not provided, will use the default catalog
        """
        self.workspace_url = workspace_url.rstrip("/")
        self.token = token
        self.catalog_name = catalog_name
        self.warehouse_id = warehouse_id

        # Initialize the Databricks SDK WorkspaceClient
        config = Config(
            host=self.workspace_url,
            token=self.token,
        )

        self.workspace_client = WorkspaceClient(config=config)

    def get_all_catalogs(self) -> List[str]:
        """
        Get all catalogs from Unity Catalog.

        Returns:
            List of catalog names
        """
        try:
            catalogs = list(self.workspace_client.catalogs.list())
            return [catalog.name for catalog in catalogs if catalog.name]
        except Exception as e:
            LOG.error(f"Error fetching catalogs: {e}")
            return []

    def get_all_schema_names(self, catalog_name: Optional[str] = None) -> List[str]:
        """
        Get all schemas from a specific catalog.

        Args:
            catalog_name: Name of the catalog. If not provided, uses the instance's catalog_name

        Returns:
            List of schema names
        """
        catalog = catalog_name or self.catalog_name

        if not catalog:
            LOG.warning("No catalog name provided for get_all_schema_names")
            return []

        try:
            schemas = list(self.workspace_client.schemas.list(catalog_name=catalog))
            return [schema.name for schema in schemas if schema.name]
        except Exception as e:
            LOG.error(f"Error fetching schemas for catalog {catalog}: {e}")
            return []

    def get_all_table_names(self, schema_name: str, catalog_name: Optional[str] = None) -> List[str]:
        """
        Get all tables in a specific schema.

        Args:
            schema_name: Name of the schema
            catalog_name: Name of the catalog. If not provided, uses the instance's catalog_name

        Returns:
            List of table names
        """
        catalog = catalog_name or self.catalog_name

        if not catalog:
            LOG.warning(
                f"No catalog name provided for get_all_table_names in schema {schema_name}")
            return []

        try:
            tables = list(
                self.workspace_client.tables.list(
                    catalog_name=catalog,
                    schema_name=schema_name,
                )
            )
            return [table.name for table in tables if table.name]
        except Exception as e:
            LOG.error(f"Error fetching tables for schema {catalog}.{schema_name}: {e}")
            return []

    def get_table(self, schema_name: str, table_name: str, catalog_name: Optional[str] = None) -> Optional[TableInfo]:
        """
        Get detailed information about a specific table.

        Args:
            schema_name: Name of the schema
            table_name: Name of the table
            catalog_name: Name of the catalog. If not provided, uses the instance's catalog_name

        Returns:
            TableInfo object containing table metadata
        """
        catalog = catalog_name or self.catalog_name
        full_table_name = f"{catalog}.{schema_name}.{table_name}"

        if not catalog:
            LOG.warning(
                f"No catalog name provided for get_table: {schema_name}.{table_name}")
            return None

        try:
            table = self.workspace_client.tables.get(full_name=full_table_name)
            return table
        except Exception as e:
            LOG.error(f"Error fetching table {full_table_name}: {e}")
            return None

    def get_columns(self, schema_name: str, table_name: str, catalog_name: Optional[str] = None) -> List[Dict]:
        """
        Get column information for a specific table.

        Args:
            schema_name: Name of the schema
            table_name: Name of the table
            catalog_name: Name of the catalog. If not provided, uses the instance's catalog_name

        Returns:
            List of column dictionaries with name, type, and comment
        """
        table_info = self.get_table(schema_name, table_name, catalog_name)

        if not table_info:
            return []

        columns = table_info.get("columns", [])
        return [
            {
                "name": col.get("name"),
                "type": col.get("type_text") or col.get("type_name"),
                "comment": col.get("comment"),
                "nullable": col.get("nullable"),
                "partition_index": col.get("partition_index"),
            }
            for col in columns
        ]

    def get_table_properties(self, schema_name: str, table_name: str, catalog_name: Optional[str] = None) -> Dict:
        """
        Get table properties including owner, creation time, and other metadata.

        Args:
            schema_name: Name of the schema
            table_name: Name of the table
            catalog_name: Name of the catalog. If not provided, uses the instance's catalog_name

        Returns:
            Dictionary with table properties
        """
        if not self.warehouse_id:
            LOG.warning(
                f"No warehouse_id provided for get_table_properties: {schema_name}.{table_name}")
            return {}

        response = self.workspace_client.statement_execution.execute_statement(
            warehouse_id=self.warehouse_id,
            statement=f"DESCRIBE EXTENDED {catalog_name}.{schema_name}.{table_name}",
            wait_timeout="30s"
        )

        if response.status.state == "SUCCEEDED":
            LOG.info(
                f"Statement executed successfully for table {schema_name}.{table_name}")

            # Parse the data_array
            table_properties = {}
            data_array = response.result.data_array

            LOG.debug(f"Data array from DESCRIBE EXTENDED: {data_array}")

            # The data_array contains rows with [col_name, data_type, comment]
            # Rows after "# Detailed Table Information" contain key-value pairs
            parsing_detailed_info = False

            for row in data_array:
                if len(row) >= 2:
                    col_name = row[0]
                    data_type = row[1]

                    # Start parsing detailed table info
                    if col_name == "# Detailed Table Information":
                        parsing_detailed_info = True
                        continue

                    # Skip header rows and empty rows
                    if col_name.startswith("#") or not col_name or not col_name.strip():
                        continue

                    # In detailed info section, col_name is the property key
                    if parsing_detailed_info and data_type:
                        table_properties[col_name] = data_type

            LOG.info(f"Parsed table properties: {table_properties}")
            return table_properties

        LOG.error(
            f"Statement execution failed: {response.status.error if response.status.error else 'Unknown error'}")
        return {}
