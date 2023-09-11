from typing import List, Tuple

from lib.logger import get_logger
from lib.metastore.base_metastore_loader import (
    DataTable,
    DataColumn,
)
from lib.metastore.loaders.hive_metastore_loader import (
    HMSMetastoreLoader,
    get_hive_metastore_table_description,
    get_partition_keys,
)
from lib.utils import json as ujson

from const.metastore import DataTag, MetastoreLoaderConfig, MetadataType, MetadataMode

from metastore_plugin.eg_hive_metastore.data_elements import (
    data_elements,
    find_data_element,
)

from const.data_element import (
    DataElementAssociationTuple,
    DataElementAssociationType,
)

LOG = get_logger(__file__)

#
# Expedia-customized version of the HMSMetastoreLoader
#
class EgHMSMetastoreLoader(HMSMetastoreLoader):
    loader_config: MetastoreLoaderConfig = MetastoreLoaderConfig(
        {
            MetadataType.TAG: MetadataMode.WRITE_BACK,
            MetadataType.DATA_ELEMENT: MetadataMode.WRITE_BACK,
        }
    )
    # # Can override this to test a limited set of tables
    # def get_all_schema_names(self) -> List[str]:
    #     # dbs = self.hmc.get_all_databases()
    #     # LOG.info("dbs: %s", dbs)

    #     return ["conversation"]

    def get_table_and_columns(
        self, schema_name, table_name
    ) -> Tuple[DataTable, List[DataColumn]]:
        description = get_hive_metastore_table_description(
            self.hmc, schema_name, table_name
        )
        if not description:
            return None, []

        parameters = description.parameters
        sd = description.sd
        partitions = (
            self.get_partitions(schema_name, table_name) if self.load_partitions else []
        )

        last_modified_time = parameters.get("last_modified_time")
        last_modified_time = (
            int(last_modified_time) if last_modified_time is not None else None
        )

        total_size = parameters.get("totalSize")
        total_size = int(total_size) if total_size is not None else None

        table = DataTable(
            name=description.tableName,
            type=description.tableType,
            owner=description.owner,
            table_created_at=description.createTime,
            table_updated_by=parameters.get("last_modified_by"),
            table_updated_at=last_modified_time,
            data_size_bytes=total_size,
            location=sd.location,
            partitions=partitions,
            raw_description=ujson.pdumps(description, default=lambda o: o.__dict__),
            partition_keys=get_partition_keys(description),
        )

        columns = list(
            map(
                lambda col: DataColumn(
                    name=col.name, type=col.type, comment=col.comment
                ),
                sd.cols + description.partitionKeys,
            )
        )

        # If the table is owned by "hadoop" and the schema_name starts with eps-prod,
        # then reassign the owner as e4b-bedrock. This fixes an issue where it displays Unknown (hadoop) as owner
        if description.owner == "hadoop" and schema_name.startswith("eps_prod"):
            table = table._replace(owner="e4b-bedrock")

        # If the table is owned by the "cloverleaf" user, then we can
        # extract the table description and owner from the table
        if description.owner == "cloverleaf":
            parameters = description.parameters

            if parameters.get("eg-creator") is not None:
                table = table._replace(owner=parameters.get("eg-creator"))

            if parameters.get("comment") is not None:
                table = table._replace(description=parameters.get("comment"))

        new_columns = columns

        if any(p.startswith("eg-sensitivity.") for p in parameters):

            # Map of eg-sensitivity tags: eg-sensitivity.<column_name> = <sensitivity_tag>
            # Map contains <column_name in lower-case>: <sensitivity_tag> pairs
            sensitivity_tags = {
                key.lower().replace("eg-sensitivity.", ""): value.lower()
                for key, value in parameters.items()
                if key.lower().startswith("eg-sensitivity.")
            }

            table = table._replace(
                tags=table.tags
                + [
                    DataTag(
                        name="Sensitivity",
                        description="This table contains sensitivity tags",
                        color="#85d0ce",
                    )
                ]
            )

            new_columns = [
                (
                    apply_sensitivity_tag_and_data_element(
                        col, sensitivity_tags[col.name.lower()]
                    )
                    if col.name.lower() in sensitivity_tags
                    else col
                )
                for col in columns
            ]

        return table, new_columns


def apply_sensitivity_tag_and_data_element(col, value):
    """
    Apply the sensitivity tag and optional data element to the column
    @param col: The column to apply the sensitivity tag and data element to
    @param value: The value of the sensitivity tag
    @return: The column with the sensitivity tag and optional data element applied
    """

    # Always add the sensitivity tag with the value in lower-case
    col = col._replace(
        tags=col.tags + [DataTag(name=value.lower(), type="Sensitivity")],
    )

    # Look for a data element by sensitivity tag value
    # Not all sensitivity tags will match a data element, usually because the tag is incorrect
    data_element = find_data_element(value)
    if data_element is not None:
        col = col._replace(
            data_element=DataElementAssociationTuple(
                type=DataElementAssociationType.REF,
                value_data_element=data_element,
            ),
        )

    return col
