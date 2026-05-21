import { searchCatalogs, searchSchemasByCatalog, changeCatalogsSort } from 'redux/dataTableSearch/action';
import { SearchCatalogResource, SearchSchemaResource } from 'resource/search';

jest.mock('resource/search', () => ({
    SearchCatalogResource: {
        getMore: jest.fn(),
    },
    SearchSchemaResource: {
        getMore: jest.fn(),
    },
    SearchTableResource: {
        searchConcise: jest.fn(),
    },
}));

describe('searchCatalogs', () => {
    let mockDispatch: jest.Mock;
    let mockGetState: jest.Mock;

    beforeEach(() => {
        mockDispatch = jest.fn();
        mockGetState = jest.fn();
        jest.clearAllMocks();
    });

    const baseState = () => ({
        dataTableSearch: {
            metastoreId: 1,
            catalogs: {
                catalogIds: [],
                catalogResultById: {},
                catalogSchemaSortByIds: {},
                sortCatalogsBy: { asc: true, key: 'name' },
                done: false,
            },
            schemas: { schemaIds: [], schemaResultById: {}, schemaSortByIds: {}, sortSchemasBy: { asc: true, key: 'name' }, done: false },
            results: [], count: 0, searchString: '', searchFilters: {},
            searchFields: { table_name: true }, searchRequest: null,
            sortTablesBy: { asc: true, key: 'relevance' },
        },
    });

    it('dispatches CATALOG_SEARCH_DONE with results', async () => {
        mockGetState.mockReturnValue(baseState());
        (SearchCatalogResource.getMore as jest.Mock).mockResolvedValue({
            data: { results: [{ id: 1, name: 'cat_a', schema_count: 2 }], done: true },
        });

        const thunk = searchCatalogs();
        await thunk(mockDispatch, mockGetState, undefined);

        expect(mockDispatch).toHaveBeenCalledWith({
            type: '@@dataTableSearch/CATALOG_SEARCH_DONE',
            payload: {
                results: [{ id: 1, name: 'cat_a', schema_count: 2 }],
                done: true,
            },
        });
    });

    it('does not fetch when catalogs.done is true', async () => {
        const state = baseState();
        state.dataTableSearch.catalogs.done = true;
        mockGetState.mockReturnValue(state);

        const thunk = searchCatalogs();
        await thunk(mockDispatch, mockGetState, undefined);

        expect(SearchCatalogResource.getMore).not.toHaveBeenCalled();
    });
});

describe('searchSchemasByCatalog', () => {
    let mockDispatch: jest.Mock;
    let mockGetState: jest.Mock;

    beforeEach(() => {
        mockDispatch = jest.fn();
        mockGetState = jest.fn();
        jest.clearAllMocks();
    });

    const stateWithCatalog = (catalogId: number, schemasLoaded = 0, schemaCount = 5) => ({
        dataTableSearch: {
            metastoreId: 1,
            catalogs: {
                catalogIds: [catalogId],
                catalogResultById: {
                    [catalogId]: {
                        id: catalogId,
                        name: 'cat_a',
                        schema_count: schemaCount,
                        schemas: Array(schemasLoaded).fill({}),
                        schemasDone: schemasLoaded >= schemaCount,
                    },
                },
                catalogSchemaSortByIds: {},
                sortCatalogsBy: { asc: true, key: 'name' },
                done: false,
            },
            schemas: { schemaIds: [], schemaResultById: {}, schemaSortByIds: {}, sortSchemasBy: { asc: true, key: 'name' }, done: false },
            results: [], count: 0, searchString: '', searchFilters: {},
            searchFields: { table_name: true }, searchRequest: null,
            sortTablesBy: { asc: true, key: 'relevance' },
        },
    });

    it('dispatches SEARCH_SCHEMA_BY_CATALOG_DONE on success', async () => {
        const catalogId = 7;
        mockGetState.mockReturnValue(stateWithCatalog(catalogId, 0, 3));
        (SearchSchemaResource.getMore as jest.Mock).mockResolvedValue({
            data: {
                results: [{ id: 10, name: 'schema_a', metastore_id: 1, table_count: 2 }],
                done: false,
            },
        });

        const thunk = searchSchemasByCatalog(catalogId);
        await thunk(mockDispatch, mockGetState, undefined);

        expect(mockDispatch).toHaveBeenCalledWith({
            type: '@@dataTableSearch/SEARCH_SCHEMA_BY_CATALOG_DONE',
            payload: expect.objectContaining({
                catalogId,
                results: expect.arrayContaining([expect.objectContaining({ name: 'schema_a' })]),
            }),
        });
    });

    it('does not fetch when catalog schemas are fully loaded (schemasDone is true)', async () => {
        const catalogId = 8;
        mockGetState.mockReturnValue(stateWithCatalog(catalogId, 5, 5));

        const thunk = searchSchemasByCatalog(catalogId);
        await thunk(mockDispatch, mockGetState, undefined);

        expect(SearchSchemaResource.getMore).not.toHaveBeenCalled();
    });
});
