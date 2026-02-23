import { searchTableBySchema } from 'redux/dataTableSearch/action';
import { SearchTableResource } from 'resource/search';

// Mock the SearchTableResource
jest.mock('resource/search', () => ({
    SearchTableResource: {
        searchConcise: jest.fn(),
    },
}));

describe('searchTableBySchema', () => {
    let mockDispatch: jest.Mock;
    let mockGetState: jest.Mock;
    let mockSearchConcise: jest.Mock;

    beforeEach(() => {
        mockDispatch = jest.fn();
        mockGetState = jest.fn();
        mockSearchConcise = SearchTableResource.searchConcise as jest.Mock;

        // Reset mocks
        jest.clearAllMocks();
    });

    const createMockState = (
        schemaId: number,
        resultsCount: number = 0,
        totalCount: number = 10
    ) => ({
        dataTableSearch: {
            metastoreId: 1,
            searchString: '',
            searchFilters: {
                golden: true,
            },
            searchFields: { name: true, description: true },
            sortTablesBy: { key: 'name', asc: true },
            schemas: {
                schemaResultById: {
                    [schemaId]: {
                        id: schemaId,
                        name: 'test_schema',
                        tables: Array(resultsCount).fill({}),
                        count: totalCount,
                    },
                },
                schemaSortByIds: {},
            },
        },
    });

    it('should include catalog in search filters when catalogName is provided', async () => {
        const schemaId = 1;
        mockGetState.mockReturnValue(createMockState(schemaId, 0, 10));
        mockSearchConcise.mockResolvedValue({
            data: { results: [], count: 0 },
        });

        const thunk = searchTableBySchema(
            'information_schema',
            schemaId,
            'catalog1'
        );
        await thunk(mockDispatch, mockGetState, undefined);

        expect(mockSearchConcise).toHaveBeenCalledWith(
            expect.objectContaining({
                filters: expect.arrayContaining([
                    ['schema', 'information_schema'],
                    ['catalog', 'catalog1'],
                ]),
            })
        );
    });

    it('should not include catalog filter when catalogName is undefined', async () => {
        const schemaId = 1;
        mockGetState.mockReturnValue(createMockState(schemaId, 0, 10));
        mockSearchConcise.mockResolvedValue({
            data: { results: [], count: 0 },
        });

        const thunk = searchTableBySchema(
            'default',
            schemaId,
            undefined // No catalog provided
        );
        await thunk(mockDispatch, mockGetState, undefined);

        const callArgs = mockSearchConcise.mock.calls[0][0];
        const filters = callArgs.filters;

        // Should have schema filter but not catalog filter
        expect(filters).toContainEqual(['schema', 'default']);
        expect(filters).not.toContainEqual(
            expect.arrayContaining(['catalog', expect.anything()])
        );
    });

    it('should work without catalog parameter for backward compatibility', async () => {
        const schemaId = 2;
        mockGetState.mockReturnValue(createMockState(schemaId, 0, 10));
        mockSearchConcise.mockResolvedValue({
            data: { results: [], count: 0 },
        });

        // Call without catalog parameter (backward compatibility)
        const thunk = searchTableBySchema('my_schema', schemaId);
        await thunk(mockDispatch, mockGetState, undefined);

        expect(mockSearchConcise).toHaveBeenCalled();

        const callArgs = mockSearchConcise.mock.calls[0][0];
        const filters = callArgs.filters;

        // Should work without errors and include schema filter
        expect(filters).toContainEqual(['schema', 'my_schema']);
    });

    it('should not make a request if results count equals total count', async () => {
        const schemaId = 3;
        // resultsCount = totalCount (10 == 10)
        mockGetState.mockReturnValue(createMockState(schemaId, 10, 10));

        const thunk = searchTableBySchema(
            'full_schema',
            schemaId,
            'catalog1'
        );
        await thunk(mockDispatch, mockGetState, undefined);

        // Should not call searchConcise when all results are loaded
        expect(mockSearchConcise).not.toHaveBeenCalled();
    });

    it('should include offset in request for pagination', async () => {
        const schemaId = 4;
        mockGetState.mockReturnValue(createMockState(schemaId, 5, 20));
        mockSearchConcise.mockResolvedValue({
            data: { results: [], count: 20 },
        });

        const thunk = searchTableBySchema(
            'paginated_schema',
            schemaId,
            'catalog2'
        );
        await thunk(mockDispatch, mockGetState, undefined);

        expect(mockSearchConcise).toHaveBeenCalledWith(
            expect.objectContaining({
                offset: 5, // Should use resultsCount as offset
            })
        );
    });

    it('should dispatch SEARCH_TABLE_BY_SCHEMA_STARTED action', async () => {
        const schemaId = 5;
        mockGetState.mockReturnValue(createMockState(schemaId, 0, 10));
        mockSearchConcise.mockResolvedValue({
            data: { results: [{ id: 1, name: 'table1' }], count: 1 },
        });

        const thunk = searchTableBySchema('schema', schemaId, 'catalog');
        await thunk(mockDispatch, mockGetState, undefined);

        expect(mockDispatch).toHaveBeenCalledWith({
            type: '@@dataTableSearch/SEARCH_TABLE_BY_SCHEMA_STARTED',
        });
    });

    it('should dispatch SEARCH_TABLE_BY_SCHEMA_DONE action with results', async () => {
        const schemaId = 6;
        const mockResults = [
            { id: 1, name: 'table1' },
            { id: 2, name: 'table2' },
        ];
        mockGetState.mockReturnValue(createMockState(schemaId, 0, 10));
        mockSearchConcise.mockResolvedValue({
            data: { results: mockResults, count: 2 },
        });

        const thunk = searchTableBySchema('schema', schemaId, 'catalog');
        await thunk(mockDispatch, mockGetState, undefined);

        expect(mockDispatch).toHaveBeenCalledWith({
            type: '@@dataTableSearch/SEARCH_TABLE_BY_SCHEMA_DONE',
            payload: {
                results: mockResults,
                count: 2,
                id: schemaId,
            },
        });
    });

    it('should handle multi-catalog scenario correctly', async () => {
        const schemaId = 7;
        mockGetState.mockReturnValue(createMockState(schemaId, 0, 10));
        mockSearchConcise.mockResolvedValue({
            data: { results: [], count: 0 },
        });

        // Test with catalog1
        const thunk1 = searchTableBySchema(
            'information_schema',
            schemaId,
            'catalog1'
        );
        await thunk1(mockDispatch, mockGetState, undefined);

        expect(mockSearchConcise).toHaveBeenLastCalledWith(
            expect.objectContaining({
                filters: expect.arrayContaining([['catalog', 'catalog1']]),
            })
        );

        jest.clearAllMocks();

        // Test with catalog2 - should filter by different catalog
        const thunk2 = searchTableBySchema(
            'information_schema',
            schemaId,
            'catalog2'
        );
        await thunk2(mockDispatch, mockGetState, undefined);

        expect(mockSearchConcise).toHaveBeenLastCalledWith(
            expect.objectContaining({
                filters: expect.arrayContaining([['catalog', 'catalog2']]),
            })
        );
    });

    it('should preserve other search filters when adding catalog', async () => {
        const schemaId = 8;
        const stateWithFilters = {
            dataTableSearch: {
                ...createMockState(schemaId, 0, 10).dataTableSearch,
                searchFilters: {
                    golden: true,
                    tags: ['important'],
                    startDate: 1234567890,
                },
            },
        };
        mockGetState.mockReturnValue(stateWithFilters);
        mockSearchConcise.mockResolvedValue({
            data: { results: [], count: 0 },
        });

        const thunk = searchTableBySchema('schema', schemaId, 'catalog1');
        await thunk(mockDispatch, mockGetState, undefined);

        const callArgs = mockSearchConcise.mock.calls[0][0];
        const filters = callArgs.filters;

        // Should preserve existing filters
        expect(filters).toContainEqual(['golden', true]);
        expect(filters).toContainEqual(['tags', ['important']]);
        expect(filters).toContainEqual(['startDate', 1234567890]);
        // And add the new filters
        expect(filters).toContainEqual(['schema', 'schema']);
        expect(filters).toContainEqual(['catalog', 'catalog1']);
    });

    it('should handle errors gracefully', async () => {
        const schemaId = 9;
        mockGetState.mockReturnValue(createMockState(schemaId, 0, 10));
        mockSearchConcise.mockRejectedValue(new Error('Network error'));

        const consoleErrorSpy = jest
            .spyOn(console, 'error')
            // eslint-disable-next-line @typescript-eslint/no-empty-function
            .mockImplementation(() => {});

        const thunk = searchTableBySchema('schema', schemaId, 'catalog');
        const result = await thunk(mockDispatch, mockGetState, undefined);

        expect(consoleErrorSpy).toHaveBeenCalled();
        expect(result).toEqual([]); // Should return empty array on error

        consoleErrorSpy.mockRestore();
    });
});
