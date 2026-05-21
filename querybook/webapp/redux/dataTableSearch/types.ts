import { Action } from 'redux';
import { ThunkAction } from 'redux-thunk';

import {
    IDataSchema,
    SchemaSortKey,
    SchemaTableSortKey,
    CatalogSortKey,
    ICatalogSearchResult,
} from 'const/metastore';
import { ICancelablePromise } from 'lib/datasource';

import { IStoreState } from '../store/types';

export interface ITableSearchResult {
    id: number;
    schema: string;
    name: string;
    catalog?: string;
    full_name?: string;
    golden?: boolean;
    tags: string[];
}

export interface ICatalogSearchState extends ICatalogSearchResult {
    schemasDone: boolean;
    schemasLoading: boolean;
}

export interface ITableSearchFilters {
    golden?: true;
    tags?: string[];
    startDate?: number;
    endDate?: number;
    catalog?: string;
    schema?: string;
    data_elements?: string[];
}

export interface ISchemaTableSearch extends IDataSchema {
    tables?: ITableSearchResult[];
    count?: number;
}

export interface IDataTableSearchResultResetAction extends Action {
    type: '@@dataTableSearch/DATA_TABLE_SEARCH_RESULT_RESET';
}

export interface IDataTableSearchResultClearAction extends Action {
    type: '@@dataTableSearch/DATA_TABLE_SEARCH_RESET';
}

export interface IDataTableSearchStartedAction extends Action {
    type: '@@dataTableSearch/DATA_TABLE_SEARCH_STARTED';
    payload: {
        searchRequest: Promise<any>;
    };
}

export interface IDataTableSearchDoneAction extends Action {
    type: '@@dataTableSearch/DATA_TABLE_SEARCH_DONE';
    payload: {
        results: ITableSearchResult[];
        count: number;
    };
}

export interface IDataTableSearchFailedAction extends Action {
    type: '@@dataTableSearch/DATA_TABLE_SEARCH_FAILED';
    payload: {
        error: any;
    };
}

export interface IDataTableSearchStringUpdateAction extends Action {
    type: '@@dataTableSearch/DATA_TABLE_SEARCH_STRING_UPDATE';
    payload: {
        searchString: string;
    };
}

export interface IDataTableSearchSortUpdateAction extends Action {
    type: '@@dataTableSearch/DATA_TABLE_SEARCH_SORT_UPDATE';
    payload: {
        sortTablesBy: {
            sortKey?: SchemaTableSortKey | undefined;
            sortAsc?: boolean | undefined;
        };
    };
}

export interface IDataTableSearchSelectMetastoreAction extends Action {
    type: '@@dataTableSearch/DATA_TABLE_SEARCH_SELECT_METASTORE';
    payload: {
        metastoreId: number;
    };
}

export interface IDataTableSearchFilterUpdateAction extends Action {
    type: '@@dataTableSearch/DATA_TABLE_SEARCH_FILTER_UPDATE';
    payload: {
        filterKey: string;
        filterValue: any;
    };
}

export interface IDataTableSearchResetFilterAction extends Action {
    type: '@@dataTableSearch/DATA_TABLE_FILTER_RESET';
}

export interface IDataTableSearchMoreAction extends Action {
    type: '@@dataTableSearch/DATA_TABLE_SEARCH_MORE';
    payload: {
        results: ITableSearchResult[];
    };
}

export interface ISchemaSearchMoreAction extends Action {
    type: '@@dataTableSearch/SCHEMA_SEARCH_STARTED';
}

export interface ISchemaSearchResultAction extends Action {
    type: '@@dataTableSearch/SCHEMA_SEARCH_DONE';
    payload: {
        results: IDataSchema[];
        done: boolean;
    };
}

export interface ISchemaSearchFailedAction extends Action {
    type: '@@dataTableSearch/SCHEMA_SEARCH_FAILED';
    payload: {
        error: any;
    };
}

export interface ISearchTableBySchemaAction extends Action {
    type: '@@dataTableSearch/SEARCH_TABLE_BY_SCHEMA_STARTED';
}

export interface ISearchTableBySchemaResultAction extends Action {
    type: '@@dataTableSearch/SEARCH_TABLE_BY_SCHEMA_DONE';
    payload: {
        results: ITableSearchResult[];
        id: number;
        count: number;
    };
}

export interface ISearchTableBySchemaFailedAction extends Action {
    type: '@@dataTableSearch/SEARCH_TABLE_BY_SCHEMA_FAILED';
    payload: {
        error: any;
    };
}

export interface ISchemaTableSortChangedAction extends Action {
    type: '@@dataTableSearch/SEARCH_TABLE_BY_SORT_CHANGED';
    payload: {
        id: number;

        sortKey?: SchemaTableSortKey | undefined;
        sortAsc?: boolean | undefined;
    };
}

