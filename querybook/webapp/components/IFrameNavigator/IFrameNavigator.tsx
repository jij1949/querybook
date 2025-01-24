import React from 'react';

import { FullHeight } from 'ui/FullHeight/FullHeight';

import './IFrameNavigator.scss';

export const IFrameNavigator: React.FC<{
    src: string;
}> = ({ src, ...props }) => {
    const contentDOM = (
        <FullHeight flex="row" className="IFrameNavigator" align="stretch">
            <iframe src={src} {...props} />
        </FullHeight>
    );

    return contentDOM;
};
