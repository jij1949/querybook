import { Location } from 'history';
import { matchPath } from 'react-router-dom';

import { IEnvironment } from 'redux/environment/types';

import { getAvaOrigin } from './origin';

export { getAvaOrigin };

export type TAvaView = 'adhoc' | 'datadoc' | 'query_execution' | null;
export type TAvaBaseView = 'adhoc' | 'datadoc' | null;

export interface IAvaRouteContext {
    view: TAvaView;
    baseView: TAvaBaseView;
    queryExecutionId: number | null;
    dataDocId: number | null;
    relativeUrl: string | null;
}

export interface IAvaDataDocContext {
    dataDocId: number | null;
    cellId: number | null;
    queryExecutionId: number | null;
}

export interface IAvaContext {
    environment: {
        id: number;
        name: string;
    } | null;
    view: TAvaView;
    baseView: TAvaBaseView;
    queryExecutionId: number | null;
    dataDocId: number | null;
    cellId: number | null;
    queryEngineId: number | null;
    relativeUrl: string | null;
}

export interface IQuerybookContextMessage {
    type: 'querybook_context';
    source: 'querybook';
    payloadVersion: 1;
    payload: IAvaContext;
}

const EMPTY_ROUTE_CONTEXT: IAvaRouteContext = {
    view: null,
    baseView: null,
    queryExecutionId: null,
    dataDocId: null,
    relativeUrl: null,
};

const EMPTY_DATADOC_CONTEXT: IAvaDataDocContext = {
    dataDocId: null,
    cellId: null,
    queryExecutionId: null,
};

type IAvaDerivedView = Pick<
    IAvaRouteContext,
    'view' | 'queryExecutionId' | 'dataDocId' | 'relativeUrl'
>;

function parsePositiveNumber(value?: string): number | null {
    if (!value) {
        return null;
    }

    const parsed = Number(value);
    return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
}

export function getEmptyAvaRouteContext(): IAvaRouteContext {
    return EMPTY_ROUTE_CONTEXT;
}

export function getEmptyAvaDataDocContext(): IAvaDataDocContext {
    return EMPTY_DATADOC_CONTEXT;
}

export function deriveAvaView(location?: Partial<Location>): IAvaDerivedView {
    if (!location?.pathname) {
        return {
            view: null,
            queryExecutionId: null,
            dataDocId: null,
            relativeUrl: null,
        };
    }

    const queryExecutionMatch = matchPath<{ id: string }>(location.pathname, {
        path: '/:env/query_execution/:id/',
    });
    if (queryExecutionMatch) {
        return {
            view: 'query_execution',
            queryExecutionId: parsePositiveNumber(
                queryExecutionMatch.params.id
            ),
            dataDocId: null,
            relativeUrl: `${location.pathname}${location.search ?? ''}${
                location.hash ?? ''
            }`,
        };
    }

    const dataDocMatch = matchPath<{ docId: string }>(location.pathname, {
        path: '/:env/datadoc/:docId/',
    });
    if (dataDocMatch) {
        return {
            view: 'datadoc',
            queryExecutionId: null,
            dataDocId: parsePositiveNumber(dataDocMatch.params.docId),
            relativeUrl: `${location.pathname}${location.search ?? ''}${
                location.hash ?? ''
            }`,
        };
    }

    const adhocMatch = matchPath(location.pathname, {
        path: '/:env/adhoc/',
    });
    if (adhocMatch) {
        return {
            view: 'adhoc',
            queryExecutionId: null,
            dataDocId: null,
            relativeUrl: `${location.pathname}${location.search ?? ''}${
                location.hash ?? ''
            }`,
        };
    }

    return {
        view: null,
        queryExecutionId: null,
        dataDocId: null,
        relativeUrl: `${location.pathname}${location.search ?? ''}${
            location.hash ?? ''
        }`,
    };
}

export function deriveAvaRouteContext(
    location?: Partial<Location>,
    baseLocation?: Partial<Location>
): IAvaRouteContext {
    const currentView = deriveAvaView(location);
    const baseDerivedView = deriveAvaView(baseLocation);
    const baseView = baseDerivedView.view;
    const avaBaseView =
        baseView === 'adhoc' || baseView === 'datadoc' ? baseView : null;

    return {
        ...currentView,
        baseView: avaBaseView,
        dataDocId:
            currentView.dataDocId ??
            (avaBaseView === 'datadoc' ? baseDerivedView.dataDocId : null),
    };
}

