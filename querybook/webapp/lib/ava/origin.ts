const QUERYBOOK_TEST_HOSTNAME = 'querybook-test.expedia.biz';
const AVA_TEST_ORIGIN = 'https://analytics-test.expedia.biz';

export function getAvaOrigin(configValue?: string): string | null {
    if (
        typeof window !== 'undefined' &&
        window.location?.hostname === QUERYBOOK_TEST_HOSTNAME
    ) {
        return AVA_TEST_ORIGIN;
    }

    const candidate = configValue?.trim();
    if (!candidate || candidate === '*') {
        return null;
    }

    try {
        const url = new URL(candidate);
        const isValidProtocol =
            url.protocol === 'https:' ||
            (url.protocol === 'http:' && url.hostname === 'localhost');
        return isValidProtocol ? url.origin : null;
    } catch {
        return null;
    }
}
