import * as React from 'react';

import { isValidUrl, titleize } from 'lib/utils';
import { ThemedCodeHighlight } from 'ui/CodeHighlight/ThemedCodeHighlight';
import { Link } from 'ui/Link/Link';

import { KeyContentDisplay } from './KeyContentDisplay';

export const KeyContentDisplayLink: React.FunctionComponent<{
    keyString: string;
    value: string | number;
}> = ({ keyString, value }) => {
    const valueStr = value?.toString() ?? '';
    return (
        <KeyContentDisplay
            key={keyString}
            keyString={titleize(keyString, '_', ' ')}
        >
            {valueStr && isValidUrl(valueStr.trim()) ? (
                <Link to={valueStr} newTab>
                    {valueStr}
                </Link>
            ) : keyString === 'original_sql' ? (
                <ThemedCodeHighlight value={valueStr} />
            ) : (
                valueStr
            )}
        </KeyContentDisplay>
    );
};
