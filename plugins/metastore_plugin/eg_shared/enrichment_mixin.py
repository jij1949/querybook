"""
EG Metastore Enrichment Mixin

This mixin class provides table and column enrichment logic that can be used
across multiple metastore types (HMS, Databricks, Glue). It extracts metadata
from table parameters, storage descriptors, and external sources to enrich
table objects with tags, owners, data elements, and custom properties.

The mixin is designed to be metastore-agnostic by using adapter methods to
extract parameters and storage descriptors from different table formats.
"""
import base64
import re
from enum import Enum
from typing import Dict, List, Optional, Tuple

from app.db import get_session
from const.data_element import (
    DataElementAssociationTuple,
    DataElementAssociationType,
)
from const.metastore import (
    DataColumn,
    DataOwner,
    DataOwnerType,
    DataTable,
    DataTableWarningSeverity,
    DataTag,
    MetadataMode,
    MetadataType,
    MetastoreLoaderConfig,
)
from lib.logger import get_logger
from lib.utils import json as ujson

from metastore_plugin.eg_shared.data_elements import find_data_element
from metastore_plugin.eg_shared.data_lake_mapping import determine_source_data_lake
from metastore_plugin.eg_shared.file_formats import detect_file_format

LOG = get_logger(__file__)


# Tag color constants
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


# Databricks data_source_format to Hadoop InputFormat class mapping
DATA_SOURCE_FORMAT_TO_INPUT_FORMAT = {
    "DELTA": None,  # Delta tables don't use traditional input format
    "PARQUET": "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat",
    "ORC": "org.apache.hadoop.hive.ql.io.orc.OrcInputFormat",
    "AVRO": "org.apache.hadoop.hive.ql.io.avro.AvroContainerInputFormat",
    "JSON": "org.apache.hadoop.mapred.TextInputFormat",
    "CSV": "org.apache.hadoop.mapred.TextInputFormat",
    "TEXT": "org.apache.hadoop.mapred.TextInputFormat",
}


# Max length of a tag name in the database
TAG_NAME_LIMIT = 255


# Governance tags for data governance
# See: https://expediagroup.atlassian.net/wiki/spaces/EDMG/pages/478642776/EDMG+-+Tags+for+Data+Governance
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


class MockStorageDescriptor:
    """
    Mock storage descriptor object for metastores that don't use HMS format.
    Used to provide a consistent interface for extracting file format information.
    """

    def __init__(
        self,
        location: Optional[str] = None,
        input_format: Optional[str] = None,
        serde: Optional[str] = None,
    ):
        self.location = location
        self.inputFormat = input_format

        # Create a mock serdeInfo object
        class SerdeInfo:
            def __init__(self, serde):
                self.serializationLib = serde

        self.serdeInfo = SerdeInfo(serde) if serde else None


