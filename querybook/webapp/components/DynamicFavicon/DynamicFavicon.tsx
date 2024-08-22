import React, { useEffect } from 'react';
import { useSelector } from 'react-redux';

import { useActiveQueryExecutions } from 'components/QueryExecutionButton/QueryExecutionButton';
import { IStoreState } from 'redux/store/types';

let intervalId: number | null = null;
let animationRunning: boolean = false;
let currentFrame = 0;
const frames = [
    '/static/favicon/querybook-busy-1.svg',
    '/static/favicon/querybook-busy-2.svg',
    '/static/favicon/querybook-busy-3.svg',
    '/static/favicon/querybook-busy-4.svg',
];

const updateFavicon = (isActive: boolean) => {
    const favicon = document.querySelector(
        'link[rel~="icon"]'
    ) as HTMLLinkElement;

    const startAnimation = () => {
        animationRunning = true;
        if (intervalId) {
            clearInterval(intervalId);
        }
        intervalId = window.setInterval(() => {
            favicon.href = frames[currentFrame];
            currentFrame = (currentFrame + 1) % frames.length;
        }, 1000);
    };

    const stopAnimation = () => {
        animationRunning = false;
        if (intervalId) {
            clearInterval(intervalId);
            intervalId = null;
        }
    };

    if (favicon) {
        if (!isActive) {
            favicon.href = '/static/favicon/querybook.svg';
            stopAnimation();
        } else {
            if (!animationRunning) {
                startAnimation();
            }
        }
    }
};

export const DynamicFavicon: React.FC = () => {
    const { activeQueryExecutions } = useActiveQueryExecutions();
    const animateFavicon = useSelector(
        (state: IStoreState) =>
            state.user.computedSettings.spin_favicon_on_query === 'enabled'
    );
    useEffect(() => {
        updateFavicon(
            animateFavicon ? activeQueryExecutions.length > 0 : false
        );

        return () => {
            updateFavicon(false);
            if (intervalId) {
                clearInterval(intervalId);
            }
        };
    }, [activeQueryExecutions, animateFavicon]);

    return null;
};
