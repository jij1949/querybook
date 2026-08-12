import { useEffect, useRef } from 'react';

import { ComponentType, ElementType } from 'const/analytics';
import { trackView } from 'lib/analytics';

export function useTrackView(
    component: ComponentType,
    element?: ElementType,
    aux?: object
) {
    // Keep the latest `aux` in a ref so it is not a hook dependency. Callers
    // often pass a fresh object literal each render (e.g. Survey), which would
    // otherwise re-run the effect on every render and log duplicate views. We
    // want exactly one view per mount, using the most recent `aux` payload.
    const auxRef = useRef(aux);
    auxRef.current = aux;

    useEffect(() => {
        trackView(component, element, auxRef.current);
    }, [component, element]);
}
