import { Location } from 'history';

import {
    buildAvaContext,
    buildAvaIframeSrc,
    createQuerybookContextMessage,
    deriveAvaRouteContext,
    getAvaOrigin,
    isValidAvaReadyMessage,
} from 'lib/ava/context';

describe('deriveAvaRouteContext', () => {
    test('derives adhoc view', () => {
        expect(
            deriveAvaRouteContext({
                pathname: '/prod/adhoc/',
                search: '',
                hash: '',
            } as Location)
        ).toEqual({
            view: 'adhoc',
            baseView: null,
            queryExecutionId: null,
            dataDocId: null,
            relativeUrl: '/prod/adhoc/',
        });
    });

    test('derives modal base view', () => {
        expect(
            deriveAvaRouteContext(
                {
                    pathname: '/prod/query_execution/42/',
                    search: '',
                    hash: '',
                } as Location,
                {
                    pathname: '/prod/datadoc/7/',
                    search: '',
                    hash: '',
                } as Location
            )
        ).toEqual({
            view: 'query_execution',
            baseView: 'datadoc',
            queryExecutionId: 42,
            dataDocId: 7,
            relativeUrl: '/prod/query_execution/42/',
        });
    });

    test('derives base view for unknown modal routes', () => {
        expect(
            deriveAvaRouteContext(
                {
                    pathname: '/prod/table/42/',
                    search: '?sample=true',
                    hash: '#columns',
                } as Location,
                {
                    pathname: '/prod/datadoc/7/',
                    search: '',
                    hash: '',
                } as Location
            )
        ).toEqual({
            view: null,
            baseView: 'datadoc',
            queryExecutionId: null,
            dataDocId: 7,
            relativeUrl: '/prod/table/42/?sample=true#columns',
        });
    });

    test('rejects non-positive and non-integer route ids', () => {
        expect(
            deriveAvaRouteContext({
                pathname: '/prod/query_execution/0/',
                search: '',
                hash: '',
            } as Location).queryExecutionId
        ).toBeNull();
        expect(
            deriveAvaRouteContext({
                pathname: '/prod/query_execution/-1/',
                search: '',
                hash: '',
            } as Location).queryExecutionId
        ).toBeNull();
        expect(
            deriveAvaRouteContext({
                pathname: '/prod/datadoc/3.5/',
                search: '',
                hash: '',
            } as Location).dataDocId
        ).toBeNull();
    });
});

