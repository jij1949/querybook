"""
EG-specific AWS Glue Data Catalog metastore loader.

Extends GlueDataCatalogLoader with Expedia Group-specific enrichment features:
- Governance tags (eg-owner, eg-creator, eg-brand, etc.)
- File format detection and warnings
- Table format detection (Iceberg, Delta Lake, Hudi)
- Sensitivity tags and data elements (column-level classification)
- Source data lake determination (catalog-aware)
- Top tier/trending table support
- AI-generated table descriptions
- Cloverleaf tagging
"""