class EgEnrichmentMixin:
    """
    Mixin class for enriching tables with EG-specific metadata.

    This mixin can be used by any metastore loader (HMS, Databricks, Glue)
    to add EG-specific enrichments like tags, owners, data elements, etc.

    The loader must implement:
    - metastore_id: The ID of the metastore
    - load_partitions: Boolean flag to control partition loading
    - get_partitions(schema_name, table_name): Method to load partitions (optional)
    """

    # Shared loader configuration for all EG loaders
    loader_config: MetastoreLoaderConfig = MetastoreLoaderConfig(
        {
            MetadataType.TAG: MetadataMode.WRITE_BACK,
            MetadataType.DATA_ELEMENT: MetadataMode.WRITE_BACK,
            MetadataType.OWNER: MetadataMode.WRITE_BACK,
        }
    )

    @classmethod
    def get_table_owner_types(cls) -> list[DataOwnerType]:
        """
        Return all the owner types the metastore supports.

        Returns:
            List of DataOwnerType with custom owner types for EG enrichment
        """
        return [
            DataOwnerType(
                name=None,
                display_name="Owners",
                description="People who own the table",
            ),
            DataOwnerType(
                name="CREATOR",
                display_name="Creator",
                description="Creator of the table, from the `eg-creator` tag",
            ),
        ]

    def __init__(self, *args, **kwargs):
        """
        Initialize the enrichment mixin with caching support.

        Sets up a dictionary cache for parsed table descriptions to
        eliminate redundant parsing during enrichment operations.
        """
        super().__init__(*args, **kwargs)
        self._parsed_description_cache = {}

    def normalize_description_key(self, key: str) -> str:
        """
        Normalize a key name from raw table description.

        This method provides a hook for child loaders to transform keys from
        their specific metadata formats (e.g., Glue's CamelCase keys) to the
        snake_case format expected by enrichment logic.

        Default implementation returns key unmodified. Child loaders override
        to apply format-specific transformations (e.g., CamelCase → snake_case).

        Args:
            key: Original key name

        Returns:
            Normalized key name
        """
        return key

    def _normalize_key_value(self, key: str, value: any) -> Tuple[str, any]:
        """
        Normalize a key-value pair with recursive dict handling.

        This method handles the generic structure (recursion) while delegating
        format-specific key transformation to normalize_description_key().

        The parent mixin handles recursive dict traversal, allowing child loaders
        to focus only on key name transformation logic.

        Args:
            key: Original key name
            value: Associated value (may be dict requiring recursion)

        Returns:
            Tuple of (normalized_key, normalized_value)
        """
        # Get normalized key from child class
        norm_key = self.normalize_description_key(key)

        # Parent handles recursive dict traversal
        if isinstance(value, dict):
            normalized_value = {}
            for nested_key, nested_val in value.items():
                n_key, n_val = self._normalize_key_value(nested_key, nested_val)
                normalized_value[n_key] = n_val
            return (norm_key, normalized_value)

        return (norm_key, value)

    def _parse_catalog_schema(self, schema_name: str) -> Tuple[Optional[str], str]:
        """
        Parse a schema identifier that may contain a catalog prefix.

        Args:
            schema_name: Schema name, may be in "catalog.schema" format

        Returns:
            Tuple of (catalog_name, schema_name)
            catalog_name will be None if no catalog prefix is present
        """
        if "." in schema_name:
            parts = schema_name.split(".", 1)
            return (parts[0], parts[1])
        return (None, schema_name)

    def _parse_raw_description(self, table):
        """
        Parse raw_description from table with caching support.

        This method caches the parsed and normalized description to eliminate
        redundant parsing when the same table object is processed multiple times
        during enrichment operations.

        Args:
            table: Table object with raw_description attribute

        Returns:
            Parsed and normalized description (dict or object), or None if parsing fails
        """
        # Use object identity as cache key (DataTable contains lists, so not hashable)
        table_id = id(table)

        # Check cache first
        if table_id in self._parsed_description_cache:
            return self._parsed_description_cache[table_id]

        # Parse and normalize (first time for this table)
        description = self._do_parse_and_normalize(table)

        # Cache result
        self._parsed_description_cache[table_id] = description
        return description

    def _do_parse_and_normalize(self, table):
        """
        Parse and normalize raw_description (implementation called from cached method).

        Calls _normalize_key_value() for each key-value pair, which delegates
        key transformation to normalize_description_key() and handles recursive
        dict traversal.

        Args:
            table: Table object with raw_description attribute

        Returns:
            Parsed and normalized description (dict or object), or None if parsing fails
        """
        if not hasattr(table, "raw_description") or not table.raw_description:
            return None

        description = table.raw_description

        # If it's a JSON string, parse it
        if isinstance(description, str):
            try:
                description = ujson.loads(description)
            except Exception as e:
                LOG.debug(f"Could not parse raw_description as JSON: {e}")
                return None

        # Apply key normalization with recursion
        if isinstance(description, dict):
            normalized = {}
            for key, value in description.items():
                norm_key, norm_value = self._normalize_key_value(key, value)
                normalized[norm_key] = norm_value
            return normalized

        # Already an object (not dict) - return as-is
        return description

    def _extract_parameters(self, table) -> Dict[str, str]:
        """
        Extract table parameters from raw_description.

        Different metastore types store parameters in different locations:
        - HMS: description.parameters
        - Databricks/Glue: table.properties or similar

        Args:
            table: The raw table object with raw_description attribute

        Returns:
            Dictionary of table parameters
        """
        description = self._parse_raw_description(table)
        if not description:
            return {}

        params = {}

        # HMS format: description.parameters
        if hasattr(description, "parameters") and description.parameters:
            params = dict(description.parameters)

        # Glue format: description.Parameters
        elif hasattr(description, "Parameters") and description.Parameters:
            params = dict(description.Parameters)

        # Databricks/Glue format: properties field
        elif hasattr(description, "properties") and description.properties:
            params = dict(description.properties)

        # Dict format: try both parameters and properties keys
        elif isinstance(description, dict):
            params = dict(description.get(
                "parameters", description.get("properties", {})))

        # For Databricks: add data_source_format and table_type to parameters
        # This allows file format detection to work correctly
        if isinstance(description, dict):
            if "data_source_format" in description and "data_source_format" not in params:
                # Convert to spark.sql.sources.provider format for Delta detection
                data_source_format = description.get("data_source_format", "").lower()
                if data_source_format == "delta":
                    params["spark.sql.sources.provider"] = "delta"
                params["data_source_format"] = description.get("data_source_format")

            if "table_type" in description and "table_type" not in params:
                params["table_type"] = description.get("table_type")

        return params

    def _extract_storage_descriptor(self, table) -> MockStorageDescriptor:
        """
        Extract storage descriptor from raw_description or create a mock object.

        Different metastore types have different storage information:
        - HMS: description.sd (StorageDescriptor object)
        - Databricks: storage_location, data_source_format
        - Glue: storage_descriptor dict

        Args:
            table: The raw table object with raw_description attribute

        Returns:
            StorageDescriptor object or MockStorageDescriptor
        """
        description = self._parse_raw_description(table)
        if not description:
            return MockStorageDescriptor()

        # HMS format: description.sd
        if hasattr(description, "sd") and description.sd:
            return description.sd

        # Databricks format: extract location and format information
        location = None
        input_format = None
        serde = None

        if hasattr(description, "storage_location"):
            location = description.storage_location
        elif hasattr(description, "StorageDescriptor"):
            location = description.StorageDescriptor.Location
        elif hasattr(description, "location"):
            location = description.location

        if hasattr(description, "data_source_format"):
            # Map Databricks data source format to input format
            data_source_format = description.data_source_format.upper()
            input_format = DATA_SOURCE_FORMAT_TO_INPUT_FORMAT.get(data_source_format)

        # Glue format: storage_descriptor dict
        if hasattr(description, "storage_descriptor") and isinstance(
            description.storage_descriptor, dict
        ):
            sd = description.storage_descriptor
            location = sd.get("location")
            input_format = sd.get("input_format")
            if "serde_info" in sd:
                serde = sd["serde_info"].get("serialization_library")

        # Handle dict format (most common for Databricks/Glue)
        if isinstance(description, dict):
            location = description.get(
                "location") or description.get("storage_location")

            # Get data_source_format from dict
            if "data_source_format" in description:
                data_source_format = description.get("data_source_format", "").upper()
                input_format = DATA_SOURCE_FORMAT_TO_INPUT_FORMAT.get(
                    data_source_format)

            # Fallback to input_format field
            if not input_format and "input_format" in description:
                input_format = description.get("input_format")

            if "serde_info" in description:
                serde = description["serde_info"].get("serialization_library")

            # Handle nested storage_descriptor dict (Glue format after normalization)
            if "storage_descriptor" in description and isinstance(description["storage_descriptor"], dict):
                sd = description["storage_descriptor"]
                # Prefer nested values over top-level values
                if not location and "location" in sd:
                    location = sd.get("location")
                if not input_format and "input_format" in sd:
                    input_format = sd.get("input_format")
                if not serde and "serde_info" in sd:
                    serde = sd["serde_info"].get("serialization_library")

        return MockStorageDescriptor(
            location=location, input_format=input_format, serde=serde
        )

    def _enrich_table_and_columns(
        self,
        table: DataTable,
        columns: List[DataColumn],
        catalog_name: Optional[str],
        schema_name: str,
        table_name: str,
        metastore_id: int,
    ) -> Tuple[DataTable, List[DataColumn]]:
        """
        Main enrichment entry point. Applies all EG-specific enrichments.

        Args:
            table: Base table object to enrich
            columns: List of column objects to enrich
            catalog_name: Catalog name (None for 2-level naming)
            schema_name: Schema name (without catalog)
            table_name: Table name
            metastore_id: Metastore ID

        Returns:
            Tuple of (enriched_table, enriched_columns)
        """
        LOG.debug(
            f"Starting enrichment for table {schema_name}.{table_name} with catalog {catalog_name}")
        # Extract parameters and storage descriptor
        parameters = self._extract_parameters(table)
        sd = self._extract_storage_descriptor(table)

        # Parse raw_description once
        description = self._parse_raw_description(table)

        # Get owner from raw_description if available
        owner = None
        if description:
            if hasattr(description, "owner"):
                owner = description.owner
            elif isinstance(description, dict):
                owner = description.get("owner")

        # Get table type from raw_description
        table_type = None
        view_original_text = None
        if description:
            if hasattr(description, "tableType"):
                table_type = description.tableType
            elif isinstance(description, dict):
                table_type = description.get("table_type")

            # Get viewOriginalText for views
            if hasattr(description, "viewOriginalText"):
                view_original_text = description.viewOriginalText
            elif isinstance(description, dict):
                view_original_text = description.get("view_original_text")

        # Initialize enrichment collections
        table_links = []
        tags = []
        custom_properties = {}

        # Process owner
        table = self._process_owners(table, owner, parameters, schema_name)

        # Process Cloverleaf tag
        tags.extend(self._process_cloverleaf_tag(owner, parameters))

        # Process comment/description
        if parameters.get("comment") is not None:
            table = table._replace(description=parameters.get("comment"))

        # Process table links
        table_links.extend(self._process_table_links(parameters))

        # Process governance tags
        tags.extend(self._process_governance_tags(parameters))

        # Process view tags and extract view metadata
        is_view = table_type in ["VIEW", "VIRTUAL_VIEW", "MATERIALIZED_VIEW"]
        if is_view:
            view_tags, view_custom_props, view_columns = self._process_view_tags(
                view_original_text, parameters, columns
            )
            tags.extend(view_tags)
            custom_properties.update(view_custom_props)
            if view_columns:
                columns = view_columns

        # Process file formats and table formats (non-views only)
        if not is_view:
            file_format_tags, file_format_props, file_format_warnings = (
                self._process_file_formats(sd, parameters)
            )
            tags.extend(file_format_tags)
            custom_properties.update(file_format_props)
            if file_format_warnings:
                table = table._replace(
                    warnings=(table.warnings or []) + file_format_warnings
                )

            # Process table format tags (Iceberg, Delta, Hudi)
            table_format_tags = self._process_table_formats(sd, parameters)
            tags.extend(table_format_tags)

        # Process sensitivity tags and apply to columns
        sensitivity_tags, new_columns = self._process_sensitivity_tags(
            parameters, columns
        )
        tags.extend(sensitivity_tags)
        columns = new_columns

        # Determine source data lake
        source_data_lake, source_schema_name = determine_source_data_lake(
            catalog_name, schema_name, sd.location, metastore_id
        )

        # Add source data lake tags and properties
        source_tags, source_props = self._process_source_data_lake(
            source_data_lake, source_schema_name
        )
        tags.extend(source_tags)
        custom_properties.update(source_props)

        # Process top tier / trending status
        table, top_tier_props = self._process_top_tier(
            table, source_data_lake, source_schema_name, table_name, schema_name
        )
        custom_properties.update(top_tier_props)

        # Process AI-generated descriptions
        ai_props = self._process_ai_descriptions(
            source_data_lake, source_schema_name, table_name
        )
        custom_properties.update(ai_props)

        # Apply collected enrichments to table
        if table_links:
            table = table._replace(table_links=table_links)

        if tags:
            # Shorten tags if any names are too long
            tags = [
                (
                    tag._replace(name=tag.name[: TAG_NAME_LIMIT - 3] + "...")
                    if len(tag.name) > TAG_NAME_LIMIT
                    else tag
                )
                for tag in tags
            ]
            table = table._replace(tags=tags)

        if custom_properties:
            table = table._replace(custom_properties=custom_properties)

        return table, columns

    def _add_owner_if_not_exists(
        self, table: DataTable, username: str, owner_type: Optional[str] = None
    ) -> bool:
        """
        Add owner to table if not already present (deduplication).

        Args:
            table: Table object
            username: Username to add
            owner_type: Type of owner (None for regular owner, "CREATOR" for creator)

        Returns:
            True if owner was added, False if already exists
        """
        # Check if owner already exists with same username and type
        for existing_owner in table.owners:
            existing_type = getattr(existing_owner, "type", None)
            if existing_owner.username == username and existing_type == owner_type:
                return False

        # Add new owner - don't pass type if None (creates regular owner)
        if owner_type is None:
            table.owners.append(DataOwner(username=username))
        else:
            table.owners.append(DataOwner(username=username, type=owner_type))
        return True

    def _process_owners(
        self,
        table: DataTable,
        owner: Optional[str],
        parameters: Dict[str, str],
        schema_name: str,
    ) -> DataTable:
        """
        Process and add table owners from metadata.

        Args:
            table: Table object
            owner: Owner from table metadata
            parameters: Table parameters
            schema_name: Schema name

        Returns:
            Table with owners added
        """
        # Clear existing owners and rebuild from current metadata to avoid duplicates
        table = table._replace(owners=[])

        # Add owner from table metadata (if not a system user)
        if owner and owner not in ["cloverleaf", "expedia", "hadoop", "root"]:
            self._add_owner_if_not_exists(table, owner)

        # Add eg-owner parameter
        if parameters.get("eg-owner") is not None:
            self._add_owner_if_not_exists(table, parameters.get("eg-owner"))

        # Add eg-creator parameter
        if parameters.get("eg-creator") is not None:
            self._add_owner_if_not_exists(
                table, parameters.get("eg-creator"), "CREATOR")

        # Special case: fix hadoop owner for eps-prod schemas
        if owner == "hadoop" and schema_name.startswith("eps_prod"):
            self._add_owner_if_not_exists(table, "e4b-bedrock")

        return table

    def _process_cloverleaf_tag(
        self, owner: Optional[str], parameters: Dict[str, str]
    ) -> List[DataTag]:
        """
        Add Cloverleaf tag if table is managed by Cloverleaf.

        Args:
            owner: Table owner
            parameters: Table parameters

        Returns:
            List of tags (empty or with Cloverleaf tag)
        """
        tags = []

        if owner == "cloverleaf" or parameters.get("eg-managed-by") == "cloverleaf":
            tags.append(
                DataTag(
                    name="Cloverleaf",
                    description="This table is managed by Cloverleaf",
                    color=EgTagColors.CLOVERLEAF.value,
                    meta={"rank": 20, "icon": "Clover"},
                )
            )

        return tags

    def _process_table_links(self, parameters: Dict[str, str]) -> List[Dict]:
        """
        Extract table links from parameters.

        Args:
            parameters: Table parameters

        Returns:
            List of table link dicts
        """
        table_links = []

        if parameters.get("eg-source-control-url") is not None:
            table_links.append(
                {
                    "label": "Source Control",
                    "url": parameters.get("eg-source-control-url"),
                }
            )

        return table_links

    def _process_governance_tags(self, parameters: Dict[str, str]) -> List[DataTag]:
        """
        Process governance tags from parameters.

        Args:
            parameters: Table parameters

        Returns:
            List of governance tags
        """
        tags = []

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

        return tags

    def _process_view_tags(
        self,
        view_original_text: Optional[str],
        parameters: Dict[str, str],
        columns: List[DataColumn],
    ) -> Tuple[List[DataTag], Dict[str, str], Optional[List[DataColumn]]]:
        """
        Process view-specific tags and metadata.

        Note: Presto view parsing is HMS-specific but kept for compatibility.
        Non-HMS loaders may skip this or handle differently.

        Args:
            view_original_text: Original view SQL text
            parameters: Table parameters
            columns: Current column list

        Returns:
            Tuple of (tags, custom_properties, new_columns or None)
        """
        tags = []
        custom_properties = {}
        new_columns = None

        tags.append(
            DataTag(
                name="View",
                description="This is a view",
                color=EgTagColors.VIEW.value,
                meta={"rank": 101, "icon": "View"},
            )
        )

        # Process viewOriginalText for views (if available)
        if view_original_text:
            # Support for Presto Views (HMS-specific), which store base64 encoded data
            if parameters.get("presto_view") == "true":
                # Parse out the base64 encoded data from the viewOriginalText
                # Format: "/* Presto View: <BASE64 DATA> */"
                base64_data = self._extract_base64_data(view_original_text)
                if base64_data:
                    try:
                        # Decode and deserialize the Base64 JSON data
                        view_data = base64.b64decode(base64_data).decode("utf-8")
                        view_data = ujson.loads(view_data)

                        # Add the original SQL to custom properties
                        custom_properties["original_sql"] = view_data.get(
                            "originalSql", ""
                        )

                        # Replace the columns with the view data columns
                        if "columns" in view_data:
                            new_columns = [
                                DataColumn(name=col["name"], type=col["type"])
                                for col in view_data["columns"]
                            ]

                        # Get view comment (if any)
                        if view_data.get("comment"):
                            # Note: Cannot modify table here, return in custom_properties
                            custom_properties["view_comment"] = view_data["comment"]
                    except Exception as e:
                        LOG.warning(f"Error parsing Presto view data: {e}")

            else:
                # Some views have viewOriginalText containing the SQL in plain text
                # (Hive views or other formats)
                custom_properties["original_sql"] = view_original_text

        return tags, custom_properties, new_columns

    def _process_file_formats(
        self, sd: MockStorageDescriptor, parameters: Dict[str, str]
    ) -> Tuple[List[DataTag], Dict[str, str], List[Tuple]]:
        """
        Detect and tag file formats.

        Args:
            sd: Storage descriptor (real or mock)
            parameters: Table parameters

        Returns:
            Tuple of (tags, custom_properties, warnings)
        """
        tags = []
        custom_properties = {}
        warnings = []

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

            # CSV and JSON warnings for unoptimized file formats
            if file_format in ["CSV", "JSON"]:
                warnings.append(
                    (
                        DataTableWarningSeverity.WARNING,
                        f"This table uses the unoptimized {file_format} file format. Use of non-optimized format can significantly slow down query performance. More information at: https://expediagroup.atlassian.net/wiki/spaces/DSPKB/pages/393153599/Parquet+vs+Json+format",
                    )
                )

            # Avro warning for tables with an external Avro schema
            if file_format == "Avro" and parameters.get("avro.schema.url"):
                warnings.append(
                    (
                        DataTableWarningSeverity.WARNING,
                        "This is an Avro table with an external schema file, so the columns shown in Querybook may not be correct.",
                    )
                )

        return tags, custom_properties, warnings

    def _process_table_formats(
        self, sd: MockStorageDescriptor, parameters: Dict[str, str]
    ) -> List[DataTag]:
        """
        Process table format tags (Iceberg, Delta, Hudi).

        Args:
            sd: Storage descriptor
            parameters: Table parameters

        Returns:
            List of table format tags
        """
        tags = []

        # Iceberg
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

        # Delta Lake
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

        # Hudi
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

        return tags

    def _process_sensitivity_tags(
        self, parameters: Dict[str, str], columns: List[DataColumn]
    ) -> Tuple[List[DataTag], List[DataColumn]]:
        """
        Process sensitivity tags and apply them to columns.

        Args:
            parameters: Table parameters
            columns: Column list

        Returns:
            Tuple of (table_tags, enriched_columns)
        """
        tags = []
        new_columns = columns

        if (
            any(p.startswith("eg-sensitivity.") for p in parameters)
            and parameters.get("eg-sensitivity.is-sensitive") != "false"
        ):
            # Map of eg-sensitivity tags: eg-sensitivity.<column_name> = <sensitivity_tag>
            # Map contains <column_name in lower-case>: <sensitivity_tag> pairs
            # If the column_name contains a dot, it's a nested column - parse out first part only
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
                    self._apply_sensitivity_tag_and_data_element(
                        col, sensitivity_tags[col.name.lower()]
                    )
                    if col.name.lower() in sensitivity_tags
                    else col
                )
                for col in columns
            ]

        return tags, new_columns

    def _apply_sensitivity_tag_and_data_element(
        self, col: DataColumn, value: str
    ) -> DataColumn:
        """
        Apply sensitivity tag and optional data element to a column.

        Args:
            col: Column to enrich
            value: Sensitivity tag value

        Returns:
            Enriched column
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
        # Not all sensitivity tags will match a data element
        data_element = find_data_element(value)
        if data_element is not None:
            col = col._replace(
                data_element=DataElementAssociationTuple(
                    type=DataElementAssociationType.REF,
                    value_data_element=data_element,
                ),
            )

        return col

    def _process_source_data_lake(
        self, source_data_lake: Optional[str], source_schema_name: str
    ) -> Tuple[List[DataTag], Dict[str, str]]:
        """
        Process source data lake tags and properties.

        Args:
            source_data_lake: Determined source data lake
            source_schema_name: Schema name without prefix

        Returns:
            Tuple of (tags, custom_properties)
        """
        tags = []
        custom_properties = {}

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

        return tags, custom_properties

    def _process_top_tier(
        self,
        table: DataTable,
        source_data_lake: Optional[str],
        source_schema_name: str,
        table_name: str,
        schema_name: str,
    ) -> Tuple[DataTable, Dict[str, str]]:
        """
        Process top tier / trending status and boost score.

        Args:
            table: Table object
            source_data_lake: Source data lake
            source_schema_name: Source schema name
            table_name: Table name
            schema_name: Full schema name (for partition loading)

        Returns:
            Tuple of (updated_table, custom_properties)
        """
        custom_properties = {}

        # Check if source_data_lake is available (required for top tier lookup)
        if not source_data_lake:
            return table, custom_properties

        # Get top tier row from database
        top_tier_row = self._get_top_tier_row(
            source_data_lake, source_schema_name, table_name
        )

        if top_tier_row:
            [_, _, _, trending, popularity, importance_score] = top_tier_row

            # The popularity column is the rank of the table per PUMA data (1 = most popular)
            custom_properties["popularity"] = popularity

            # The trending column is a boolean (0 or 1) and set to 1 if the table is trending
            is_trending = trending == 1

            # The importance_score column is a float derived from table popularity
            table = table._replace(
                golden=is_trending,
                boost_score=importance_score,
            )

            # Load partitions if enabled and trending
            if (
                hasattr(self, "load_partitions")
                and self.load_partitions
                and is_trending
            ):
                if hasattr(self, "get_partitions"):
                    try:
                        partitions = self.get_partitions(schema_name, table_name)
                        table = table._replace(partitions=partitions)
                    except Exception as e:
                        LOG.warning(f"Error loading partitions: {e}")

        return table, custom_properties

    def _process_ai_descriptions(
        self, source_data_lake: Optional[str], source_schema_name: str, table_name: str
    ) -> Dict[str, str]:
        """
        Process AI-generated table descriptions.

        Args:
            source_data_lake: Source data lake
            source_schema_name: Source schema name
            table_name: Table name

        Returns:
            Custom properties dict with AI descriptions
        """
        custom_properties = {}

        # Check if source_data_lake is available
        if not source_data_lake:
            return custom_properties

        ai_table_descriptions_row = self._get_ai_table_descriptions_row(
            source_data_lake, source_schema_name, table_name
        )

        if ai_table_descriptions_row:
            [
                _,
                _,
                _,
                business_value,
                table_purpose,
                key_characteristics,
                partition_information,
            ] = ai_table_descriptions_row

            # Add the AI table description to the custom properties
            custom_properties["business_value"] = business_value
            custom_properties["table_purpose"] = table_purpose
            custom_properties["key_characteristics"] = key_characteristics
            custom_properties["partition_information"] = partition_information

        return custom_properties

    def _extract_base64_data(self, view_text: str) -> Optional[str]:
        """
        Extract base64 data from Presto view text.

        HMS-specific feature for Presto views.

        Args:
            view_text: The view original text

        Returns:
            Base64 encoded data or None
        """
        pattern = r"/\* Presto View: (.*) \*/"
        match = re.search(pattern, view_text)
        if match:
            return match.group(1)
        else:
            return None

    def _get_top_tier_row(
        self, source_data_lake: str, source_schema_name: str, table_name: str
    ) -> Optional[Tuple]:
        """
        Get the top tier row for a given table from eg_top_tier_table.

        Args:
            source_data_lake: Source data lake
            source_schema_name: Source schema name
            table_name: Table name

        Returns:
            Row tuple or None
        """
        try:
            session = get_session()

            top_tier_rows = session.execute(
                """
                SELECT
                    source_data_lake,
                    source_schema_name,
                    table_name,
                    trending,
                    popularity,
                    importance_score
                FROM eg_top_tier_table
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

            return None

        except Exception as e:
            LOG.error(f"Error checking Top Tier status: {e}")
            return None

    def _get_ai_table_descriptions_row(
        self, source_data_lake: str, source_schema_name: str, table_name: str
    ) -> Optional[Tuple]:
        """
        Get AI-generated table descriptions from eg_table_descriptions_table.

        Args:
            source_data_lake: Source data lake
            source_schema_name: Source schema name
            table_name: Table name

        Returns:
            Row tuple or None
        """
        try:
            session = get_session()

            rows = session.execute(
                """
                SELECT
                    source_data_lake,
                    source_schema_name,
                    table_name,
                    business_value,
                    table_purpose,
                    key_characteristics,
                    partition_information
                FROM eg_table_descriptions_table
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

            if rows and len(rows) > 0:
                row = rows[0]
                LOG.debug(f"AI Table Descriptions {row}")
                return row

            return None

        except Exception as e:
            LOG.error(f"Error getting AI table descriptions: {e}")
            return None
