import clsx from 'clsx';
import React from 'react';
import { useDispatch, useSelector } from 'react-redux';

import { DataDocNavigator } from 'components/DataDocNavigator/DataDocNavigator';
import { DataDocSchemaNavigator } from 'components/DataDocSchemaNavigator/DataDocSchemaNavigator';
import { IFrameNavigator } from 'components/IFrameNavigator/IFrameNavigator';
import { QueryReviewsNavigator } from 'components/QueryReviewsNavigator/QueryReviewsNavigator';
import { QuerySnippetNavigator } from 'components/QuerySnippetNavigator/QuerySnippetNavigator';
import { QueryViewNavigator } from 'components/QueryViewNavigator/QueryViewNavigator';
import { AvaHostContext } from 'context/AvaContext';
import { useEvent } from 'hooks/useEvent';
import { useLocalStoreState } from 'hooks/useLocalStoreState';
import { useResizeToCollapseSidebar } from 'hooks/useResizeToCollapse';
import { buildAvaContext, buildAvaIframeSrc, IAvaContext } from 'lib/ava/context';
import {
    CHAT_SIDEBAR_WIDTH_KEY,
    ChatSidebarWidthValue,
    SIDEBAR_ENTITY,
} from 'lib/local-store/const';
import { AVA_ORIGIN } from 'lib/public-config';
import { KeyMap, matchKeyMap } from 'lib/utils/keyboard';
import { navigateWithinEnv } from 'lib/utils/query-string';
import { Message } from 'ui/Message/Message';
import { currentEnvironmentSelector } from 'redux/environment/selector';
import { setCollapsed } from 'redux/querybookUI/action';
import { Dispatch, IStoreState } from 'redux/store/types';
import { Icon } from 'ui/Icon/Icon';
import { Sidebar } from 'ui/Sidebar/Sidebar';

import { EntitySidebar } from './EntitySidebar';
import { EnvironmentDropdownButton } from './EnvironmentDropdownButton';
import { EnvironmentIcon } from './EnvironmentIcon';
import { EnvironmentTopbar } from './EnvironmentTopbar';
import { Entity } from './types';

import './EnvironmentAppSidebar.scss';

// Minimum width, and the default width for every non-chat sidebar entity.
const DEFAULT_SIDEBAR_WIDTH = 320;
// The Ava chat iframe is cramped at 320px, so it opens wider by default.
const DEFAULT_CHAT_SIDEBAR_WIDTH = 480;

