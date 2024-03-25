from lib.logger import get_logger


LOG = get_logger(__file__)

FILE_FORMAT_MAPPING = [
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
        "input_format": [
            "org.apache.hadoop.hive.ql.io.orc.OrcInputFormat",
            "org.apache.hadoop.hive.ql.io.SymlinkTextInputFormat",
            "*",
        ],
        "serde": ["org.apache.hadoop.hive.ql.io.orc.OrcSerde"],
        "format": "ORC",
    },
    {
        "input_format": ["org.apache.hadoop.mapred.SequenceFileInputFormat"],
        "serde": ["org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe"],
        "format": "Sequence",
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
        "input_format": [
            "org.apache.hadoop.mapred.TextInputFormat",
            "com.amazon.emr.cloudtrail.CloudTrailInputFormat",
            "*",
        ],
        "serde": [
            "org.openx.data.jsonserde.JsonSerDe",
            "org.apache.hadoop.hive.contrib.serde2.JsonSerde",
        ],
        "format": "JSON",
    },
    {
        "input_format": ["org.apache.hadoop.hive.ql.io.avro.AvroContainerInputFormat"],
        "serde": ["org.apache.hadoop.hive.serde2.avro.AvroSerDe"],
        "format": "Avro",
    },
    {
        "input_format": [
            "org.apache.hadoop.mapred.TextInputFormat",
            "org.apache.hadoop.mapred.FileInputFormat",
        ],
        "serde": ["org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe"],
        "format": "Text",
    },
    {
        "input_format": ["org.apache.hadoop.hive.ql.io.RCFileInputFormat"],
        "serde": ["org.apache.hadoop.hive.serde2.columnar.ColumnarSerDe"],
        "format": "RCFile",
    },
    {
        "input_format": ["*"],
        "serde": ["org.apache.hadoop.hive.jdbc.storagehandler.JdbcSerDe"],
        "format": "JDBC",
    },
    {
        "input_format": ["*"],
        "serde": ["org.elasticsearch.hadoop.hive.EsSerDe"],
        "format": "Elasticsearch",
    },
    {
        "input_format": ["*"],
        "serde": ["com.willetinc.hive.mapreduce.dynamodb.HiveDynamoDBSerde"],
        "format": "DynamoDB",
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
            and any(s == serde for s in item["serde"])
        ),
        None,
    )

    if match:
        return match["format"]
    else:
        LOG.warn(f"No match for input_format: {input_format} and serde: {serde}")
        return "Unknown File Format"
