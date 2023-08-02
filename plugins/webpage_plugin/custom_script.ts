// Place your custom css/js logic here
import React from 'react';

export {};

interface IColumnDetector {
    type: string;
    priority: number;
    checker: (colName: string, values: any[]) => boolean;
}

interface IColumnStatsAnalyzer {
    key: string;
    name: string;
    appliesToType: string[];
    generator: (values: any[]) => string;
}

interface IColumnTransformer {
    key: string;
    name: string;

    appliesToType: string[];
    priority: number;
    auto: boolean;

    transform: (v: any) => React.ReactNode;
}

// Use the following definitions to override default Querybook
// behavior
declare global {
    /* tslint:disable:interface-name */
    interface Window {
        // Users will see this message if they cannot
        // access any
        NO_ENVIRONMENT_MESSAGE?: string;
        CUSTOM_LANDING_PAGE?: {
            // Two modes of custom landing page
            // replace: replace the entire landing page with custom content
            // not specified: add the custom content to the middle of the
            //                landing page
            mode?: 'replace';
            renderer: () => React.ReactElement;
        };
        CUSTOM_COLUMN_STATS_ANALYZERS?: IColumnStatsAnalyzer[];
        CUSTOM_COLUMN_DETECTORS?: IColumnDetector[];
        CUSTOM_COLUMN_TRANSFORMERS?: IColumnTransformer[];
        CUSTOM_KEY_MAP?: Record<
            string,
            Record<string, { key?: string; name?: string }>
        >;

        ROW_LIMIT_SCALE?: number[];
        DEFAULT_ROW_LIMIT?: number;
        ALLOW_UNLIMITED_QUERY?: boolean;
    }
}

window.ROW_LIMIT_SCALE = [1, 2, 3, 4, 5, 6].map((v) => Math.pow(10, v));
window.DEFAULT_ROW_LIMIT = window.ROW_LIMIT_SCALE[2];
window.ALLOW_UNLIMITED_QUERY = true;

// Analytics
function setupAnalytics() {
    var scriptTag = document.createElement('script');
    scriptTag.async = true;
    scriptTag.src =
        'https://egap-umami.rcp.us-west-2.data.test.exp-aws.net/custom.js';

    var domain = window.location.hostname;
    if (domain === 'querybook.expedia.biz') {
        scriptTag.setAttribute(
            'data-website-id',
            'cd9789ee-fe74-4ea1-9164-14cbd608186c'
        );
    } else if (domain === 'querybook-test.expedia.biz') {
        scriptTag.setAttribute(
            'data-website-id',
            'd98152cf-992d-4d2d-8a4d-a4b7cf98a393'
        );
    } else {
        // Do not load analytics for other domains (e.g. localhost)
        return;
    }

    document.head.appendChild(scriptTag);
}
setupAnalytics();
