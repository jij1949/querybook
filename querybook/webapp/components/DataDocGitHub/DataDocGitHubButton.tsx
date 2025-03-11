import React, { useCallback, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';

import { fetchDataDocGitHubLinked } from 'redux/dataDoc/action';
import { IStoreState } from 'redux/store/types';
import { IconButton } from 'ui/Button/IconButton';

import { GitHubIntegration } from './GitHubIntegration';

interface IProps {
    docId: number;
}

export const DataDocGitHubButton: React.FunctionComponent<IProps> = ({
    docId,
}) => {
    const [isGitHubModalOpen, setIsGitHubModalOpen] = useState(false);

    const handleOpenGitHubModal = useCallback(() => {
        setIsGitHubModalOpen(true);
    }, []);

    const handleCloseGitHubModal = useCallback(() => {
        setIsGitHubModalOpen(false);
    }, []);

    const isGitHubLinked = useSelector(
        (state: IStoreState) => state.dataDoc.gitHubLinkedByDocId[docId]
    );

    const dispatch = useDispatch();
    React.useEffect(() => {
        dispatch(fetchDataDocGitHubLinked(docId));
    }, [dispatch, docId]);

    return (
        <>
            <IconButton
                icon="Github"
                onClick={handleOpenGitHubModal}
                tooltip={
                    isGitHubLinked ? 'Connected to GitHub' : 'Connect to GitHub'
                }
                tooltipPos="left"
                title="GitHub"
                color={isGitHubLinked ? 'accent' : undefined}
            />
            {isGitHubModalOpen && (
                <GitHubIntegration
                    docId={docId}
                    onClose={handleCloseGitHubModal}
                />
            )}
        </>
    );
};
