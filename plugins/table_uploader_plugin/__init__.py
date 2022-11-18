from table_uploader_plugin.trino_exporter import TrinoExporter
from table_uploader_plugin.trino_bulk_exporter import TrinoBulkExporter

# Must be Dict[str, BaseTableUploadExporter]
ALL_PLUGIN_TABLE_UPLOAD_EXPORTERS = {
    "TrinoExporter": TrinoExporter(),
    "TrinoBulkExporter": TrinoBulkExporter()
}
