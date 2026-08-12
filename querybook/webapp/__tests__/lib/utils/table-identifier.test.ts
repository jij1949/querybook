import {
    getLegacyPrefixedSchemaName,
    getTableTokenDisplayName,
    resolveTableWithLegacyFallback,
} from 'lib/utils/table-identifier';

describe('getTableTokenDisplayName', () => {
    const tableWithCatalog = {
        catalog: 'hive_metastore',
        schema: 'default',
        name: 'orders',
    };

    const tableWithoutCatalog = {
        catalog: null,
        schema: 'default',
        name: 'orders',
    };

    describe('when showCatalog is true', () => {
        it('includes catalog when catalog is present', () => {
            expect(getTableTokenDisplayName(tableWithCatalog, true)).toBe(
                'hive_metastore.default.orders'
            );
        });

        it('excludes catalog when catalog is null', () => {
            expect(getTableTokenDisplayName(tableWithoutCatalog, true)).toBe(
                'default.orders'
            );
        });

        it('excludes catalog when catalog is undefined', () => {
            const tableUndefinedCatalog = {
                catalog: undefined,
                schema: 'default',
                name: 'orders',
            };
            expect(getTableTokenDisplayName(tableUndefinedCatalog, true)).toBe(
                'default.orders'
            );
        });
    });

    describe('when showCatalog is false', () => {
        it('excludes catalog even when catalog is present', () => {
            expect(getTableTokenDisplayName(tableWithCatalog, false)).toBe(
                'default.orders'
            );
        });

        it('excludes catalog when catalog is null', () => {
            expect(getTableTokenDisplayName(tableWithoutCatalog, false)).toBe(
                'default.orders'
            );
        });

        it('excludes catalog when catalog is undefined', () => {
            const tableUndefinedCatalog = {
                catalog: undefined,
                schema: 'default',
                name: 'orders',
            };
            expect(getTableTokenDisplayName(tableUndefinedCatalog, false)).toBe(
                'default.orders'
            );
        });
    });

    describe('when showCatalog parameter is omitted (default behavior)', () => {
        it('excludes catalog even when catalog is present (defaults to false)', () => {
            expect(getTableTokenDisplayName(tableWithCatalog)).toBe(
                'default.orders'
            );
        });

        it('excludes catalog when catalog is null (defaults to false)', () => {
            expect(getTableTokenDisplayName(tableWithoutCatalog)).toBe(
                'default.orders'
            );
        });
    });

    describe('edge cases', () => {
        it('handles empty string catalog', () => {
            const tableEmptyCatalog = {
                catalog: '',
                schema: 'default',
                name: 'orders',
            };
            expect(getTableTokenDisplayName(tableEmptyCatalog, true)).toBe(
                'default.orders'
            );
            expect(getTableTokenDisplayName(tableEmptyCatalog, false)).toBe(
                'default.orders'
            );
        });

        it('handles complex schema and table names', () => {
            const complexTable = {
                catalog: 'prod_catalog',
                schema: 'finance_schema',
                name: 'user_transactions_2024',
            };
            expect(getTableTokenDisplayName(complexTable, true)).toBe(
                'prod_catalog.finance_schema.user_transactions_2024'
            );
            expect(getTableTokenDisplayName(complexTable, false)).toBe(
                'finance_schema.user_transactions_2024'
            );
        });

        it('handles schema and table names with special characters', () => {
            const specialTable = {
                catalog: 'catalog_v2',
                schema: 'schema-name',
                name: 'table_name',
            };
            expect(getTableTokenDisplayName(specialTable, true)).toBe(
                'catalog_v2.schema-name.table_name'
            );
            expect(getTableTokenDisplayName(specialTable, false)).toBe(
                'schema-name.table_name'
            );
        });
    });
});

describe('getLegacyPrefixedSchemaName', () => {
    it('collapses catalog and schema into the legacy prefixed schema', () => {
        expect(
            getLegacyPrefixedSchemaName('egdp_analytics', 'plat_metrics')
        ).toBe('egdp_analytics_plat_metrics');
    });

    it('returns null when catalog is null', () => {
        expect(getLegacyPrefixedSchemaName(null, 'plat_metrics')).toBeNull();
    });

    it('returns null when catalog is undefined', () => {
        expect(
            getLegacyPrefixedSchemaName(undefined, 'plat_metrics')
        ).toBeNull();
    });

    it('returns null when catalog is an empty string', () => {
        expect(getLegacyPrefixedSchemaName('', 'plat_metrics')).toBeNull();
    });
});

describe('resolveTableWithLegacyFallback', () => {
    it('returns the canonical result without a fallback when it hits', async () => {
        const fetch = jest.fn(async (schema: string) => ({ schema }));
        const result = await resolveTableWithLegacyFallback(
            fetch,
            'egdp_analytics',
            'plat_metrics',
            'orders'
        );

        expect(result).toEqual({ schema: 'plat_metrics' });
        expect(fetch).toHaveBeenCalledTimes(1);
        expect(fetch).toHaveBeenCalledWith(
            'plat_metrics',
            'orders',
            'egdp_analytics'
        );
    });

    it('retries with the collapsed legacy schema and no catalog when the canonical lookup misses', async () => {
        const fetch = jest.fn(async (schema: string) =>
            schema === 'egdp_analytics_plat_metrics' ? { schema } : null
        );
        const result = await resolveTableWithLegacyFallback(
            fetch,
            'egdp_analytics',
            'plat_metrics',
            'orders'
        );

        expect(result).toEqual({ schema: 'egdp_analytics_plat_metrics' });
        expect(fetch).toHaveBeenCalledTimes(2);
        expect(fetch).toHaveBeenNthCalledWith(
            2,
            'egdp_analytics_plat_metrics',
            'orders'
        );
    });

    it('does not retry when there is no catalog', async () => {
        const fetch = jest.fn(async () => null);
        const result = await resolveTableWithLegacyFallback(
            fetch,
            null,
            'plat_metrics',
            'orders'
        );

        expect(result).toBeNull();
        expect(fetch).toHaveBeenCalledTimes(1);
    });

    it('resolves to undefined without a lookup when fetch is not provided', async () => {
        expect(
            await resolveTableWithLegacyFallback(
                undefined,
                'egdp_analytics',
                'plat_metrics',
                'orders'
            )
        ).toBeUndefined();
    });
});
