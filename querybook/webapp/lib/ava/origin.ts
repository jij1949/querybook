export function getAvaOrigin(configValue?: string): string | null {
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
