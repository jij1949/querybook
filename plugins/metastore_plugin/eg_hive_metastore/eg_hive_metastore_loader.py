import base64
import re

from enum import Enum
import time
from typing import Dict, List, Tuple

from app.db import get_session, with_session
from env import QuerybookSettings
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

from hmsclient.genthrift.hive_metastore.ttypes import NoSuchObjectException

from logic.admin import get_query_metastore_by_id
from logic.elasticsearch import delete_es_table_by_id
from logic.metastore import (
    delete_schema,
    delete_table,
    get_table_by_schema_id,
    get_table_by_schema_id_and_name,
    iterate_data_schema,
)
from metastore_plugin.eg_hive_metastore.data_elements import (
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
    HUDI: str = "#b7652b"  # choco
    VIEW: str = "#f5a623"  # orange
    FILE_FORMAT: str = "#6ba097"  # creamy forest green
    SOURCE: str = "#C792EA"  # light purple


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
        "meta": {"rank": 59},
    },
    {
        "name": "eg-domain",
        "label": "Domain",
        "mandatory": False,
        "tag": True,
        "meta": {"rank": 58},
    },
    {
        "name": "eg-application-name",
        "label": "Application",
        "mandatory": True,
        "tag": True,
        "meta": {"rank": 57},
    },
    {
        "name": "eg-origin-location",
        "label": "Origin Location",
        "mandatory": True,
        "tag": True,
        "meta": {"rank": 56},
    },
    {
        "name": "eg-storage-location",
        "label": "Storage Location",
        "mandatory": True,
        "tag": True,
        "meta": {"rank": 55},
    },
    {
        "name": "eg-partner-data",
        "label": "Partner Data",
        "mandatory": False,
        "tag": True,
        "meta": {"rank": 54},
    },
]