export function buildAvaContext({
    environment,
    routeContext,
    adhocExecutionId,
    adhocEngineId,
    dataDocContext,
}: {
    environment?: IEnvironment | null;
    routeContext?: IAvaRouteContext | null;
    adhocExecutionId?: number | null;
    adhocEngineId?: number | null;
    dataDocContext?: IAvaDataDocContext | null;
}): IAvaContext {
    const effectiveRouteContext = routeContext ?? EMPTY_ROUTE_CONTEXT;
    const effectiveDataDocContext = dataDocContext ?? EMPTY_DATADOC_CONTEXT;
    const environmentContext = environment
        ? { id: environment.id, name: environment.name }
        : null;
    const isBaseDataDocContext =
        effectiveRouteContext.baseView === 'datadoc' &&
        (effectiveRouteContext.dataDocId == null ||
            effectiveDataDocContext.dataDocId ===
                effectiveRouteContext.dataDocId);
    const baseDataDocId =
        effectiveRouteContext.dataDocId ?? effectiveDataDocContext.dataDocId;

    if (effectiveRouteContext.view === 'adhoc') {
        return {
            environment: environmentContext,
            view: 'adhoc',
            baseView: null,
            queryExecutionId: adhocExecutionId ?? null,
            dataDocId: null,
            cellId: null,
            queryEngineId: adhocEngineId ?? null,
            relativeUrl: effectiveRouteContext.relativeUrl,
        };
    }

    if (effectiveRouteContext.view === 'datadoc') {
        const isCurrentDoc =
            effectiveDataDocContext.dataDocId ===
            effectiveRouteContext.dataDocId;
        return {
            environment: environmentContext,
            view: 'datadoc',
            baseView: null,
            queryExecutionId:
                isCurrentDoc && effectiveDataDocContext.cellId != null
                    ? effectiveDataDocContext.queryExecutionId
                    : null,
            dataDocId: effectiveRouteContext.dataDocId,
            cellId:
                isCurrentDoc && effectiveDataDocContext.cellId != null
                    ? effectiveDataDocContext.cellId
                    : null,
            queryEngineId: null,
            relativeUrl: effectiveRouteContext.relativeUrl,
        };
    }

    if (effectiveRouteContext.view === 'query_execution') {
        return {
            environment: environmentContext,
            view: 'query_execution',
            baseView: effectiveRouteContext.baseView,
            queryExecutionId: effectiveRouteContext.queryExecutionId,
            dataDocId:
                effectiveRouteContext.baseView === 'datadoc'
                    ? baseDataDocId
                    : null,
            cellId: isBaseDataDocContext
                ? effectiveDataDocContext.cellId
                : null,
            queryEngineId: null,
            relativeUrl: effectiveRouteContext.relativeUrl,
        };
    }

    if (effectiveRouteContext.baseView === 'adhoc') {
        return {
            environment: environmentContext,
            view: null,
            baseView: 'adhoc',
            queryExecutionId: adhocExecutionId ?? null,
            dataDocId: null,
            cellId: null,
            queryEngineId: adhocEngineId ?? null,
            relativeUrl: effectiveRouteContext.relativeUrl,
        };
    }

    if (effectiveRouteContext.baseView === 'datadoc') {
        return {
            environment: environmentContext,
            view: null,
            baseView: 'datadoc',
            queryExecutionId:
                isBaseDataDocContext &&
                effectiveDataDocContext.cellId != null
                    ? effectiveDataDocContext.queryExecutionId
                    : null,
            dataDocId: baseDataDocId,
            cellId: isBaseDataDocContext
                ? effectiveDataDocContext.cellId
                : null,
            queryEngineId: null,
            relativeUrl: effectiveRouteContext.relativeUrl,
        };
    }

    return {
        environment: environmentContext,
        view: null,
        baseView: null,
        queryExecutionId: null,
        dataDocId: null,
        cellId: null,
        queryEngineId: null,
        relativeUrl: effectiveRouteContext.relativeUrl,
    };
}

export function buildAvaIframeSrc(
    avaOrigin: string | null,
    theme: 'dark' | 'light'
): string | null {
    if (!avaOrigin) {
        return null;
    }

    const url = new URL('/ava', avaOrigin);
    url.searchParams.set('fullscreen', 'true');
    url.searchParams.set('ref', 'querybook');
    url.searchParams.set('theme', theme);

    return url.toString();
}

export function createQuerybookContextMessage(
    payload: IAvaContext
): IQuerybookContextMessage {
    return {
        type: 'querybook_context',
        source: 'querybook',
        payloadVersion: 1,
        payload,
    };
}

export function isValidAvaReadyMessage(message: unknown): boolean {
    return (
        typeof message === 'object' &&
        message != null &&
        (message as { type?: string }).type === 'ava_ready'
    );
}