export const EnvironmentAppSidebar: React.FunctionComponent = () => {
    const theme = useSelector(
        (state: IStoreState) => state.user.computedSettings.theme
    );
    const { routeContext, dataDocContext } = React.useContext(AvaHostContext);

    const collapsed: boolean = useSelector(
        (state: IStoreState) => state.querybookUI.isEnvCollapsed
    );
    const dispatch: Dispatch = useDispatch();
    const [entity, setEntity] = useLocalStoreState<Entity>({
        storeKey: SIDEBAR_ENTITY,
        defaultValue: 'datadoc',
    });

    const currentEnvironment = useSelector(currentEnvironmentSelector);
    const adhocExecutionId = useSelector((state: IStoreState) =>
        currentEnvironment?.id != null
            ? state.adhocQuery[currentEnvironment.id]?.executionId
            : null
    );
    const adhocEngineId = useSelector((state: IStoreState) =>
        currentEnvironment?.id != null
            ? state.adhocQuery[currentEnvironment.id]?.engineId
            : null
    );

    const avaContext: IAvaContext = React.useMemo(
        () =>
            buildAvaContext({
                environment: currentEnvironment,
                routeContext,
                adhocExecutionId,
                adhocEngineId,
                dataDocContext,
            }),
        [
            adhocEngineId,
            adhocExecutionId,
            currentEnvironment,
            dataDocContext,
            routeContext,
        ]
    );

    const avaSrc = React.useMemo(
        () => buildAvaIframeSrc(AVA_ORIGIN, theme === 'dark' ? 'dark' : 'light'),
        [theme]
    );

    const isChat = entity === 'chat';

    // Persisted width for the Ava chat panel — remembered across sessions so
    // users don't have to widen it every time.
    const [storedChatWidth, setStoredChatWidth] =
        useLocalStoreState<ChatSidebarWidthValue>({
            storeKey: CHAT_SIDEBAR_WIDTH_KEY,
            defaultValue: DEFAULT_CHAT_SIDEBAR_WIDTH,
        });

    // Width the sidebar should use for the current entity. Chat uses the
    // persisted width when it's valid, otherwise the chat default — a corrupt
    // or out-of-range stored value falls back to 480 rather than the bare
    // minimum. Every other entity uses the standard width.
    const hasValidStoredChatWidth =
        Number.isFinite(storedChatWidth) &&
        storedChatWidth >= DEFAULT_SIDEBAR_WIDTH;
    const resolvedWidth = isChat
        ? hasValidStoredChatWidth
            ? storedChatWidth
            : DEFAULT_CHAT_SIDEBAR_WIDTH
        : DEFAULT_SIDEBAR_WIDTH;

    // Controlled width applied while mounted, updated live during a drag.
    const [sidebarWidth, setSidebarWidth] =
        React.useState<number>(resolvedWidth);

    // Re-sync when the resolved width changes (entity switch, async load of the
    // persisted width) or when the sidebar is expanded after a collapse — a
    // drag-to-collapse would otherwise leave the local width at the minimum.
    React.useEffect(() => {
        if (!collapsed) {
            setSidebarWidth(resolvedWidth);
        }
    }, [collapsed, resolvedWidth]);

    const handleEntitySelect = React.useCallback(
        (newEntity: Entity | null) => {
            setEntity((oldEntity) => {
                if (collapsed) {
                    dispatch(setCollapsed(false));
                } else if (newEntity === oldEntity) {
                    // Collapse sidebar if the entity is the same
                    dispatch(setCollapsed(true));
                }

                return newEntity;
            });
        },
        [dispatch, collapsed, setEntity]
    );

    // Tracks whether the in-progress drag collapsed the sidebar, so a
    // collapse gesture isn't mistaken for (and persisted as) a resize.
    const collapsedDuringResize = React.useRef(false);

    const resizeToCollapseSidebar = useResizeToCollapseSidebar(
        DEFAULT_SIDEBAR_WIDTH,
        1 / 3,
        React.useCallback(() => {
            collapsedDuringResize.current = true;
            dispatch(setCollapsed(true));
        }, [dispatch])
    );

    const handleResizeStart = React.useCallback(() => {
        collapsedDuringResize.current = false;
    }, []);

    const handleResize = React.useCallback(
        (event: Event, direction: string, elementRef: HTMLElement) => {
            // Keep the controlled width in sync while the user drags. Use
            // clientWidth to match the basis useResizeToCollapseSidebar checks.
            setSidebarWidth(elementRef.clientWidth);
            resizeToCollapseSidebar(event, direction, elementRef);
        },
        [resizeToCollapseSidebar]
    );

    const handleResizeStop = React.useCallback(
        (_event: Event, _direction: string, elementRef: HTMLElement) => {
            // Persist genuine resizes only, not a drag that collapsed the
            // sidebar (which ends at the minimum width).
            if (isChat && !collapsedDuringResize.current) {
                setStoredChatWidth(elementRef.clientWidth);
            }
        },
        [isChat, setStoredChatWidth]
    );

    const handleCollapseKeyDown = React.useCallback(
        (evt) => {
            if (matchKeyMap(evt, KeyMap.overallUI.toggleSidebar)) {
                dispatch(setCollapsed(!collapsed));
                evt.stopPropagation();
                evt.preventDefault();
            }
        },
        [collapsed, dispatch]
    );

    useEvent('keydown', handleCollapseKeyDown);

    let navigator: React.ReactNode;
    if (!collapsed) {
        navigator =
            entity === 'datadoc' ? (
                <DataDocNavigator />
            ) : entity === 'table' ? (
                <DataDocSchemaNavigator />
            ) : entity === 'snippet' ? (
                <QuerySnippetNavigator
                    onQuerySnippetSelect={(querySnippet) =>
                        navigateWithinEnv(
                            `/query_snippet/${querySnippet.id}/`,
                            {
                                isModal: true,
                            }
                        )
                    }
                />
            ) : entity === 'execution' ? (
                <QueryViewNavigator />
            ) : entity === 'review' ? (
                <QueryReviewsNavigator />
            ) : entity === 'chat' ? (
                avaSrc ? (
                    <IFrameNavigator
                        src={avaSrc}
                        message={avaContext}
                        targetOrigin={AVA_ORIGIN}
                    />
                ) : (
                    <Message
                        title="Ava is unavailable"
                        message="The configured Ava origin is invalid."
                        type="error"
                    />
                )
            ) : (
                <div />
            );
    }

    const collapseButton = (
        <span
            onClick={() => dispatch(setCollapsed(!collapsed))}
            className="collapse-sidebar-button"
        >
            <Icon name={collapsed ? 'ChevronRight' : 'ChevronLeft'} />
        </span>
    );

    const environmentPickerSection = collapsed ? (
        <div className="collapsed-env flex-center">
            <EnvironmentDropdownButton
                customButtonRenderer={() => (
                    <EnvironmentIcon
                        disabled={false}
                        selected={true}
                        environmentName={currentEnvironment.name}
                    />
                )}
            />
        </div>
    ) : (
        <EnvironmentTopbar />
    );

    const envPickerClassName = clsx({
        'sidebar-environment-picker': true,
        'flex-center': collapsed,
    });

    const contentDOM = (
        <>
            <div className="EnvironmentAppSidebar-content">
                <div className={envPickerClassName}>
                    {environmentPickerSection}
                </div>
                <div className="sidebar-content-main">
                    <EntitySidebar
                        selectedEntity={entity}
                        onSelectEntity={handleEntitySelect}
                    />
                    <div className="sidebar-content-main-navigator">
                        {navigator}
                    </div>
                </div>
                {collapseButton}
            </div>
        </>
    );

    const className = clsx({
        EnvironmentAppSidebar: true,
        collapsed,
    });

    return collapsed ? (
        <div className={className}>{contentDOM}</div>
    ) : (
        <Sidebar
            className={className}
            size={{ width: sidebarWidth, height: '100%' }}
            minWidth={DEFAULT_SIDEBAR_WIDTH}
            onResizeStart={handleResizeStart}
            onResize={handleResize}
            onResizeStop={handleResizeStop}
        >
            {contentDOM}
        </Sidebar>
    );
};
