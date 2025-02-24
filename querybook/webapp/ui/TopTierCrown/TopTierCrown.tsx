import clsx from 'clsx';
import React from 'react';

import { Icon } from 'ui/Icon/Icon';

import './TopTierCrown.scss';

export const TopTierCrown: React.FunctionComponent<{
    className?: string;
    showTooltip?: boolean;
    tooltip?: string;
    tooltipPos?: string;
}> = ({ className, showTooltip = true, tooltip, tooltipPos = 'down' }) => (
    <span
        className={clsx('TopTierCrown', 'flex-row', className)}
        {...(showTooltip
            ? {
                  'aria-label':
                      tooltip ??
                      'Platinum or Platinum Candidate designation via Collibra, indicating financial, business, or regulatory impact',
                  'data-balloon-pos': tooltipPos,
                  'data-balloon-length': 'medium',
              }
            : {})}
    >
        <Icon name="Crown" />
    </span>
);