#
# Expedia-customized version of the HMSMetastoreLoader
#
class EgHMSMetastoreLoader(HMSMetastoreLoader):

    def __init__(self, metastore_dict: Dict):
        super().__init__(metastore_dict)

        # Number of days to wait before refreshing a table (in batch refresh mode)
        # This is used to stagger the refresh of tables across multiple days
        # Every table will be refreshed every `resync_tables_every_n_days` days
        self.resync_tables_every_n_days = 5

        # Calculate the modulo of the current day, which is used to stagger the refresh of tables
        # This assigns every day a number from 0 to `resync_tables_every_n_days - 1`, and every day
        # when the sync is run, it will only refresh tables that match the current day modulo
        #
        # This value is calculated once and used for the entire lifetime of the loader
        # A new instance of the loader will be created every time the metastore is refreshed
        self.current_day_modulo = (
            int(time.time() / 86400) % self.resync_tables_every_n_days
        )

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

    def should_sync_table(self, table=None):
        """
        Determine if a table should by synced or not.  This function should
        only be used in batch refresh mode.

        We want to stagger the refresh of tables across multiple days, so we don't
        refresh all tables at once. This is to prevent overloading the metastore, speed up
        the refresh process, and spread out the load across multiple days.

        Every table will be refreshed every `resync_tables_every_n_days` days.

        Tables are assigned to N buckets based on their id. Then we check if the modulo of the current day
        matches the bucket of the table. If it does, we refresh the table.

        Any new tables will be immediately refreshed since they don't have an id yet.
        """
        if not table:
            return True

        # If the table updated_at is more than self.resync_tables_every_n_days days ago, then refresh it
        # This might happen if the resync doesn't run every day
        if (
            time.time() - table.updated_at.timestamp()
            > self.resync_tables_every_n_days * 86400
        ):
            return True

        # If the table id modulo matches the current day modulo, then refresh it
        if self.current_day_modulo == table.id % self.resync_tables_every_n_days:
            return True
        return False

    # Custom implementation to double-check before deleting schemas
    @with_session
    def delete_schema_not_in_metastore(self, metastore_id, schema_names, session=None):
        checked_count = 0
        deleted_count = 0

        for data_schema in iterate_data_schema(metastore_id, session=session):
            checked_count += 1
            LOG.info(f"Checking schema {data_schema.id}, {data_schema.name}...")
            try:
                if data_schema.name not in schema_names:
                    # Note: this bypasses the ACL check, but we're not currently using ACLs
                    LOG.info(
                        f"Double-checking if schema should be deleted: {data_schema.id}, {data_schema.name}"
                    )
                    schema = self.get_schema(data_schema.name)
                    if schema is not None:
                        LOG.warning(
                            f"Schema was found in metastore, skipping deletion: {data_schema.id}, {data_schema.name}"
                        )
                        continue

                    LOG.info(f"Deleting schema {data_schema.id}, {data_schema.name}...")
                    # We delete table 1 by 1 since we need to delete it for elasticsearch
                    # Maybe we can optimize it to allow batch deletion
                    for table in data_schema.tables:
                        table_id = table.id
                        delete_table(table_id=table_id, commit=False, session=session)
                        delete_es_table_by_id(table_id)
                    delete_schema(id=data_schema.id, commit=False, session=session)
                    LOG.info(f"Deleted schema {data_schema.id}, {data_schema.name}")
                    deleted_count += 1
            except Exception as e:
                LOG.error(
                    f"Error deleting schema, skipping deletion: {data_schema.id}, {data_schema.name}",
                    e,
                )

        session.commit()

        LOG.info(
            f"Checked {checked_count} schemas for metastore {metastore_id}, deleted {deleted_count} schemas"
        )

    # Custom implementation to double-check before deleting tables
    @with_session
    def delete_table_not_in_metastore(self, schema_id, table_names, session=None):
        checked_count = 0
        deleted_count = 0

        db_tables = get_table_by_schema_id(schema_id, session=session)

        with session.no_autoflush:
            for data_table in db_tables:
                checked_count += 1
                try:
                    if data_table.name not in table_names:
                        # Note: this bypasses the ACL check, but we're not currently using ACLs
                        LOG.info(
                            f"Double-checking if table should be deleted: {data_table.id}, {data_table.data_schema.name}.{data_table.name}"
                        )
                        table = self.get_table(
                            data_table.data_schema.name, data_table.name
                        )
                        if table is not None:
                            LOG.warning(
                                f"Table was found in metastore, skipping deletion: {data_table.id}, {data_table.name} "
                            )
                            continue

                        LOG.info(
                            f"Deleting table {data_table.id}, {data_table.name}..."
                        )
                        table_id = data_table.id
                        delete_table(table_id=table_id, commit=False, session=session)
                        delete_es_table_by_id(table_id)
                        LOG.info(f"Deleted table {table_id}, {data_table.name}")
                        deleted_count += 1
                except Exception as e:
                    LOG.error(
                        f"Error deleting table, skipping deletion: {data_table.id}, {data_table.data_schema.name}.{data_table.name}",
                        e,
                    )
            session.commit()

            LOG.info(
                f"Checked {checked_count} tables for schema {schema_id}, deleted {deleted_count} tables"
            )

    @with_session
    def _create_table_table(
        self,
        schema_id,
        schema_name,
        table_name,
        table=None,
        columns=None,
        from_batch=False,
        session=None,
    ):
        """
        Override the base method to filter out tables we don't want to refresh.
        """
        # If from_batch is True, it is a batch refresh of the metastore
        # Check if the table is already in the database.
        # If it is, check if we should refresh it or not.
        # This is a performance optimization to speed up the batch refresh process
        if from_batch:
            # Get the existing table from the database
            existing_table = get_table_by_schema_id_and_name(
                schema_id, table_name, session=session
            )

            # If the table exists and we don't want to refresh it, then skip it
            if not self.should_sync_table(existing_table):
                LOG.debug(f"Skipping refresh of {schema_name}.{table_name}")
                return None

        # Sync the table as normal
        return super()._create_table_table(
            schema_id,
            schema_name,
            table_name,
            table=table,
            columns=columns,
            from_batch=from_batch,
            session=session,
        )

    def get_all_schema_names(self) -> List[str]:
        schemas = self.hmc.get_all_databases()
        LOG.info(f"Found {len(schemas)} schemas in metastore {self.metastore_id}")

        return schemas

    def get_schema(self, schema_name: str):
        """
        Get the schema object from the metastore.
        """
        try:
            return self.hmc.get_database(schema_name)
        except NoSuchObjectException:
            return None

    def get_table(self, schema_name: str, table_name: str):
        """
        Get the table object from the metastore.
        """
        try:
            return self.hmc.get_table(schema_name, table_name)
        except NoSuchObjectException:
            return None

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
            partitions=[],
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

        table_links = []
        tags = []
        custom_properties = {}

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
                    meta={"rank": 20, "icon": "Clover"},
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

        if parameters.get("eg-source-control-url") is not None:
            table_links.append(
                {
                    "label": "Source Control",
                    "url": parameters.get("eg-source-control-url"),
                }
            )

        # Iterate through the list of dataset tags, filtered to tag: True
        for tag in [tag for tag in DATASET_TAGS if tag["tag"]]:
            tag_name = tag["name"]
            if parameters.get(tag_name) is not None:
                if tag_name == "eg-partner-data":
                    # Special case for partner data, which is either true / false
                    tags.append(
                        DataTag(
                            name=(
                                "Partner Data: Yes"
                                if parameters.get(tag_name) == "true"
                                else "Partner Data: No"
                            ),
                            type=tag["label"],
                            description=f"This table is tagged with `{tag_name}`",
                            color=EgTagColors.GOVERNANCE.value,
                            meta=tag["meta"] or {},
                        )
                    )
                else:
                    tags.append(
                        DataTag(
                            name=tag["label"] + ": " + parameters.get(tag_name),
                            type=tag["label"],
                            description=f"This table is tagged with `{tag_name}`",
                            color=EgTagColors.GOVERNANCE.value,
                            meta=tag["meta"] or {},
                        )
                    )

        # Check if the table is a view
        if (
            description.tableType == "VIEW"
            or description.tableType == "VIRTUAL_VIEW"
            or description.tableType == "MATERIALIZED_VIEW"
        ):
            tags.append(
                DataTag(
                    name="View",
                    description="This is a view",
                    color=EgTagColors.VIEW.value,
                    meta={"rank": 101, "icon": "View"},
                )
            )

            # Process viewOriginalText for views
            # Note: not all views have viewOriginalText
            if description.viewOriginalText:
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
                        custom_properties["original_sql"] = view_data["originalSql"]

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
                    custom_properties["original_sql"] = description.viewOriginalText

        # Detect and tag table / file formats
        # Skip all views, since they don't have a file format
        else:
            file_format = detect_file_format(sd, parameters)
            if file_format:

                custom_properties["file_format"] = file_format

                tags.append(
                    DataTag(
                        name=f"File Format: {file_format}",
                        type="File Format",
                        description=f"This table is stored in {file_format} format",
                        color=EgTagColors.FILE_FORMAT.value,
                        meta={"rank": 100},
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
                        name="Table Format: Iceberg",
                        type="Table Format",
                        description="This is an Iceberg table",
                        color=EgTagColors.ICEBERG.value,
                        meta={"rank": 99},
                    )
                )

            # Delta Lake!
            elif parameters.get("spark.sql.sources.provider") == "delta":
                tags.append(
                    DataTag(
                        name="Table Format: Delta",
                        type="Table Format",
                        description="This is a Delta Lake table",
                        color=EgTagColors.DELTA.value,
                        meta={"rank": 99},
                    )
                )

            # Hudi!
            elif sd.inputFormat == "org.apache.hudi.hadoop.HoodieParquetInputFormat":
                tags.append(
                    DataTag(
                        name="Table Format: Hudi",
                        type="Table Format",
                        description="This is a Hudi table",
                        color=EgTagColors.HUDI.value,
                        meta={"rank": 99},
                    )
                )

        # If the table is owned by "hadoop" and the schema_name starts with eps-prod,
        # then reassign the owner as e4b-bedrock. This fixes an issue where it displays Unknown (hadoop) as owner
        if description.owner == "hadoop" and schema_name.startswith("eps_prod"):
            table.owners.append(DataOwner(username="e4b-bedrock"))

        # Look for eg-sensitivity tags and apply them to the table and columns
        new_columns = columns
        if (
            any(p.startswith("eg-sensitivity.") for p in parameters)
            and parameters.get("eg-sensitivity.is-sensitive") != "false"
        ):

            # Map of eg-sensitivity tags: eg-sensitivity.<column_name> = <sensitivity_tag>
            # Map contains <column_name in lower-case>: <sensitivity_tag> pairs
            # If the column_name contains a dot, then it's a nested column, and we parse out the first part only
            sensitivity_tags = {
                key.lower().replace("eg-sensitivity.", "").split(".")[0]: value
                for key, value in parameters.items()
                if key.lower().startswith("eg-sensitivity.")
                and key.lower() != "eg-sensitivity.is-sensitive"
            }

            tags.append(
                DataTag(
                    name="Sensitivity",
                    description="This table contains sensitivity tags",
                    color=EgTagColors.SENSITIVITY.value,
                    meta={"rank": 90, "icon": "Fingerprint"},
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

        # Determine source data lake and schema name
        source_data_lake, source_schema_name = get_source_data_lake_and_schema(
            self.metastore_id,
            schema_name,
            sd.location,
        )
        if source_data_lake is None:
            tags.append(
                DataTag(
                    name="Source Data Lake: Unknown",
                    type="Source Data Lake",
                    description="The source data lake for this table is unknown",
                    color=EgTagColors.SOURCE.value,
                    meta={"rank": 40},
                )
            )
        else:
            tags.append(
                DataTag(
                    name=f"Source Data Lake: {source_data_lake}",
                    type="Source Data Lake",
                    description="The source data lake for this table",
                    color=EgTagColors.SOURCE.value,
                    meta={"rank": 40},
                )
            )

            # Add custom properties which are visible in the table details
            custom_properties["source_schema_name"] = source_schema_name
            custom_properties["source_data_lake"] = source_data_lake

        # Determine Top Tier status and boost score
        # This comes from the `querybook2.eg_top_tier_table` table,
        # which is populated by the `top_tier_task.py` task
        #
        # This table started as just top tier, but now contains the most popular tables as well
        # As a result, Top Tier tables are identified via the `top_tier` column
        top_tier_row = get_top_tier_row(
            source_data_lake, source_schema_name, table_name
        )

        if top_tier_row:
            # Columns: source_data_lake, source_schema_name, table_name, user_count, number_of_queries, popularity, top_tier, boost_score
            [
                _,
                _,
                _,
                _,
                _,
                popularity,
                top_tier,
                boost_score,
            ] = top_tier_row

            # The `popularity` column is the rank of the table per PUMA data (1 = most popular)
            custom_properties["popularity"] = popularity

            # The `top_tier` column is a boolean (0 or 1) and determines whether the table is top tier or not
            is_top_tier = top_tier == 1

            # The `boost_score` column is a float and is derived from the popularity of the table
            table = table._replace(
                golden=is_top_tier,
                boost_score=boost_score,
            )

            # Load partitions if enabled and top tier
            if self.load_partitions and is_top_tier:
                table = table._replace(
                    partitions=self.get_partitions(schema_name, table_name)
                )

        # Update the table with table_links (if any)
        if table_links:
            table = table._replace(table_links=table_links)

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

        if custom_properties:
            table = table._replace(custom_properties=custom_properties)

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
                name=f"Sensitivity: {value.lower()}",
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


# Map of federation prefixes to data lakes
schema_prefixes_to_data_lakes = {
    "bexg_etl_prod_": "bexg_etl_prod",
    "bexg_etl_test_": "bexg_etl_test",
    "bexg_prod_": "bexg_prod",
    "bexg_test_": "bexg_test",
    "content_prod_": "content_prod",
    "controlplane_prod_": "controlplane_prod",
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
    "hcom_data_prod_uw2_": "hcom_.data_prod",
    "hotwire_prod_": "hotwire_prod",
    "marketplacehealth_prod_": "marketplacehealth_prod",
    "perf_": "perf",
    "qubole_meta_": "dsp_prod",
    "vrbo_prod_": "vrbo_prod",
    "vrbo_stage_": "vrbo_stage",
    "vrbo_test_": "vrbo_test",
}


def get_source_data_lake_and_schema(metastore_id, schema_name, location):
    """
    Get the source schema from the schema name.
    The source schema is a schema name without any federation prefix.
    Not all schemas have a federation prefix, so this function may return the same schema name.

    Returns (source_data_lake, source_schema_name)
    """
    metastore = get_query_metastore_by_id(metastore_id, session=get_session())
    querybook_instance = (
        "prod"
        if QuerybookSettings.PUBLIC_URL == "https://querybook.expedia.biz"
        else "test"
    )
    # LOG.debug(
    #     f"Schema Name: {schema_name}, Metastore name: {metastore.name}, Querybook instance: {querybook_instance}"
    # )

    # Test for matching prefixes
    for prefix, data_lake in schema_prefixes_to_data_lakes.items():
        if schema_name.startswith(prefix):
            return (data_lake, schema_name[len(prefix) :])

    # If there's no prefix, then it's not federated,
    # so we can use the metastore name to determine the data lake
    if metastore.name == "egdp-analytics-waggledance":
        return ("egdp_analytics", schema_name)
    if metastore.name == "egdp-test-waggledance":
        return ("egdp_test_analytics", schema_name)
    if metastore.name == "bex-waggledance" and querybook_instance == "prod":
        return ("bexg_prod", schema_name)
    if metastore.name == "bex-waggledance" and querybook_instance == "test":
        return ("bexg_test", schema_name)
    if metastore.name == "data-corp-waggledance":
        return ("egdataplatform_corp", schema_name)
    if metastore.name == "data-test-waggledance":
        return ("egdataplatform_test", schema_name)
    if metastore.name == "vrbo-waggledance" and querybook_instance == "prod":
        return ("vrbo_prod", schema_name)
    if metastore.name == "vrbo-waggledance" and querybook_instance == "test":
        return ("vrbo_test", schema_name)
    if metastore.name == "egdp-waggledance":
        if schema_name == "sandbox":
            # Sandbox is a special case
            return ("egdp_analytics", schema_name)
        else:
            return ("egdp_prod", schema_name)

    return (None, schema_name)


def get_top_tier_row(source_data_lake, source_schema_name, table_name, session=None):
    """
    Get the top tier row for a given table.
    Returns the row if found, otherwise None.
    """
    try:
        session = get_session() if session is None else session

        top_tier_rows = session.execute(
            """
            SELECT * FROM eg_top_tier_table
            WHERE source_data_lake = :source_data_lake
                AND source_schema_name = :source_schema_name
                AND table_name = :table_name
        """,
            {
                "source_data_lake": source_data_lake,
                "source_schema_name": source_schema_name,
                "table_name": table_name,
            },
        ).fetchall()

        if top_tier_rows and len(top_tier_rows) > 0:
            row = top_tier_rows[0]
            LOG.debug(f"Top Tier Rows {row}")
            return row

        # No row found
        return None

    except Exception as e:
        LOG.error(f"Error checking Top Tier status: {e}")
        return None
