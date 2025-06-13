import React, { useCallback } from 'react';

import { Card } from 'ui/Card/Card';
import { Icon } from 'ui/Icon/Icon';
import { Link } from 'ui/Link/Link';
import { Message } from 'ui/Message/Message';
import { StyledText } from 'ui/StyledText/StyledText';

import { GitHubDirectory } from './GitHubDirectory';

import './GitHub.scss';
import { IconButton } from 'ui/Button/IconButton';
import { GitHubResource } from 'resource/github';
import toast from 'react-hot-toast';

interface IProps {
    docId: number;
    linkedDirectory?: string | null;
    onLinkDirectory: (directory: string) => Promise<void>;
}

export const GitHubSettings: React.FC<IProps> = ({
    docId,
    linkedDirectory,
    onLinkDirectory,
}) => {
    const resetGitHubToken = useCallback(async () => {
        try {
            await GitHubResource.resetGitHubToken();
            toast.success(
                'GitHub token reset successfully. Please reload the page.'
            );
        } catch (error) {
            toast.error('Failed to reset GitHub token.');
        }
    }, []);

    const authorizationCardDom = (
        <div className="GitHubSettings-section-content p8 mb12 mt16">
            <Message
                title="GitHub Authorization"
                type="success"
                icon="CheckCircle"
                iconSize={20}
                size="large"
                center
            >
                <div>
                    <StyledText center>
                        Your GitHub account is successfully authorized. Manage
                        your GitHub authorized OAuth apps{' '}
                        <Link
                            to="https://github.com/settings/applications"
                            newTab
                        >
                            <strong>here</strong>{' '}
                            <Icon name="ExternalLink" size={14} />
                        </Link>
                        .
                    </StyledText>
                    <div className={'flex-row align-items-center mt8'}>
                        Issues? Try resetting your GitHub token:
                        <IconButton
                            icon="RefreshCw"
                            tooltip="Reset GitHub Token"
                            tooltipPos="right"
                        />
                    </div>
                </div>
            </Message>
        </div>
    );

    const directoryCardDom = (
        <div className="GitHubSettings-section-content p8 mb12">
            <GitHubDirectory
                docId={docId}
                linkedDirectory={linkedDirectory}
                onLinkDirectory={onLinkDirectory}
            />
        </div>
    );

    return (
        <Card className="GitHubSettings p4 mt4">
            {authorizationCardDom}
            {directoryCardDom}
        </Card>
    );
};
