import React, { useState } from 'react';
import { TooltipDirection } from 'const/tooltip';
import { IconButton } from 'ui/Button/IconButton';
import { UploadDataDocWindow } from './UploadDataDocWindow';

export interface IUploadDataDocButtonProps {
    tooltipPos?: TooltipDirection;
    tooltip?: string;
}

export const UploadDataDocButton: React.FunctionComponent<
    IUploadDataDocButtonProps
> = ({ tooltipPos = 'left', tooltip = 'Upload DataDoc JSON' }) => {
    const [showUploader, setShowUploader] = useState(false);

    return (
        <>
            <IconButton
                icon="Upload"
                tooltip={tooltip}
                tooltipPos={tooltipPos}
                onClick={() => setShowUploader(true)}
            />
            {showUploader && (
                <UploadDataDocWindow onHide={() => setShowUploader(false)} />
            )}
        </>
    );
};
