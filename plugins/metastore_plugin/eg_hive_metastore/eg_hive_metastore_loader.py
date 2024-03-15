import base64
import re

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
)
from lib.utils import json as ujson

from const.metastore import (
    DataOwner,
    DataOwnerType,
    DataTableWarningSeverity,
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

from metastore_plugin.eg_hive_metastore.file_formats import detect_file_format

LOG = get_logger(__file__)


# Map of data elements and their colors
class EgTagColors(Enum):
    SENSITIVITY: str = "#85d0ce"  # icy blue
    CLOVERLEAF: str = "#ffca00"  # gold
    GOVERNANCE: str = "#35b5bb"  # blue
    ICEBERG: str = "#529dce"  # picton blue
    DELTA: str = "#b7652b"  # choco
    VIEW: str = "#f5a623"  # orange
    FILE_FORMAT: str = "#6ba097"  # creamy forest green


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

        last_modified_time = parameters.get("last_modified_time") or parameters.get(
            "transient_lastDdlTime"
        )
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
            partition_keys=self.get_partition_keys(description),
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
            tag_name = tag["name"]
            if parameters.get(tag_name) is not None:
                if tag_name == "eg-partner-data":
                    # Special case for partner data, which is either true / false
                    tags.append(
                        # either "No Partner Data" or "Partner Data"
                        DataTag(
                            name=(
                                "Partner Data"
                                if parameters.get(tag_name) == "true"
                                else "No Partner Data"
                            ),
                            type=tag["label"],
                            description=f"This table is tagged with `{tag_name}`",
                            color=EgTagColors.GOVERNANCE.value,
                        )
                    )
                else:
                    tags.append(
                        DataTag(
                            name=(
                                tag["concat"] + ": " + parameters.get(tag_name)
                                if tag.get("concat")
                                else parameters.get(tag_name)
                            ),
                            type=tag["label"],
                            description=f"This table is tagged with `{tag_name}`",
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

        # Check if the table is a view
        # Note: There's also `tableType` which can be `VIRTUAL_VIEW` or `MATERIALIZED_VIEW`
        # but we're using `viewOriginalText` to determine if it's a view
        if description.viewOriginalText is not None:
            tags.append(
                DataTag(
                    name="View",
                    description="This is a view",
                    color=EgTagColors.VIEW.value,
                )
            )

            # Support for Presto Views, which store base64 encoded data
            if parameters.get("presto_view") == "true":
                # Parse out the base64 encoded data from the viewOriginalText
                # Format: "/* Presto View: <BASE64 DATA> */"
                base64_data = extract_base64_data(description.viewOriginalText)
                if base64_data:
                    # Decode and deserialize the Base64 JSON data
                    view_data = base64.b64decode(base64_data).decode("utf-8")
                    view_data = ujson.loads(view_data)

                    # Add the original SQL to custom properties
                    table = table._replace(
                        custom_properties={
                            "original_sql": view_data["originalSql"],
                        }
                    )

                    # Replace the columns with the view data columns
                    columns = [
                        DataColumn(name=col["name"], type=col["type"])
                        for col in view_data["columns"]
                    ]

                    # Get view comment (if any) and replace the generated "Presto view" description
                    if view_data.get("comment"):
                        table = table._replace(description=view_data["comment"])

            else:
                # Some views have `viewOriginalText` containing the SQL in plain text
                # (I assume these are Hive views)
                table = table._replace(
                    custom_properties={
                        "original_sql": description.viewOriginalText,
                    }
                )

        # Detect and tag table / file formats
        # Skip views
        else:
            file_format = detect_file_format(sd, parameters)
            if file_format:
                # Add to existing custom_properties
                table = table._replace(
                    custom_properties={
                        **(
                            table.custom_properties
                            if table.custom_properties is not None
                            else {}
                        ),
                        "file_format": file_format,
                    }
                )

                tags.append(
                    DataTag(
                        name=file_format,
                        type="File Format",
                        description=f"This table is stored in {file_format} format",
                        color=EgTagColors.FILE_FORMAT.value,
                    )
                )

            # Avro warning for tables with an external Avro schema
            # The Hive Metastore may not report the correct column list in this case, and it's not
            # practical to load the schema directly from S3. So we just add a warning to the table.
            if file_format == "Avro" and parameters.get("avro.schema.url"):
                table = table._replace(
                    warnings=[
                        (
                            DataTableWarningSeverity.WARNING,
                            "This is an Avro table with an external schema file, so the columns shown in Querybook may not be correct.",
                        )
                    ]
                )

            # Iceberg!
            if parameters.get("table_type") == "ICEBERG":
                tags.append(
                    DataTag(
                        name="Iceberg",
                        type="Table Format",
                        description="This is an Iceberg table",
                        color=EgTagColors.ICEBERG.value,
                    )
                )
            # Delta Lake!
            elif parameters.get("spark.sql.sources.provider") == "delta":
                tags.append(
                    DataTag(
                        name="Delta",
                        type="Table Format",
                        description="This is a Delta Lake table",
                        color=EgTagColors.DELTA.value,
                    )
                )

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

    def get_partition_keys(self, hive_metastore_description):
        """
        Modified version from the base class to handle Iceberg tables
        """
        try:
            # Normal Hive tables
            if hive_metastore_description.partitionKeys:
                return [
                    partition_key.name
                    for partition_key in hive_metastore_description.partitionKeys
                ]

            # Iceberg tables
            elif hive_metastore_description.parameters.get("default-partition-spec"):
                default_partition_spec = ujson.loads(
                    hive_metastore_description.parameters.get("default-partition-spec")
                )
                current_schema = ujson.loads(
                    hive_metastore_description.parameters.get("current-schema")
                )
                current_schema_fields = {
                    field["id"]: field for field in current_schema["fields"]
                }

                # Get a list of source-ids for the partition fields
                partition_source_ids = [
                    field["source-id"] for field in default_partition_spec["fields"]
                ]

                # Convert the source-ids to column names
                return [
                    current_schema_fields[source_id]["name"]
                    for source_id in partition_source_ids
                ]

            else:
                return []

        except Exception:
            return []


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


def extract_base64_data(view_text):
    """
    Extracts base64 data from a given view text.

    Args:
        view_text (str): The text of the view.

    Returns:
        str or None: The extracted base64 data if found, None otherwise.
    """
    pattern = r"/\* Presto View: (.*) \*/"
    match = re.search(pattern, view_text)
    if match:
        return match.group(1)  # group(1) refers to the first parenthesized subgroup
    else:
        return None
