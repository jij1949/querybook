from enum import Enum
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

from const.metastore import (
    DataOwner,
    DataOwnerType,
    DataTag,
    MetastoreLoaderConfig,
    MetadataType,
    MetadataMode,
)

from metastore_plugin.eg_hive_metastore.data_elements import (
    data_elements,
    find_data_element,
)

from const.data_element import (
    DataElementAssociationTuple,
    DataElementAssociationType,
)

LOG = get_logger(__file__)


# Map of data elements and their colors
class EgTagColors(Enum):
    SENSITIVITY: str = "#85d0ce"  # icy blue
    CLOVERLEAF: str = "#ffca00"  # gold
    GOVERNANCE: str = "#35b5bb"  # blue
    ICEBERG: str = "#529dce"  # picton blue


# Max length of a tag name in the database (tag.name)
TAG_NAME_LIMIT = 255


# See: https://confluence.expedia.biz/display/EDMG/EDMG+-+Tags+for+Data+Governance
DATASET_TAGS = [
    {"name": "eg-owner", "mandatory": True, "tag": False},
    {"name": "eg-creator", "mandatory": True, "tag": False},
    {
        "name": "eg-brand",
        "label": "Brand",
        "mandatory": False,
        "tag": True,
    },
    {
        "name": "eg-domain",
        "label": "Domain",
        "mandatory": False,
        "tag": True,
    },
    {
        "name": "eg-storage-location",
        "label": "Storage Location",
        "mandatory": True,
        "tag": True,
        "concat": "Storage",
    },
    {
        "name": "eg-origin-location",
        "label": "Origin Location",
        "mandatory": True,
        "tag": True,
        "concat": "Origin",
    },
    {
        "name": "eg-application-name",
        "label": "Application",
        "mandatory": True,
        "tag": True,
    },
    {
        "name": "eg-partner-data",
        "label": "Partner Data",
        "mandatory": False,
        "tag": True,
    },
]

#
# Expedia-customized version of the HMSMetastoreLoader
#
class EgHMSMetastoreLoader(HMSMetastoreLoader):
    loader_config: MetastoreLoaderConfig = MetastoreLoaderConfig(
        {
            MetadataType.TAG: MetadataMode.WRITE_BACK,
            MetadataType.DATA_ELEMENT: MetadataMode.WRITE_BACK,
            MetadataType.OWNER: MetadataMode.WRITE_BACK,
        }
    )

    @classmethod
    def get_table_owner_types(cls) -> list[DataOwnerType]:
        """Return all the owner types the metastore supports.
        Override this method if loading table owners from metastore is enabled
        and your metastore supports owner types.
        E.g.
        [
            DataOwnerType(
                name="CREATOR",
                display_name="Table Creator",
                description="Person who created the table",
            ),
            DataOwnerType(
                name="BUSINESS_OWNER",
                display_name="Owners",
                description="Person or group who is responsible for business related aspects of the table",
            ),
        ]
        The `display_name` will be rendered as the field label in the detailed table view, which is `Owners` by default.
        """
        return [
            DataOwnerType(
                name=None, display_name="Owners", description="People who own the table"
            ),
            DataOwnerType(
                name="CREATOR",
                display_name="Creator",
                description="Creator of the table, from the `eg-creator` tag",
            ),
        ]

    # Can override this to test a limited set of tables
    # def get_all_schema_names(self) -> List[str]:
    #     # dbs = self.hmc.get_all_databases()
    #     # LOG.info("dbs: %s", dbs)

    #     return [
    #         "conversation",
    #         "egdp_test_conversation",
    #         "project_meso_raw",
    #         "supply",
    #         "egdp_prod_content",
    #         "bexg_etl_test_meso",
    #     ]

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
            owners=[],
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

        tags = []

        if description.owner and description.owner not in [
            "cloverleaf",
            "expedia",
            "hadoop",
            "root",
        ]:
            table.owners.append(DataOwner(username=description.owner))

        #
        # Process table parameters
        #

        # Add a table tag if the table is managed by Cloverleaf
        if (
            description.owner == "cloverleaf"
            or parameters.get("eg-managed-by") == "cloverleaf"
        ):
            tags.append(
                DataTag(
                    name="Cloverleaf",
                    description="This table is managed by Cloverleaf",
                    color=EgTagColors.CLOVERLEAF.value,
                )
            )

        # Iceberg!
        if parameters.get("table_type") == "ICEBERG":
            tags.append(
                DataTag(
                    name="Iceberg",
                    description="This is an Iceberg table",
                    color=EgTagColors.ICEBERG.value,
                )
            )

        if parameters.get("comment") is not None:
            # If the table has a comment, then use it as the description
            table = table._replace(description=parameters.get("comment"))
        if parameters.get("eg-owner") is not None:
            table.owners.append(DataOwner(username=parameters.get("eg-owner")))
        if parameters.get("eg-creator") is not None:
            table.owners.append(
                DataOwner(username=parameters.get("eg-creator"), type="CREATOR")
            )

        # Iterate through the list of dataset tags, filtered to tag: True
        for tag in [tag for tag in DATASET_TAGS if tag["tag"]]:
            tagName = tag["name"]
            if parameters.get(tagName) is not None:
                tags.append(
                    DataTag(
                        name=(
                            tag["concat"] + ": " + parameters.get(tagName)
                            if tag.get("concat")
                            else parameters.get(tagName)
                        ),
                        type=tag["label"],
                        description=f"This table is tagged with `{tagName}`",
                        color=EgTagColors.GOVERNANCE.value,
                    )
                )

        # # Disabled top tier for now
        # # If parameters contains all 5 mandatory tags, then set Top Tier
        # if all(
        #     parameters.get(tag["name"]) is not None
        #     for tag in DATASET_TAGS
        #     if tag["mandatory"]
        # ):
        #     table = table._replace(golden=True)

        # If the table is owned by "hadoop" and the schema_name starts with eps-prod,
        # then reassign the owner as e4b-bedrock. This fixes an issue where it displays Unknown (hadoop) as owner
        if description.owner == "hadoop" and schema_name.startswith("eps_prod"):
            table.owners.append(DataOwner(username="e4b-bedrock"))

        # Look for eg-sensitivity tags and apply them to the table and columns
        new_columns = columns
        if any(p.startswith("eg-sensitivity.") for p in parameters):

            # Map of eg-sensitivity tags: eg-sensitivity.<column_name> = <sensitivity_tag>
            # Map contains <column_name in lower-case>: <sensitivity_tag> pairs
            sensitivity_tags = {
                key.lower().replace("eg-sensitivity.", ""): value.lower()
                for key, value in parameters.items()
                if key.lower().startswith("eg-sensitivity.")
            }

            tags.append(
                DataTag(
                    name="Sensitivity",
                    description="This table contains sensitivity tags",
                    color=EgTagColors.SENSITIVITY.value,
                )
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

        # Update the table with the tags if any
        if tags:
            # Shorten tags if any names are too long (TAG_NAME_LIMIT)
            tags = [
                (
                    tag._replace(name=tag.name[: TAG_NAME_LIMIT - 3] + "...")
                    if len(tag.name) > TAG_NAME_LIMIT
                    else tag
                )
                for tag in tags
            ]

            # Add to the table
            table = table._replace(tags=tags)

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
        tags=col.tags
        + [
            DataTag(
                name=value.lower(),
                type="Sensitivity",
                color=EgTagColors.SENSITIVITY.value,
                description="This column contains a sensitivity tag",
            )
        ],
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
