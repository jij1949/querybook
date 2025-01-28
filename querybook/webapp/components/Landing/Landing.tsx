import { sample } from 'lodash';
import React from 'react';
import { useDispatch } from 'react-redux';

import { QuerybookSidebarUIGuide } from 'components/UIGuide/QuerybookSidebarUIGuide';
import loadingHintsConfig from 'config/loading_hints.yaml';
import { ComponentType, ElementType } from 'const/analytics';
import { useShallowSelector } from 'hooks/redux/useShallowSelector';
import { useBrowserTitle } from 'hooks/useBrowserTitle';
import { useTrackView } from 'hooks/useTrackView';
import { trackClick } from 'lib/analytics';
import { titleize } from 'lib/utils';
import { navigateWithinEnv } from 'lib/utils/query-string';
import { fetchDataDocs } from 'redux/dataDoc/action';
import {
    favoriteDataDocsSelector,
    recentDataDocsSelector,
} from 'redux/dataDoc/selector';
import { currentEnvironmentSelector } from 'redux/environment/selector';
import { IStoreState } from 'redux/store/types';
import { Column, Columns } from 'ui/Column/Column';
import { Link } from 'ui/Link/Link';
import { Markdown } from 'ui/Markdown/Markdown';
import { Message } from 'ui/Message/Message';

import './Landing.scss';

const querybookHints = loadingHintsConfig.hints;

const DefaultLanding: React.FC = ({ children }) => {
    const { userInfo, recentDataDocs, favoriteDataDocs, environment } =
        useShallowSelector((state: IStoreState) => {
            const recentDataDocsFromState = recentDataDocsSelector(state);
            const favoriteDataDocsFromState = favoriteDataDocsSelector(
                state
            ).slice(0, 5);
            return {
                userInfo: state.user.userInfoById[state.user.myUserInfo.uid],
                recentDataDocs: recentDataDocsFromState,
                favoriteDataDocs: favoriteDataDocsFromState,
                environment: currentEnvironmentSelector(state),
            };
        });

    const dispatch = useDispatch();
    React.useEffect(() => {
        dispatch(fetchDataDocs('favorite'));
        dispatch(fetchDataDocs('recent'));
    }, [environment.id]);

    const onDataDocClick = React.useCallback((docId, elementType) => {
        trackClick({
            component: ComponentType.LANDING_PAGE,
            element: elementType,
            aux: {
                docId,
            },
        });
        navigateWithinEnv(`/datadoc/${docId}/`);
    }, []);

    const getRecentDOM = () =>
        recentDataDocs.map((dataDoc) => (
            <div
                className="Landing-data-doc"
                onClick={() =>
                    onDataDocClick(dataDoc.id, ElementType.RECENT_DATADOC)
                }
                key={dataDoc.id}
            >
                {dataDoc.title || 'Untitled'}
            </div>
        ));
    const getFavoriteDOM = () =>
        favoriteDataDocs.map((dataDoc) => (
            <div
                className="Landing-data-doc"
                onClick={() =>
                    onDataDocClick(dataDoc.id, ElementType.FAVORITE_DATADOC)
                }
                key={dataDoc.id}
            >
                {dataDoc.title || 'Untitled'}
            </div>
        ));

    const [hint] = React.useState(sample(querybookHints));

    const LandingHeader = (
        <div className="Landing-top horizontal-space-between">
            <div>
                <div className="Landing-greeting">
                    Hi {titleize(userInfo.fullname || userInfo.username)},
                </div>
                <div className="Landing-subtitle">
                    Welcome back to Querybook
                </div>
            </div>
            <QuerybookSidebarUIGuide />
        </div>
    );

    const LandingFooter = (
        <div className="Landing-bottom flex-column">
            <div style={{ marginLeft: '-8px' }}>
                <Message type="tip">
                    <div className="flex-row">
                        <img
                            src="/static/workbench.png"
                            style={{
                                width: '24px',
                                marginRight: '4px',
                            }}
                        />{' '}
                        Try out Ava, our new AI Agent! Now available in the
                        sidebar or on{' '}
                        <Link to="https://analytics.expedia.biz/" newTab={true}>
                            Analytics Workbench
                        </Link>{' '}
                        🎉
                    </div>
                </Message>
            </div>
            <Columns>
                <Column>
                    <div className="Landing-section-title">Documentation</div>
                    <div className="Landing-list">
                        <div>
                            <Link
                                to="https://confluence.expedia.biz/display/DSPKB/Querybook"
                                newTab={true}
                            >
                                Querybook Knowledge Base (KB) 📖
                            </Link>
                        </div>
                        <div>
                            <Link
                                to="https://confluence.expedia.biz/display/DSPKB/Querybook+Best+Practices"
                                newTab={true}
                            >
                                Querybook Best Practices 📚
                            </Link>
                        </div>
                        <div>
                            <Link
                                to="https://pages.github.expedia.biz/analytics-learning/analytics-bootcamp/docs/Querybook/querybook"
                                newTab={true}
                            >
                                Querybook 101 in Analytics Bootcamp 🎓
                            </Link>
                        </div>
                        <br />
                        <div>
                            <Link
                                to="https://analytics.expedia.biz/trino"
                                newTab={true}
                            >
                                Trino Clusters in Analytics Workbench 🎉
                            </Link>
                        </div>
                        <div>
                            <Link
                                to="https://analytics.expedia.biz/apiary"
                                newTab={true}
                            >
                                Apiary Configuration in Analytics Workbench 🎉
                            </Link>
                        </div>
                    </div>
                </Column>
            </Columns>
            <Columns>
                <Column>
                    <div className="Landing-section-title">Did you know?</div>
                    <p>
                        <Markdown>{hint}</Markdown>
                    </p>
                </Column>
            </Columns>
            <Columns>
                <Column>
                    <div className="Landing-section-title">Recent DataDocs</div>
                    <div className="Landing-list">{getRecentDOM()}</div>
                </Column>
                <Column>
                    <div className="Landing-section-title">
                        Favorite DataDocs
                    </div>
                    <div className="Landing-list">{getFavoriteDOM()}</div>
                </Column>
            </Columns>
        </div>
    );

    return (
        <div className="Landing flex-column">
            {LandingHeader}
            <div className="Landing-middle">{children}</div>
            {LandingFooter}
        </div>
    );
};

const Landing: React.FC = () => {
    useTrackView(ComponentType.LANDING_PAGE);
    useBrowserTitle();

    const customLandingConfig = window.CUSTOM_LANDING_PAGE;
    if (customLandingConfig?.mode === 'replace') {
        return customLandingConfig.renderer();
    }

    return <DefaultLanding>{customLandingConfig?.renderer()}</DefaultLanding>;
};

export default Landing;
