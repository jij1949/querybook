import { getCatalogType } from 'lib/utils/catalog-type';

describe('getCatalogType', () => {
    describe('direct catalogType value', () => {
        it('returns databricks for catalogType="databricks"', () => {
            expect(getCatalogType({ catalogType: 'databricks' })).toBe('databricks');
        });

        it('returns glue for catalogType="glue"', () => {
            expect(getCatalogType({ catalogType: 'glue' })).toBe('glue');
        });

        it('returns glue for legacy catalogType="aws_glue"', () => {
            expect(getCatalogType({ catalogType: 'aws_glue' })).toBe('glue');
        });

        it('is case-insensitive', () => {
            expect(getCatalogType({ catalogType: 'Databricks' })).toBe('databricks');
            expect(getCatalogType({ catalogType: 'GLUE' })).toBe('glue');
        });

        it('returns unknown for unrecognized catalogType value', () => {
            expect(getCatalogType({ catalogType: 'snowflake' })).toBe('unknown');
        });
    });

    describe('empty / no input', () => {
        it('returns unknown for empty input', () => {
            expect(getCatalogType({})).toBe('unknown');
        });

        it('returns unknown when catalogType is undefined', () => {
            expect(getCatalogType({ catalogType: undefined })).toBe('unknown');
        });
    });
});
