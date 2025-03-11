import React from 'react';

import { AsyncButton } from 'ui/AsyncButton/AsyncButton';
import { Icon } from 'ui/Icon/Icon';
import { Message } from 'ui/Message/Message';

import './GitHub.scss';

interface IProps {
    onAuthorize: () => Promise<void>;
}

export const GitHubAuth: React.FunctionComponent<IProps> = ({
    onAuthorize,
}) => (
    <div className="GitHubAuth p20">
        <Icon name="Github" size={64} className="GitHubAuth-icon mb20" />
        <Message title="Connect to GitHub" type="info" iconSize={32}>
            <p>
                We need your permission to access your GitHub repositories.
                Please authorize to enable GitHub features on Querybook.
            </p>
            <br />
            <p>
                <strong>Important:</strong> use your GHEC account (
                <code>&lt;username&gt;_expedia</code>) instead of a personal
                GitHub account.
            </p>
        </Message>
        <AsyncButton
            onClick={onAuthorize}
            title="Connect Now"
            color="accent"
            theme="fill"
        />
    </div>
);
