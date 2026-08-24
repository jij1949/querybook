import { isEqual } from 'lodash';
import React from 'react';

import {
    createQuerybookContextMessage,
    IAvaContext,
    isValidAvaReadyMessage,
} from 'lib/ava/context';
import { FullHeight } from 'ui/FullHeight/FullHeight';

import './IFrameNavigator.scss';

export const IFrameNavigator: React.FC<{
    src: string;
    message?: IAvaContext;
    targetOrigin?: string | null;
}> = ({ src, message, targetOrigin, ...props }) => {
    const iframeRef = React.useRef<HTMLIFrameElement>(null);
    const lastSentMessageRef = React.useRef<IAvaContext | null>(null);

    const postContextMessage = React.useCallback(
        (force = false) => {
            if (!message || !targetOrigin) {
                return;
            }

            const contentWindow = iframeRef.current?.contentWindow;
            if (!contentWindow) {
                return;
            }

            if (!force && isEqual(message, lastSentMessageRef.current)) {
                return;
            }

            contentWindow.postMessage(
                createQuerybookContextMessage(message),
                targetOrigin
            );
            lastSentMessageRef.current = message;
        },
        [message, targetOrigin]
    );

    React.useEffect(() => {
        postContextMessage();
    }, [postContextMessage]);

    React.useEffect(() => {
        if (!targetOrigin) {
            return;
        }

        const onMessage = (event: MessageEvent) => {
            if (
                event.origin !== targetOrigin ||
                event.source !== iframeRef.current?.contentWindow ||
                !isValidAvaReadyMessage(event.data)
            ) {
                return;
            }

            postContextMessage(true);
        };

        window.addEventListener('message', onMessage);
        return () => window.removeEventListener('message', onMessage);
    }, [postContextMessage, targetOrigin]);

    const contentDOM = (
        <FullHeight flex="row" className="IFrameNavigator" align="stretch">
            <iframe
                {...props}
                ref={iframeRef}
                src={src}
                onLoad={() => postContextMessage(true)}
            />
        </FullHeight>
    );

    return contentDOM;
};