describe('buildAvaContext', () => {
    const environment = { id: 3, name: 'prod' } as any;

    test('builds adhoc context', () => {
        expect(
            buildAvaContext({
                environment,
                routeContext: {
                    view: 'adhoc',
                    baseView: null,
                    queryExecutionId: null,
                    dataDocId: null,
                    relativeUrl: '/prod/adhoc/',
                },
                adhocExecutionId: 11,
                adhocEngineId: 12,
            })
        ).toEqual({
            environment: { id: 3, name: 'prod' },
            view: 'adhoc',
            baseView: null,
            queryExecutionId: 11,
            dataDocId: null,
            cellId: null,
            queryEngineId: 12,
            relativeUrl: '/prod/adhoc/',
        });
    });

    test('uses datadoc publication only for the active document', () => {
        expect(
            buildAvaContext({
                environment,
                routeContext: {
                    view: 'datadoc',
                    baseView: null,
                    queryExecutionId: null,
                    dataDocId: 22,
                    relativeUrl: '/prod/datadoc/22/',
                },
                dataDocContext: {
                    dataDocId: 999,
                    cellId: 45,
                    queryExecutionId: 46,
                },
            })
        ).toEqual({
            environment: { id: 3, name: 'prod' },
            view: 'datadoc',
            baseView: null,
            queryExecutionId: null,
            dataDocId: 22,
            cellId: null,
            queryEngineId: null,
            relativeUrl: '/prod/datadoc/22/',
        });
    });

    test('preserves datadoc context behind unknown modal routes', () => {
        expect(
            buildAvaContext({
                environment,
                routeContext: {
                    view: null,
                    baseView: 'datadoc',
                    queryExecutionId: null,
                    dataDocId: 22,
                    relativeUrl: '/prod/table/55/',
                },
                dataDocContext: {
                    dataDocId: 22,
                    cellId: 45,
                    queryExecutionId: 46,
                },
            })
        ).toEqual({
            environment: { id: 3, name: 'prod' },
            view: null,
            baseView: 'datadoc',
            queryExecutionId: 46,
            dataDocId: 22,
            cellId: 45,
            queryEngineId: null,
            relativeUrl: '/prod/table/55/',
        });
    });

    test('ignores stale datadoc cell context behind unknown modal routes', () => {
        expect(
            buildAvaContext({
                environment,
                routeContext: {
                    view: null,
                    baseView: 'datadoc',
                    queryExecutionId: null,
                    dataDocId: 22,
                    relativeUrl: '/prod/table/55/',
                },
                dataDocContext: {
                    dataDocId: 999,
                    cellId: 45,
                    queryExecutionId: 46,
                },
            })
        ).toEqual({
            environment: { id: 3, name: 'prod' },
            view: null,
            baseView: 'datadoc',
            queryExecutionId: null,
            dataDocId: 22,
            cellId: null,
            queryEngineId: null,
            relativeUrl: '/prod/table/55/',
        });
    });

    test('preserves adhoc context behind unknown modal routes', () => {
        expect(
            buildAvaContext({
                environment,
                routeContext: {
                    view: null,
                    baseView: 'adhoc',
                    queryExecutionId: null,
                    dataDocId: null,
                    relativeUrl: '/prod/search/',
                },
                adhocExecutionId: 11,
                adhocEngineId: 12,
            })
        ).toEqual({
            environment: { id: 3, name: 'prod' },
            view: null,
            baseView: 'adhoc',
            queryExecutionId: 11,
            dataDocId: null,
            cellId: null,
            queryEngineId: 12,
            relativeUrl: '/prod/search/',
        });
    });

    test('preserves datadoc context behind query execution modal routes', () => {
        expect(
            buildAvaContext({
                environment,
                routeContext: {
                    view: 'query_execution',
                    baseView: 'datadoc',
                    queryExecutionId: 99,
                    dataDocId: 22,
                    relativeUrl: '/prod/query_execution/99/',
                },
                dataDocContext: {
                    dataDocId: 22,
                    cellId: 45,
                    queryExecutionId: 46,
                },
            })
        ).toEqual({
            environment: { id: 3, name: 'prod' },
            view: 'query_execution',
            baseView: 'datadoc',
            queryExecutionId: 99,
            dataDocId: 22,
            cellId: 45,
            queryEngineId: null,
            relativeUrl: '/prod/query_execution/99/',
        });
    });
});

describe('ava origin and messaging', () => {
    test('validates and normalizes origins', () => {
        expect(getAvaOrigin()).toBeNull();
        expect(getAvaOrigin('   ')).toBeNull();
        expect(getAvaOrigin('https://analytics.expedia.biz/ava')).toBe(
            'https://analytics.expedia.biz'
        );
        expect(getAvaOrigin('http://localhost:3000/anything')).toBe(
            'http://localhost:3000'
        );
        expect(getAvaOrigin('http://example.com')).toBeNull();
        expect(getAvaOrigin('*')).toBeNull();
    });

    test('builds iframe src and message envelope', () => {
        const payload = buildAvaContext({
            environment: { id: 1, name: 'dev' } as any,
            routeContext: {
                view: null,
                baseView: null,
                queryExecutionId: null,
                dataDocId: null,
                relativeUrl: '/dev/',
            },
        });

        expect(buildAvaIframeSrc('https://analytics.expedia.biz', 'dark')).toBe(
            'https://analytics.expedia.biz/ava?fullscreen=true&ref=querybook&theme=dark'
        );
        expect(createQuerybookContextMessage(payload)).toEqual({
            type: 'querybook_context',
            source: 'querybook',
            payloadVersion: 1,
            payload,
        });
        expect(isValidAvaReadyMessage({ type: 'ava_ready' })).toBe(true);
        expect(isValidAvaReadyMessage({ type: 'other' })).toBe(false);
    });
});
