import { useShallowSelector } from 'hooks/redux/useShallowSelector';
import { useMemo } from 'react';
import { IStoreState } from 'redux/store/types';

export function useExactMatchTableId() {
    const { dataTables, searchString, searchFilters } = useShallowSelector(
        (state: IStoreState) => ({
            dataTables: state.dataTableSearch.results,
            searchString: state.dataTableSearch.searchString,
            searchFilters: state.dataTableSearch.searchFilters,
        })
    );

    const [searchStringCatalog, searchStringSchema, searchStringTable] = useMemo(() => {
        const trimmedStr = searchString.trim();
        const separatedStrs = trimmedStr.split('.');

        if (separatedStrs.length === 1) {
            // Just table name: use filters for catalog and schema
            return [
                searchFilters.catalog,
                searchFilters.schema,
                separatedStrs[0]
            ];
        } else if (separatedStrs.length === 2) {
            // schema.table: use filter for catalog (if any)
            return [
                searchFilters.catalog,
                separatedStrs[0],
                separatedStrs[1]
            ];
        } else if (separatedStrs.length === 3) {
            // catalog.schema.table: full qualified name
            return [
                separatedStrs[0],
                separatedStrs[1],
                separatedStrs[2]
            ];
        }
        
        // Invalid format (more than 3 parts)
        return [null, null, null];
    }, [searchString, searchFilters]);

    const exactMatchTableId = useMemo(() => {
        if (!searchStringSchema || !searchStringTable) {
            return null;
        }

        return dataTables.find((table) => {
            const tableNameMatch = table.name.toLowerCase() === searchStringTable.toLowerCase();
            const schemaNameMatch = table.schema.toLowerCase() === searchStringSchema.toLowerCase();

            // If catalog filter is provided, it must match exactly
            // If no catalog filter is provided, ignore the table's catalog
            if (searchStringCatalog != null) {
                const catalogNameMatch = table.catalog?.toLowerCase() === searchStringCatalog.toLowerCase();
                return tableNameMatch && schemaNameMatch && catalogNameMatch;
            } else {
                // No catalog filter - match on table and schema only
                return tableNameMatch && schemaNameMatch;
            }
        })?.id;
    }, [searchStringCatalog, searchStringSchema, searchStringTable, dataTables]);

    return exactMatchTableId;
}
