import { IQueryEngine } from 'const/queryEngine';
import {
    IQueryError,
    IQueryExecution,
    IStatementExecution,
} from 'const/queryExecution';

const queryErrorsByLanguage: Record<
    string,
    Record<
        string,
        {
            regex: string;
            message: string;
        }
    >
> = require('config/query_error.yaml');
const SHARED_ERROR_SUGGESTION = 'common';

// Merge all the common in
for (const language of Object.keys(queryErrorsByLanguage)) {
    if (language !== SHARED_ERROR_SUGGESTION) {
        queryErrorsByLanguage[language] = {
            ...queryErrorsByLanguage[language],
            ...queryErrorsByLanguage[SHARED_ERROR_SUGGESTION],
        };
    }
}

const errorSuggestionInfoByLanguage = Object.entries(
    queryErrorsByLanguage
).reduce(
    (hash, [language, queryErrors]) => {
        if (language !== SHARED_ERROR_SUGGESTION) {
            hash[language] = Object.entries(queryErrors).reduce(
                (innerHash, [errorName, error]) => {
                    innerHash[errorName] = {
                        ...error,
                        regex: new RegExp(error.regex, 'i'),
                    };
                    return innerHash;
                },
                {}
            );
        }
        return hash;
    },
    {} as {
        [language: string]: {
            [errorName: string]: {
                regex: RegExp;
                message: string;
            };
        };
    }
);

function getDefaultQueryErrorSuggestion(
    queryError: IQueryError,
    _queryExecution: IQueryExecution,
    _statementExecutions: IStatementExecution[],
    queryEngine: IQueryEngine
): string {
    const errorMsg = queryError.error_message;
    const language = queryEngine.language;

    for (const errorInfo of Object.values(
        errorSuggestionInfoByLanguage[language] ?? {}
    )) {
        if (errorInfo.regex.test(errorMsg)) {
            return errorInfo.message;
        }
    }
    return '';
}

export function getQueryErrorSuggestion(
    queryError: IQueryError,
    queryExecution: IQueryExecution,
    statementExecutions: IStatementExecution[],
    queryEngine: IQueryEngine
): string {
    let suggestion = window.GET_QUERY_ERROR_SUGGESTION(
        queryError,
        queryExecution,
        statementExecutions,
        queryEngine
    );

    if (suggestion === '') {
        suggestion = getDefaultQueryErrorSuggestion(
            queryError,
            queryExecution,
            statementExecutions,
            queryEngine
        );
    }

    return suggestion;
}

const getQueryEngineClusterType = (queryEngine: IQueryEngine): string => {
    if (queryEngine.language === 'trino') {
        // Match substring in query engine
        const matches = queryEngine.name.match(/-(.*?)-trino \(/);
        if (matches && matches.length === 2) {
            return matches[1];
        }
    }

    return 'unknown';
};

window.GET_QUERY_ERROR_SUGGESTION = (
    queryError: IQueryError,
    queryExecution: IQueryExecution,
    statementExecutions: IStatementExecution[],
    queryEngine: IQueryEngine
): string => {
    console.log('QueryError', queryError);
    console.log('Query Engine: ', queryEngine);

    const queryEngineClusterType = getQueryEngineClusterType(queryEngine);
    console.log('query engine type', queryEngineClusterType);

    if (
        queryEngine.language === 'trino' &&
        queryEngineClusterType === 'etl' &&
        /Access Denied.*hive\.sandbox/.test(queryError.error_message)
    ) {
        return `ETL clusters cannot access the \`sandbox\` schema.  Please use an Ad hoc cluster instead.

For more details, please refer to https://confluence.expedia.biz/pages/viewpage.action?spaceKey=DAPS&title=Cluster+Types`;
    }
    if (
        queryEngine.language === 'trino' &&
        queryEngineClusterType === 'adhoc' &&
        /Access Denied: Cannot .*? table hive\.(?!sandbox)/.test(
            queryError.error_message
        )
    ) {
        return `Ad hoc clusters cannot write to persistent schemas.  Please use an ETL cluster instead.

For more details, please refer to https://confluence.expedia.biz/pages/viewpage.action?spaceKey=DAPS&title=Cluster+Types`;
    }
    if (
        queryEngine.language === 'trino' &&
        queryEngineClusterType === 'adhoc' &&
        /Table 'hive\.sandbox.* does not exist/.test(queryError.error_message)
    ) {
        return `Sandbox schemas are configured with a time-to-live (TTL) of 10 days, after which they are automatically cleaned up.

If you need to keep data for longer, please use a persistent schema instead.`;
    }

    return '';
};
