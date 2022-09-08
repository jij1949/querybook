from table_uploader_plugin.trino_exporter import TrinoExporter

# Must be Dict[str, BaseTableUploadExporter]
ALL_PLUGIN_TABLE_UPLOAD_EXPORTERS = {"TrinoExporter": TrinoExporter}
