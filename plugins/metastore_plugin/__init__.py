from metastore_plugin.eg_hive_metastore.eg_hive_metastore_loader import (
    EgHMSMetastoreLoader,
)
from metastore_plugin.eg_databricks.eg_databricks_metastore_loader import (
    EgDatabricksMetastoreLoader,
)
from metastore_plugin.eg_glue.eg_glue_metastore_loader import (
    EgGlueMetastoreLoader,
)


ALL_PLUGIN_METASTORE_LOADERS = [
    EgHMSMetastoreLoader,
    EgDatabricksMetastoreLoader,
    EgGlueMetastoreLoader,
]
