"""
Databricks Unity Catalog Metastore Loader
This loader integrates Databricks Unity Catalog with Querybook's metastore system.
"""
from typing import Dict, List, Optional, Tuple

from clients.databricks_client import DatabricksUnityCatalogClient
from const.metastore import DataCatalog, DataColumn, DataSchema, DataTable
from lib.form import FormField, FormFieldType, StructFormField
from lib.metastore.base_metastore_loader import BaseMetastoreLoader
from lib.metastore.loaders.form_fileds import load_partitions_field
from lib.logger import get_logger
from lib.utils import json as ujson

LOG = get_logger(__name__)


class DatabricksMetastoreLoader(BaseMetastoreLoader):
    """
    Metastore loader for Databricks Unity Catalog.

    This loader fetches schema and table metadata from Databricks Unity Catalog
    and syncs it with Querybook's internal metastore.
    """

    def __init__(self, metastore_dict: Dict):
        """
        Initialize the Databricks metastore loader.

        Args:
            metastore_dict: Dictionary containing metastore configuration including:
                - workspace_url: Databricks workspace URL
                - token: Personal access token or service principal token
                - catalog_name: Optional catalog name (defaults to None for all catalogs)
                - warehouse_id: Optional warehouse ID for executing SQL statements
                - load_partitions: Whether to load partition information (TODO: Implement partition loading)
        """
        metastore_params = metastore_dict.get("metastore_params", {})

        self.workspace_url = metastore_params.get("workspace_url")
        self.token = metastore_params.get("token")
        self.catalog_name = metastore_params.get("catalog_name")
        self.warehouse_id = metastore_params.get("warehouse_id")
        self.load_partitions = metastore_params.get("load_partitions", False)

        # Initialize the Databricks client
        self.databricks_client = DatabricksUnityCatalogClient(
            workspace_url=self.workspace_url,
            token=self.token,
            catalog_name=self.catalog_name,
            warehouse_id=self.warehouse_id,
        )

        super(DatabricksMetastoreLoader, self).__init__(metastore_dict)

    @classmethod
    def get_metastore_params_template(cls):
        """
        Define the configuration form for the Databricks metastore loader.

        Returns:
            StructFormField with required configuration fields
        """
        return StructFormField(
            (
                "workspace_url",
                FormField(
                    required=True,
                    description="Databricks workspace URL (e.g., https://your-workspace.databricks.com)",
                    field_type=FormFieldType.String,
                    helper="The full URL of your Databricks workspace",
                ),
            ),
            (
                "token",
                FormField(
                    required=True,
                    hidden=True,
                    description="Databricks Personal Access Token (PAT) or Service Principal Token",
                    field_type=FormFieldType.String,
                    helper="Token for authenticating with the Databricks API.",
                ),
            ),
            (
                "catalog_name",
                FormField(
                    required=False,
                    description="Unity Catalog name (optional, leave empty to sync all catalogs)",
                    field_type=FormFieldType.String,
                    helper="Specify a specific catalog to sync, or leave empty to sync all accessible catalogs",
                ),
            ),
            (
                "warehouse_id",
                FormField(
                    required=False,
                    description="Databricks SQL Warehouse ID for executing SQL statements",
                    field_type=FormFieldType.String,
                    helper="Specify the warehouse ID to use for executing SQL statements like `DESCRIBE EXTENDED <table>`",
                ),
            ),
            ("load_partitions", load_partitions_field),
        )

    def get_all_schema_names(self) -> List[DataSchema]:
        """
        Get all schemas from the Databricks catalog with their catalog information.

        Returns:
            List of DataSchema NamedTuples with separated catalog and schema names
        """
        try:
            result = []

            if self.catalog_name:
                # If a specific catalog is configured, get schemas from that catalog
                schemas = self.databricks_client.get_all_schema_names(self.catalog_name)

                # Get catalog info
                catalog_info = self.get_catalog_info(self.catalog_name)

                # Create DataSchema objects with catalog information
                for schema in schemas:
                    result.append(DataSchema(
                        name=schema,
                        catalog=catalog_info
                    ))
            else:
                # If no catalog is specified, get schemas from all catalogs
                catalogs = self.databricks_client.get_all_catalogs()

                for catalog_name in catalogs:
                    schemas = self.databricks_client.get_all_schema_names(catalog_name)

                    # Get catalog info
                    catalog_info = self.get_catalog_info(catalog_name)

                    # Create DataSchema objects with catalog information
                    for schema in schemas:
                        result.append(DataSchema(
                            name=schema,
                            catalog=catalog_info
                        ))

            return result
        except Exception as e:
            LOG.error(f"Error fetching schema names from Databricks: {e}")
            return []

    def get_catalog_info(self, catalog_name: str) -> DataCatalog:
        """
        Get catalog metadata from Databricks.

        Args:
            catalog_name: The catalog name

        Returns:
            DataCatalog NamedTuple with catalog metadata
        """
        try:
            catalog_info = self.databricks_client.get_catalog_info(catalog_name)

            if not catalog_info:
                LOG.warning(f"Catalog {catalog_name} not found in Databricks")
                return DataCatalog(name=catalog_name)

            return DataCatalog(
                name=catalog_info.get("name"),
                description=catalog_info.get("comment"),
                owner=catalog_info.get("owner"),
                properties=catalog_info.get("properties", {}),
            )
        except Exception as e:
            LOG.error(f"Error fetching catalog info for {catalog_name}: {e}")
            # Return a basic DataCatalog with just the name on error
            return DataCatalog(name=catalog_name)

    def get_all_table_names_in_schema(
        self, schema_name: str, catalog_name: Optional[str] = None
    ) -> List[str]:
        """
        Get all table names in a specific schema.

        Args:
            schema_name: The schema name
            catalog_name: Optional explicit catalog name

        Returns:
            List of table names
        """
        try:
            # Determine catalog to use
            if catalog_name:
                actual_catalog = catalog_name
                actual_schema = schema_name
            else:
                # Fallback if only schema name is provided
                actual_catalog = self.catalog_name
                actual_schema = schema_name

            if not actual_catalog:
                LOG.warning(f"No catalog determined for schema {schema_name}")
                return []

            tables = self.databricks_client.get_all_table_names(
                schema_name=actual_schema,
                catalog_name=actual_catalog,
            )
            return tables
        except Exception as e:
            LOG.error(f"Error fetching table names for schema {schema_name}: {e}")
            return []

    def get_table_and_columns(
        self, schema_name: str, table_name: str, catalog_name: Optional[str] = None
    ) -> Tuple[DataTable, List[DataColumn]]:
        """
        Get detailed table metadata and column information.

        Args:
            schema_name: The schema name
            table_name: The table name
            catalog_name: Optional explicit catalog name

        Returns:
            Tuple of (DataTable, List[DataColumn])
        """
        try:
            # Determine catalog to use
            if catalog_name:
                actual_catalog = catalog_name
                actual_schema = schema_name
            else:
                # Fallback if only schema name is provided
                actual_catalog = self.catalog_name
                actual_schema = schema_name

            if not actual_catalog:
                LOG.warning(
                    f"No catalog determined for table {schema_name}.{table_name}")
                return None, []

            # Fetch table
            table_obj = self.databricks_client.get_table(
                schema_name=actual_schema,
                table_name=table_name,
                catalog_name=actual_catalog,
            )

            if not table_obj:
                LOG.warning(f"Table {schema_name}.{table_name} not found in Databricks")
                return None, []

            # TODO: We're already getting table properties from the table object,
            # but we might want to fetch additional metadata like partitions with this same method.
            # # Get table properties
            # table_properties = self.get_table_properties(
            #     schema_name=actual_schema,
            #     table_name=table_name,
            #     catalog_name=catalog_name,
            # )

            # Convert the table object to a dictionary-like structure
            table_props = {
                "name": table_obj.name,
                "catalog_name": table_obj.catalog_name,
                "schema_name": table_obj.schema_name,
                "table_type": table_obj.table_type.value if table_obj.table_type else None,
                "data_source_format": table_obj.data_source_format.value if table_obj.data_source_format else None,
                "storage_location": table_obj.storage_location,
                "owner": table_obj.owner,
                "comment": table_obj.comment,
                "created_at": table_obj.created_at,
                "updated_at": table_obj.updated_at,
                "created_by": table_obj.created_by,
                "updated_by": table_obj.updated_by,
                "columns": [
                    {
                        "name": col.name,
                        "type": col.type_text,
                        "comment": col.comment,
                        "nullable": col.nullable,
                        "partition_index": col.partition_index,
                    }
                    for col in (table_obj.columns or [])
                ],
                "properties": table_obj.properties or {},
            }

            columns_data = table_props.get("columns", [])

            # Convert timestamps from milliseconds to seconds if needed
            created_at = table_props.get("created_at")
            updated_at = table_props.get("updated_at")

            # Databricks timestamps are in milliseconds, convert to seconds
            if created_at:
                created_at = int(
                    created_at / 1000) if created_at > 10000000000 else int(created_at)
            if updated_at:
                updated_at = int(
                    updated_at / 1000) if updated_at > 10000000000 else int(updated_at)

            try:
                raw_description = ujson.pdumps(
                    table_obj.as_dict(), default=lambda o: o.__dict__)
            except Exception as e:
                LOG.warning(f"Could not create raw_description: {e}")
                raw_description = ujson.pdumps(table_obj, default=str)

            table = DataTable(
                name=table_name,
                type=table_props.get("table_type"),
                owner=table_props.get("owner"),
                table_created_at=created_at,
                table_updated_by=table_props.get("updated_by"),
                table_updated_at=updated_at,
                location=table_props.get("storage_location"),
                # TODO: Implement partition loading on the next phase, for now we can leave it empty or None
                partitions=[] if not self.load_partitions else None,
                raw_description=raw_description,
            )

            # Create DataColumn objects
            columns = [
                DataColumn(
                    name=col.get("name"),
                    type=col.get("type"),
                    comment=col.get("comment"),
                )
                for col in columns_data
            ]

            return table, columns

        except Exception as e:
            LOG.error(
                f"Error fetching table and columns for {schema_name}.{table_name}: {e}",
                exc_info=True
            )
            return None, []

    def get_table_properties(self, schema_name: str, table_name: str, catalog_name: str) -> Dict:
        """
        Get table properties for additional table metadata.

        Args:
            schema_name: Name of the schema
            table_name: Name of the table
            catalog_name: Name of the catalog

        """
        table_properties_obj = self.databricks_client.get_table_properties(
            schema_name=schema_name,
            table_name=table_name,
            catalog_name=catalog_name,
        )

        LOG.debug(
            f"Fetched table properties for {schema_name}.{table_name}: {table_properties_obj}")
        return table_properties_obj

    # TODO: Implement partition loading in the next phase, for now we can leave it empty or None
    def get_partitions(
        self, schema_name: str, table_name: str, conditions: Dict[str, str] = None
    ) -> List[str]:
        """
        Get partition information for a table.

        Note: This is a placeholder for future implementation.
        Databricks Unity Catalog partition information would require additional API calls.

        Args:
            schema_name: The schema name in format 'catalog.schema'
            table_name: The table name
            conditions: Optional filtering conditions for partitions

        Returns:
            List of partition strings
        """
        LOG.warning("Partition loading not yet implemented for Databricks tables")
        return []
