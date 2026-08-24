import React from 'react';

import {
    getEmptyAvaDataDocContext,
    getEmptyAvaRouteContext,
    IAvaDataDocContext,
    IAvaRouteContext,
} from 'lib/ava/context';

interface IAvaHostContextType {
    routeContext: IAvaRouteContext;
    dataDocContext: IAvaDataDocContext;
    setRouteContext: (routeContext: IAvaRouteContext) => void;
    publishDataDocContext: (dataDocContext: IAvaDataDocContext) => void;
    clearDataDocContext: () => void;
}

const defaultContext: IAvaHostContextType = {
    routeContext: getEmptyAvaRouteContext(),
    dataDocContext: getEmptyAvaDataDocContext(),
    setRouteContext: () => undefined,
    publishDataDocContext: () => undefined,
    clearDataDocContext: () => undefined,
};

export const AvaHostContext =
    React.createContext<IAvaHostContextType>(defaultContext);

export const AvaHostContextProvider: React.FC = ({ children }) => {
    const [routeContext, setRouteContext] = React.useState<IAvaRouteContext>(
        getEmptyAvaRouteContext()
    );
    const [dataDocContext, setDataDocContext] =
        React.useState<IAvaDataDocContext>(getEmptyAvaDataDocContext());

    const publishDataDocContext = React.useCallback(
        (nextDataDocContext: IAvaDataDocContext) => {
            setDataDocContext(nextDataDocContext);
        },
        []
    );

    const clearDataDocContext = React.useCallback(() => {
        setDataDocContext(getEmptyAvaDataDocContext());
    }, []);

    const value = React.useMemo(
        () => ({
            routeContext,
            dataDocContext,
            setRouteContext,
            publishDataDocContext,
            clearDataDocContext,
        }),
        [
            clearDataDocContext,
            dataDocContext,
            publishDataDocContext,
            routeContext,
        ]
    );

    return (
        <AvaHostContext.Provider value={value}>
            {children}
        </AvaHostContext.Provider>
    );
};
