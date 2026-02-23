import { getTableTokenDisplayName } from 'lib/utils/table-identifier';

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
            expect(
                getTableTokenDisplayName(tableUndefinedCatalog, false)
            ).toBe('default.orders');
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
