import clsx from 'clsx';
import React from 'react';

import { Icon } from 'ui/Icon/Icon';

import './TrendingFlame.scss';

export const TrendingFlame: React.FunctionComponent<{
    className?: string;
    showTooltip?: boolean;
    tooltip?: string;
    tooltipPos?: string;
}> = ({ className, showTooltip = true, tooltip, tooltipPos = 'down' }) => (
    <span
        className={clsx('TrendingFlame', 'flex-row', className)}
        {...(showTooltip
            ? {
                  'aria-label': tooltip ?? 'Trending in Trino usage via PUMA',
                  'data-balloon-pos': tooltipPos,
              }
            : {})}
    >
        <Icon name="Flame" />
    </span>
);