export interface ISchemasSortChangedAction extends Action {
    type: '@@dataTableSearch/SCHEMAS_SORT_CHANGED';
    payload: {
        sortKey?: SchemaSortKey | undefined;
        sortAsc?: boolean | undefined;
    };
}

export interface ICatalogSearchStartedAction extends Action {
    type: '@@dataTableSearch/CATALOG_SEARCH_STARTED';
}

export interface ICatalogSearchDoneAction extends Action {
    type: '@@dataTableSearch/CATALOG_SEARCH_DONE';
    payload: {
        results: ICatalogSearchResult[];
        done: boolean;
    };
}

export interface ICatalogSearchFailedAction extends Action {
    type: '@@dataTableSearch/CATALOG_SEARCH_FAILED';
    payload: {
        error: any;
    };
}

export interface ISearchSchemaByCatalogStartedAction extends Action {
    type: '@@dataTableSearch/SEARCH_SCHEMA_BY_CATALOG_STARTED';
    payload: {
        catalogId: number;
    };
}

export interface ISearchSchemaByCatalogDoneAction extends Action {
    type: '@@dataTableSearch/SEARCH_SCHEMA_BY_CATALOG_DONE';
    payload: {
        results: IDataSchema[];
        catalogId: number;
        done: boolean;
    };
}

export interface ISearchSchemaByCatalogFailedAction extends Action {
    type: '@@dataTableSearch/SEARCH_SCHEMA_BY_CATALOG_FAILED';
    payload: {
        catalogId: number;
        error: any;
    };
}

export interface ICatalogsSortChangedAction extends Action {
    type: '@@dataTableSearch/CATALOGS_SORT_CHANGED';
    payload: {
        sortKey?: CatalogSortKey;
        sortAsc?: boolean;
    };
}

export interface ICatalogSchemaSortChangedAction extends Action {
    type: '@@dataTableSearch/CATALOG_SCHEMA_SORT_CHANGED';
    payload: {
        catalogId: number;
        sortKey?: SchemaSortKey;
        sortAsc?: boolean;
    };
}

export type DataTableSearchAction =
    | IDataTableSearchResultResetAction
    | IDataTableSearchResultClearAction
    | IDataTableSearchStartedAction
    | IDataTableSearchDoneAction
    | IDataTableSearchFailedAction
    | IDataTableSearchStringUpdateAction
    | IDataTableSearchSortUpdateAction
    | IDataTableSearchFilterUpdateAction
    | IDataTableSearchResetFilterAction
    | IDataTableSearchMoreAction
    | IDataTableSearchSelectMetastoreAction
    | ISchemaSearchMoreAction
    | ISchemaSearchResultAction
    | ISearchTableBySchemaAction
    | ISearchTableBySchemaResultAction
    | ISchemaSearchFailedAction
    | ISearchTableBySchemaFailedAction
    | ISchemaTableSortChangedAction
    | ISchemasSortChangedAction
    | ICatalogSearchStartedAction
    | ICatalogSearchDoneAction
    | ICatalogSearchFailedAction
    | ISearchSchemaByCatalogStartedAction
    | ISearchSchemaByCatalogDoneAction
    | ISearchSchemaByCatalogFailedAction
    | ICatalogsSortChangedAction
    | ICatalogSchemaSortChangedAction;

export interface IDataTableSearchPaginationState {
    results: ITableSearchResult[];
    count: number;
    schemas: {
        done: boolean;

        schemaResultById: Record<number, ISchemaTableSearch>;
        schemaIds: number[];
        schemaSortByIds: Record<
            number,
            { asc: boolean; key: SchemaTableSortKey }
        >;
        sortSchemasBy: {
            asc: boolean;
            key: SchemaSortKey;
        };
    };
    catalogs: {
        done: boolean;
        catalogIds: number[];
        catalogResultById: Record<number, ICatalogSearchState>;
        catalogSchemaSortByIds: Record<number, { asc: boolean; key: SchemaSortKey }>;
        sortCatalogsBy: {
            asc: boolean;
            key: CatalogSortKey;
        };
    };
}

export interface IDataTableSearchState extends IDataTableSearchPaginationState {
    searchFilters: ITableSearchFilters;
    searchFields: Partial<
        Record<'table_name' | 'description' | 'column', boolean>
    >;
    searchString: string;
    searchRequest?: ICancelablePromise<any>;
    metastoreId?: number;
    sortTablesBy: {
        asc: boolean;
        key: SchemaTableSortKey;
    };
}

export type ThunkResult<R> = ThunkAction<
    R,
    IStoreState,
    undefined,
    DataTableSearchAction
>;
