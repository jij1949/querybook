import clsx from 'clsx';
import React from 'react';

import { Center } from 'ui/Center/Center';
import { FullHeight } from 'ui/FullHeight/FullHeight';
import { Icon } from 'ui/Icon/Icon';
import { Subtitle, Title } from 'ui/Title/Title';

export const ExpediaOktaError: React.FunctionComponent = () => {
    const classNameProp = clsx({
        ErrorPage: true,
    });

    console.log(location);

    return (
        <FullHeight className={classNameProp}>
            <Center className="flex-column">
                <Icon name="ShieldAlert" size={96} />
                <Title size="xxlarge" className="mb24">
                    Oops!
                </Title>

                <Subtitle className="ErrorPage-message mb16">
                    You aren't assigned the <strong>Querybook</strong> app in
                    Okta. Please refer to the following link to request access:
                </Subtitle>

                <Subtitle className="ErrorPage-message mb16">
                    <a
                        style={{ fontWeight: 'bold' }}
                        href="https://confluence.expedia.biz/display/DSPKB/Querybook+Access"
                    >
                        Querybook Access Request
                    </a>
                </Subtitle>
            </Center>
        </FullHeight>
    );
};
