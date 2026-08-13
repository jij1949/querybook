import axios, { AxiosRequestConfig, Canceler, Method } from 'axios';
import toast from 'react-hot-toast';

import { setSessionExpired } from 'lib/querybookUI';
import { formatError } from 'lib/utils/error';

export interface ICancelablePromise<T> extends Promise<T> {
    cancel?: Canceler;
}

type UrlOrOptions = string | AxiosRequestConfig;
interface DatasourceOptions {
    notifyOnError?: boolean;
    timeout?: number;
    // Coalesce concurrent identical GET requests into a single in-flight
    // request (opt-in). Useful when several components can independently
    // request the same resource at the same time (e.g. a table tooltip
    // popover and the table details view). Only applies to `fetch` (GET).
    // Note: the coalesced callers share one request, so a `.cancel()` from
    // any of them aborts it for all — only enable where per-caller
    // cancellation is not required.
    dedupe?: boolean;
}

function handleRequestException(error: any, notifyOnError?: boolean) {
    console.error(error);

    if (notifyOnError) {
        toast.error(formatError(error));
    }

    if (error?.response?.status === 401) {
        setSessionExpired();
    }

    return Promise.reject(error);
}

function syncDatasource<T>(
    method: Method,
    urlOrOptions: UrlOrOptions,
    data?: Record<string, unknown>,
    options: DatasourceOptions = {}
): ICancelablePromise<{ data: T }> {
    const url =
        typeof urlOrOptions === 'string' ? urlOrOptions : urlOrOptions['url'];
    const { notifyOnError = false, timeout = 0 } = options;

    let cancel: Canceler;
    const defaultConfig: AxiosRequestConfig = {
        url,
        baseURL: '/ds',
        headers: {
            'Content-Type': 'application/json; charset=utf-8',
        },
        method,
        cancelToken: new axios.CancelToken((c) => (cancel = c)),
        timeout, // 0 is the default value which means no timeout
    };

    if (data) {
        if (method === 'GET') {
            defaultConfig.params = {
                params: JSON.stringify(data),
            };
        } else {
            defaultConfig.data = data;
        }
    }

    const combinedConfig =
        typeof urlOrOptions === 'string'
            ? defaultConfig
            : {
                  ...defaultConfig,
                  ...urlOrOptions,
              };

    const request: ICancelablePromise<any> = axios.request(combinedConfig).then(
        (resp) => {
            if (resp.status === 200) {
                return Promise.resolve(resp.data);
            } else {
                return handleRequestException(resp, notifyOnError);
            }
        },
        (rej) => handleRequestException(rej, notifyOnError)
    );

    request.cancel = cancel;

    return request;
}

// Tracks in-flight GET requests opted into `dedupe`, keyed by url + data, so
// concurrent identical requests share a single request instead of each firing
// their own. Entries are removed once the request settles.
const inFlightGetRequests = new Map<string, ICancelablePromise<any>>();

function fetchDatasource<T>(
    urlOrOptions: UrlOrOptions,
    data?: Record<string, unknown>,
    options: DatasourceOptions = {
        notifyOnError: false,
    }
): ICancelablePromise<{ data: T }> {
    // Only dedupe plain string-URL GETs: an AxiosRequestConfig can carry
    // non-serializable fields (e.g. transformResponse) or circular refs that
    // make a stable JSON key unreliable, so those fall through to a normal
    // request. The key intentionally covers url + data only, not options like
    // timeout/notifyOnError -- those don't change the response, so coalescing
    // across them is safe (the first caller's options win for the shared call).
    if (!options.dedupe || typeof urlOrOptions !== 'string') {
        return syncDatasource<T>('GET', urlOrOptions, data, options);
    }

    const key = JSON.stringify([urlOrOptions, data ?? null]);
    const existing = inFlightGetRequests.get(key);
    if (existing) {
        return existing;
    }

    const request = syncDatasource<T>('GET', urlOrOptions, data, options);
    inFlightGetRequests.set(key, request);
    const cleanup = () => inFlightGetRequests.delete(key);
    request.then(cleanup, cleanup);
    return request;
}

function saveDatasource<T>(
    urlOrOptions: UrlOrOptions,
    data?: Record<string, unknown>,
    options: DatasourceOptions = {
        notifyOnError: true,
    }
) {
    return syncDatasource<T>('POST', urlOrOptions, data, options);
}

function updateDatasource<T>(
    urlOrOptions: UrlOrOptions,
    data?: Record<string, unknown>,
    options: DatasourceOptions = {
        notifyOnError: true,
    }
) {
    return syncDatasource<T>('PUT', urlOrOptions, data, options);
}

function deleteDatasource<T = null>(
    urlOrOptions: UrlOrOptions,
    data?: Record<string, unknown>,
    options: DatasourceOptions = {
        notifyOnError: true,
    }
) {
    return syncDatasource<T>('DELETE', urlOrOptions, data, options);
}

export function uploadDatasource<T = null>(
    url: string,
    data: Record<string, any>,
    options: DatasourceOptions = {
        notifyOnError: true,
    }
) {
    const formData = new FormData();
    for (const [key, value] of Object.entries(data)) {
        let strOrBlobValue = value;
        if (
            !(
                strOrBlobValue instanceof Blob ||
                strOrBlobValue instanceof String
            )
        ) {
            strOrBlobValue = JSON.stringify(strOrBlobValue);
        }

        formData.append(key, strOrBlobValue);
    }

    const urlOptions: AxiosRequestConfig = {
        url,
        headers: {
            'Content-Type': 'multipart/form-data; charset=utf-8',
        },
        data: formData,
    };
    return syncDatasource<T>('POST', urlOptions, null, options);
}

export default {
    fetch: fetchDatasource,
    save: saveDatasource,
    update: updateDatasource,
    delete: deleteDatasource,
    upload: uploadDatasource,
};
