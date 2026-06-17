export type CatalogType = 'glue' | 'databricks' | 'unknown';

export interface CatalogTypeInput {
    // Direct catalog_type value from custom_properties or tag meta.
    catalogType?: string;
}

// Maps stored catalog_type values to CatalogType. Handles both current ("glue") and
// legacy ("aws_glue") values that may exist in custom_properties before this change.
const CATALOG_TYPE_VALUE_MAP: Record<string, CatalogType> = {
    databricks: 'databricks',
    glue: 'glue',
    aws_glue: 'glue',
};

export function getCatalogType(input: CatalogTypeInput): CatalogType {
    const { catalogType } = input;
    if (catalogType) {
        const mapped = CATALOG_TYPE_VALUE_MAP[catalogType.toLowerCase()];
        if (mapped) return mapped;
    }
    return 'unknown';
}
