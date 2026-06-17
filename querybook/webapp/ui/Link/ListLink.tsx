import clsx from 'clsx';
import * as React from 'react';

import { Icon } from 'ui/Icon/Icon';
import type { AllLucideIconNames } from 'ui/Icon/LucideIcons';
import { StyledText, UntitledText } from 'ui/StyledText/StyledText';

import { ILinkProps, Link } from './Link';

import './ListLink.scss';

interface IProps extends ILinkProps {
    className?: string;
    title?: string;
    noPlaceHolder?: boolean;
    icons?: AllLucideIconNames[];
    customIcons?: React.ReactNode[];
    isRow?: boolean;
}

export const ListLink: React.FunctionComponent<IProps> = React.memo(
    ({
        className,
        title,
        icons,
        customIcons,
        isRow,
        noPlaceHolder = false,
        children,
        ...listProps
    }) => {
        const mergedClassName = clsx({
            ListLink: true,
            [className]: !!className,
            row: isRow,
        });
        return (
            <Link className={mergedClassName} {...listProps}>
                {title ? (
                    <StyledText className="ListLinkText" size="small">
                        {title}
                    </StyledText>
                ) : noPlaceHolder ? null : (
                    <UntitledText
                        className="ListLinkPlaceholder"
                        size="small"
                    />
                )}
                {icons &&
                    icons.map((icon) => (
                        <Icon key={icon} name={icon} size={16} />
                    ))}
                {customIcons &&
                    customIcons.map((icon, i) => (
                        <React.Fragment key={i}>{icon}</React.Fragment>
                    ))}
                {children}
            </Link>
        );
    }
);
