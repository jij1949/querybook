import { ILinterWarning, TableToken } from './sql-lexer';

import { DataTableWarningSeverity } from 'const/metastore';
import {
    getLegacyPrefixedSchemaName,
    getTableTokenDisplayName,
} from 'lib/utils/table-identifier';
import { reduxStore } from 'redux/store';

export function getContextSensitiveWarnings(
    metastoreId: number,
    tableReferences: TableToken[],
    ignoreTableNotExistWarnings: boolean,
    showCatalog: boolean
) {
    const contextSensitiveWarnings: ILinterWarning[] = [];

    const { dataTableNameToId, dataTablesById, dataTableWarningById } =
        reduxStore.getState().dataSources;
    const nameToId = dataTableNameToId[metastoreId] || {};
    for (const table of tableReferences) {
        const implicitSchema = table.end - table.start === table.name.length;
        // Build fullName with catalog if present
        const fullName = getTableTokenDisplayName(table, showCatalog);
        // Mid-migration fallback: a catalog-qualified reference
        // (catalog.schema.table) may still be indexed under its legacy prefixed
        // name (catalog_schema.table). Resolve against that too so tables that
        // only exist in the pre-catalog form aren't flagged as "not found".
        const legacySchema = getLegacyPrefixedSchemaName(
            table.catalog,
            table.schema
        );
        const legacyName = legacySchema
            ? getTableTokenDisplayName({
                  schema: legacySchema,
                  name: table.name,
              })
            : null;
        const resolvedName =
            fullName in nameToId
                ? fullName
                : legacyName && legacyName in nameToId
                ? legacyName
                : null;

        if (resolvedName === null) {
            if (!ignoreTableNotExistWarnings) {
                contextSensitiveWarnings.push({
                    message: `Table ${table.name} is newly created or does not exist`,
                    severity: 'warning',
                    type: 'lint',
                    from: {
                        line: table.line,
                        ch: implicitSchema
                            ? table.start
                            : table.start + table.schema.length + 1,
                    },
                    to: {
                        line: table.line,
                        ch: table.end,
                    },
                    suggestion: null,
                });
            }
        } else {
            const tableId = nameToId[resolvedName];
            const dataTable = dataTablesById[tableId];
            if (dataTable.warnings?.length) {
                const tableWarnings = dataTable.warnings.map(
                    (id) => dataTableWarningById[id]
                );
                const warningMessage = tableWarnings
                    .map(
                        (warning) =>
                            (warning.severity === DataTableWarningSeverity.ERROR
                                ? 'ERROR:'
                                : 'WARN:') + warning.message
                    )
                    .join('\n');
                const maxSeverity: DataTableWarningSeverity = Math.max(
                    ...tableWarnings.map((warning) => warning.severity)
                );

                contextSensitiveWarnings.push({
                    message: warningMessage,
                    type: 'lint',
                    severity:
                        maxSeverity === DataTableWarningSeverity.ERROR
                            ? 'error'
                            : 'warning',
                    from: {
                        line: table.line,
                        ch: implicitSchema
                            ? table.start
                            : table.start + table.schema.length + 1,
                    },
                    to: {
                        line: table.line,
                        ch: table.end,
                    },
                    suggestion: null,
                });
            }
        }
    }

    return contextSensitiveWarnings;
}
