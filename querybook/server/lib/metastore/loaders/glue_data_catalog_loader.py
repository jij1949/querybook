from datetime import datetime
from typing import Dict, List, Tuple

from clients.glue_client import GlueDataCatalogClient
from const.metastore import DataColumn, DataSchema, DataTable
from lib.form import FormField, StructFormField
from lib.metastore.base_metastore_loader import BaseMetastoreLoader
from lib.metastore.loaders.form_fileds import load_partitions_field
from lib.logger import get_logger
from lib.utils import json as ujson

LOG = get_logger(__name__)


class GlueDataCatalogLoader(BaseMetastoreLoader):
    def __init__(self, metastore_dict: Dict):
        self.catalog_id = metastore_dict.get("metastore_params").get("catalog_id")
        self.region = metastore_dict.get("metastore_params").get("region")
        self.aws_profile = metastore_dict.get("metastore_params").get("aws_profile")
        self.load_partitions = metastore_dict.get("metastore_params").get(
            "load_partitions"
        )
        self.glue_client = self._get_glue_data_catalog_client(
            self.catalog_id, self.region, self.aws_profile
        )
        super(GlueDataCatalogLoader, self).__init__(metastore_dict)

    @classmethod
    def get_metastore_params_template(cls):
        return StructFormField(
            (
                "catalog_id",
                FormField(
                    required=True,
                    description="Enter the Glue Data Catalog ID",
                    regex=r"^\d{12}$",
                ),
            ),
            ("region", FormField(required=True, description="Enter the AWS Region")),
            (
                "aws_profile",
                FormField(
                    required=False,
                    description="AWS Profile name from ~/.aws/credentials (optional, uses default if not specified)  *For local testing only*",
                ),
            ),
            ("load_partitions", load_partitions_field),
        )

    def get_all_schema_names(self) -> List[DataSchema]:
        """Get all schemas from Glue Data Catalog.

        Returns:
            List of DataSchema NamedTuples with separated catalog and schema names
        """
        from const.metastore import DataCatalog

        schema_names = self.glue_client.get_all_database_names()

        LOG.info(f"Retrieved  {len(schema_names)} schema names")

        # Use configured display name if set, otherwise use catalog_id
        catalog_display_name = self.get_catalog_display_name(self.catalog_id)

        LOG.info(f"Using catalog display name: {catalog_display_name}")

        glue_catalog = DataCatalog(
            name=catalog_display_name,
            description="AWS Glue Data Catalog",
        )
        return [DataSchema(name=schema, catalog=glue_catalog) for schema in schema_names]

    def get_all_table_names_in_schema(
        self, schema_name: str
    ) -> List[str]:
        return self.glue_client.get_all_table_names(schema_name)

    def get_table_and_columns(
        self, schema_name: str, table_name: str
    ) -> Tuple[DataTable, List[DataColumn]]:
        glue_table = self.glue_client.get_table(schema_name, table_name).get("Table")

        if self.load_partitions:
            partitions = self.get_partitions(schema_name, table_name)
        else:
            partitions = []

        # Get storage descriptor safely
        storage_descriptor = glue_table.get("StorageDescriptor") or {}

        table = DataTable(
            name=glue_table.get("Name"),
            type=glue_table.get("TableType"),
            owner=glue_table.get("Owner"),
            table_created_at=int(
                glue_table.get("CreateTime", datetime(1970, 1, 1)).timestamp()
            ),
            table_updated_at=int(
                glue_table.get("UpdateTime", datetime(1970, 1, 1)).timestamp()
            ),
            location=storage_descriptor.get("Location"),
            partitions=partitions,
            raw_description=ujson.pdumps(glue_table, default=str),
        )

        columns = [
            DataColumn(col.get("Name"), col.get("Type"), col.get("Comment"))
            for col in (storage_descriptor.get("Columns") or [])
        ]

        partition_keys = glue_table.get("PartitionKeys") or []
        columns.extend(
            [
                DataColumn(col.get("Name"), col.get("Type"), col.get("Comment"))
                for col in partition_keys
            ]
        )

        return table, columns

    def get_partitions(
        self, schema_name: str, table_name: str, conditions: Dict[str, str] = None
    ) -> List[str]:
        return self.glue_client.get_hms_style_partitions(
            schema_name, table_name, conditions
        )

    @staticmethod
    def _get_glue_data_catalog_client(catalog_id, region, aws_profile):
        return GlueDataCatalogClient(catalog_id, region, aws_profile)
