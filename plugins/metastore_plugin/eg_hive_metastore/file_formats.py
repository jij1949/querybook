from lib.logger import get_logger


LOG = get_logger(__file__)

# Generally, the serde is the more specific determinant of the file format,
# although there are some exceptions. As such, the mappings are ordered by
# specificity, with the most specific mappings at the top.
#
# The mappings are structured as a list of dictionaries, where each dictionary
# contains the following keys:
# - input_format: A list of input formats that the mapping applies to. The
#                 wildcard "*" can be used to match any input format.
# - serde: A list of serdes that the mapping applies to. The wildcard "*" can
#          be used to match any serde.
# - format: The determined file format.
#
# When matching against a table, the first mapping that matches both the input format and serde
# will be used to determine the file format.
#
# While technically any mapping with a "*" wildcard in the input_format or serde fields will match
# any value, common values are included in the list to make it easier to understand the mappings.
#
# Note: wildcard serdes should be placed at the bottom of the list since they are less specific
#
FILE_FORMAT_MAPPING = [
    {
        "input_format": [
            "org.apache.hadoop.hive.ql.io.avro.AvroContainerInputFormat",
            "*",
        ],
        "serde": ["org.apache.hadoop.hive.serde2.avro.AvroSerDe"],
        "format": "Avro",
    },
    {
        "input_format": ["org.apache.hadoop.mapred.TextInputFormat", "*"],
        "serde": [
            "com.bizo.hive.serde.csv.CSVSerde",
            "org.apache.hadoop.hive.serde2.OpenCSVSerde",
        ],
        "format": "CSV",
    },
    {
        "input_format": ["*"],
        "serde": [
            "com.willetinc.hive.mapreduce.dynamodb.HiveDynamoDBSerde",
            "org.apache.hadoop.hive.dynamodb.DynamoDBSerDe",
        ],
        "format": "DynamoDB",
    },
    {
        "input_format": ["*"],
        "serde": ["org.elasticsearch.hadoop.hive.EsSerDe"],
        "format": "Elasticsearch",
    },
    {
        "input_format": ["org.apache.iceberg.mr.hive.HiveIcebergInputFormat"],
        "serde": ["org.apache.iceberg.mr.hive.HiveIcebergSerDe"],
        "format": "Iceberg",
    },
    {
        "input_format": ["*"],
        "serde": ["org.apache.hadoop.hive.jdbc.storagehandler.JdbcSerDe"],
        "format": "JDBC",
    },
    {
        "input_format": [
            "org.apache.hadoop.mapred.TextInputFormat",
            "com.amazon.emr.cloudtrail.CloudTrailInputFormat",
            "*",
        ],
        "serde": [
            "com.expedia.edw.hive.serde.ExpJSONSerDe",
            "com.proofpoint.hive.serde.JsonSerde",
            "org.apache.hadoop.hive.contrib.serde2.JsonSerde",
            "org.apache.hive.hcatalog.data.JsonSerDe",
            "org.openx.data.jsonserde.JsonSerDe",
        ],
        "format": "JSON",
    },
    {
        "input_format": ["org.apache.hadoop.hive.ql.io.orc.OrcInputFormat"],
        "serde": ["org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe"],
        "format": "ORC",
    },
    {
        "input_format": [
            "org.apache.hadoop.hive.ql.io.orc.OrcInputFormat",
            "org.apache.hadoop.hive.ql.io.SymlinkTextInputFormat",
            "org.apache.hadoop.mapred.TextInputFormat",
            "*",
        ],
        "serde": ["org.apache.hadoop.hive.ql.io.orc.OrcSerde"],
        "format": "ORC",
    },
    {
        "input_format": [
            "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat",
            "org.apache.hudi.hadoop.HoodieParquetInputFormat",
            "*",
        ],
        "serde": ["org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"],
        "format": "Parquet",
    },
    {
        "input_format": ["org.apache.hadoop.hive.ql.io.RCFileInputFormat"],
        "serde": [
            "org.apache.hadoop.hive.serde2.columnar.ColumnarSerDe",
            "org.apache.hadoop.hive.serde2.columnar.LazyBinaryColumnarSerDe",
        ],
        "format": "RCFile",
    },
    # Wildcard sedres at the bottom to avoid matching with more specific mappings
    {
        "input_format": ["org.apache.hadoop.hive.ql.io.orc.OrcInputFormat"],
        "serde": ["*"],
        "format": "ORC",
    },
    {
        "input_format": [
            "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
        ],
        "serde": ["*"],
        "format": "Parquet",
    },
    {
        "input_format": ["org.apache.hadoop.mapred.SequenceFileInputFormat"],
        "serde": [
            "org.apache.hadoop.hive.contrib.serde2.MultiDelimitSerDe",
            "org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe",
            "org.apache.hadoop.hive.serde2.MetadataTypedColumnsetSerDe",
            "*",
        ],
        "format": "Sequence",
    },
    {
        "input_format": [
            "org.apache.hadoop.hive.ql.io.SymlinkTextInputFormat",
            "org.apache.hadoop.mapred.FileInputFormat",
            "org.apache.hadoop.mapred.TextInputFormat",
        ],
        "serde": [
            "org.apache.hadoop.hive.contrib.serde2.MultiDelimitSerDe",
            "org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe",
            "org.apache.hadoop.hive.serde2.RegexSerDe",
            "*",
        ],
        "format": "Text",
    },
]


def detect_file_format(sd, parameters):
    """
    Detects the file format of the table from the serde/input format.
    Check the serde first since it's more specific, then check the input format
    """
    if parameters.get("table_type", "").lower() == "iceberg":
        # Iceberg tables don't use the serde or input format fields
        if parameters.get("write.format.default"):
            write_format = parameters.get("write.format.default")
            return write_format.capitalize()
        else:
            # The default format for Iceberg tables is Parquet
            # https://iceberg.apache.org/docs/latest/configuration/#write-properties
            return "Parquet"

    if parameters.get("spark.sql.sources.provider", "") == "delta":
        # Delta tables are always in Parquet format
        return "Parquet"

    input_format = sd.inputFormat if sd.inputFormat else None
    serde = sd.serdeInfo.serializationLib if sd.serdeInfo else None

    # Search format_mapping where both input_format and serde match and return format
    # Both input_format and serde must match one of the values in the mapping
    # Some mappings include a wildcard "*" to match any input_format
    match = next(
        (
            item
            for item in FILE_FORMAT_MAPPING
            # if item["input_format"] == input_format and item["serde"] == serde
            if any(
                i_format == "*" or i_format == input_format
                for i_format in item["input_format"]
            )
            and any(s == "*" or s == serde for s in item["serde"])
        ),
        None,
    )

    if match:
        return match["format"]
    else:
        LOG.warn(f"No match for input_format: {input_format} and serde: {serde}")
        return "Unknown"
