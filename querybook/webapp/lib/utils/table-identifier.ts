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
    showCatalog: boolean = false
): string {
    if (schema.catalog && showCatalog) {
        return `${schema.catalog.name}.${schema.name}`;
    }
    return schema.name;
}

/**
 * Builds the legacy prefixed schema name for a catalog-qualified reference.
 *
 * During the Glue three-level-catalog migration, a schema that a user now
 * writes as `catalog.schema` (e.g. `egdp_analytics.plat_metrics`) may still be
 * indexed in Querybook under its pre-catalog two-level name, with the catalog
 * folded into the schema prefix (`egdp_analytics_plat_metrics`). This collapses
 * the two parts into that legacy schema name.
 *
 * @returns The legacy `catalog_schema` name, or null when there is no catalog.
 */
export function getLegacyPrefixedSchemaName(
    catalog: string | null | undefined,
    schema: string
): string | null {
    if (!catalog) {
        return null;
    }
    return `${catalog}_${schema}`;
}

/**
 * Resolves a table via `fetch`, falling back to the legacy prefixed schema name
 * when the canonical lookup misses.
 *
 * During the Glue three-level-catalog migration a catalog-qualified reference
 * (`catalog.schema.table`) may still be indexed under its legacy prefixed name
 * (`catalog_schema.table`). This runs the canonical lookup first and, only when
 * it returns nothing, retries against the collapsed legacy schema (see
 * {@link getLegacyPrefixedSchemaName}). Centralizing the fallback keeps every
 * editor path (prefetch, hover tooltip, "open table") in sync, so the rule only
 * ever has to change in one place.
 *
 * @param fetch - Looks up a table by (schema, name[, catalog]). The catalog is
 * only passed on the canonical attempt, never on the collapsed legacy retry.
 * May be undefined (e.g. the editor has no engine/metastore), in which case
 * this resolves to undefined without attempting a lookup.
 * @param catalog - The reference's catalog, if any.
 * @param schema - The reference's schema.
 * @param name - The table name.
 * @returns The resolved table, or the canonical (falsy) result when neither hits.
 */
export async function resolveTableWithLegacyFallback<T>(
    fetch:
        | ((
              schema: string,
              name: string,
              catalog?: string | null
          ) => T | Promise<T>)
        | undefined
        | null,
    catalog: string | null | undefined,
    schema: string,
    name: string
): Promise<T | undefined> {
    if (!fetch) {
        return undefined;
    }
    const table = await fetch(schema, name, catalog);
    if (table) {
        return table;
    }
    const legacySchema = getLegacyPrefixedSchemaName(catalog, schema);
    if (legacySchema) {
        return fetch(legacySchema, name);
    }
    return table;
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
    showCatalog: boolean = false
): string {
    if (table.catalog && showCatalog) {
        return `${table.catalog}.${table.schema}.${table.name}`;
    }
    return `${table.schema}.${table.name}`;
}
