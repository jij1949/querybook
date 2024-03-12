from lib.logger import get_logger


LOG = get_logger(__file__)

FILE_FORMAT_MAPPING = [
    {
        "input_format": "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat",
        "serde": "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe",
        "format": "Parquet",
    },
    {
        "input_format": "org.apache.hadoop.hive.ql.io.orc.OrcInputFormat",
        "serde": "org.apache.hadoop.hive.ql.io.orc.OrcSerde",
        "format": "ORC",
    },
    {
        "input_format": "org.apache.hadoop.mapred.SequenceFileInputFormat",
        "serde": "org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe",
        "format": "Sequence",
    },
    {
        "input_format": "org.apache.hadoop.mapred.TextInputFormat",
        "serde": "org.apache.hadoop.hive.serde2.OpenCSVSerde",
        "format": "CSV",
    },
    {
        "input_format": "org.apache.hadoop.mapred.TextInputFormat",
        "serde": "org.openx.data.jsonserde.JsonSerDe",
        "format": "JSON",
    },
    {
        "input_format": "org.apache.hadoop.hive.ql.io.avro.AvroContainerInputFormat",
        "serde": "org.apache.hadoop.hive.serde2.avro.AvroSerDe",
        "format": "Avro",
    },
    {
        # Text format, fields are separated by a delimiter
        "input_format": "org.apache.hadoop.mapred.TextInputFormat",
        "serde": "org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe",
        "format": "Text",
    },
    {
        "input_format": "org.apache.hadoop.mapred.FileInputFormat",
        "serde": "org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe",
        "format": "Text",
    },
    {
        "input_format": "org.apache.hadoop.hive.ql.io.RCFileInputFormat",
        "serde": "org.apache.hadoop.hive.serde2.columnar.ColumnarSerDe",
        "format": "RCFile",
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
    match = next(
        (
            item
            for item in FILE_FORMAT_MAPPING
            if item["input_format"] == input_format and item["serde"] == serde
        ),
        None,
    )

    if match:
        return match["format"]
    else:
        LOG.warn(f"No match for input_format: {input_format} and serde: {serde}")
        return "Unknown File Format"
