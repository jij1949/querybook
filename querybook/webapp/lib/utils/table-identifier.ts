/**
 * Get the display name for a table based on metastore settings.
 * This function respects the metastore's catalog display settings:
 * - If full_name is provided, uses that
 * - Otherwise falls back to the full table name (schema.name or catalog.schema.name)
 *
 * @param table - Object containing table information with required schema and name properties,
 * and optional full_name and catalog properties
 * @returns The formatted table display name
 */
export function getTableDisplayName(table: {
    full_name?: string;
    catalog?: string;
    schema: string;
    name: string;
}): string {
    // If full_name is already computed by the backend, use it
    if (table.full_name) {
        return table.full_name;
    }

    // Fallback: construct the full name
    if (table.catalog) {
        return `${table.catalog}.${table.schema}.${table.name}`;
    }
    return `${table.schema}.${table.name}`;
}

/**
 * Get the display name for a schema, optionally including catalog information.
 * Used in SchemaTableView to format schema dropdown headers.
 *
 * @param schema - Schema object with name and optional catalog
 * @param showCatalog - Whether to show catalog in the display name (from metastore settings)
 * @returns The formatted schema display name (e.g., "catalog.schema" or "schema")
 */
export function getSchemaDisplayName(
    schema: {
        name: string;
        catalog?: {
            name: string;
        };
    },
    showCatalog: boolean = false,
): string {
    if (schema.catalog && showCatalog) {
        return `${schema.catalog.name}.${schema.name}`;
    }
    return schema.name;
}

/**
 * Constructs a display name for a TableToken from SQL parsing.
 * TableToken objects come from client-side SQL parsing and have no backend context,
 * so this function simply formats the raw components.
 * Handles 2-part (schema.table) and 3-part (catalog.schema.table) identifiers.
 *
 * @param table - TableToken or object with catalog (optional), schema, and name properties
 * @param showCatalog - Whether to include catalog in the display name (default: false)
 * @returns Formatted table identifier string
 */
export function getTableTokenDisplayName(
    table: {
        catalog?: string | null;
        schema: string;
        name: string;
    },
    showCatalog: boolean = false,
): string {
    if (table.catalog && showCatalog) {
        return `${table.catalog}.${table.schema}.${table.name}`;
    }
    return `${table.schema}.${table.name}`;
}
