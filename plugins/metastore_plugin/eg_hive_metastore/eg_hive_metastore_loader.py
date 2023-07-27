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


LOG = get_logger(__file__)

#
# Expedia-customized version of the HMSMetastoreLoader
#
class EgHMSMetastoreLoader(HMSMetastoreLoader):
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

        return table, columns
