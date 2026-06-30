import { debounce } from 'lodash';
import React, { ReactElement, useMemo } from 'react';
import toast from 'react-hot-toast';
import AsyncCreatableSelect, {
    Props as AsyncCreatableProps,
} from 'react-select/async-creatable';
import * as Yup from 'yup';

import { UserBadge } from 'components/UserBadge/UserBadge';
import {
    makeReactSelectStyle,
    multiCreatableReactSelectStyles,
} from 'lib/utils/react-select';
import { SearchUserResource } from 'resource/search';
import { overlayRoot } from 'ui/Overlay/Overlay';
import { AccentText } from 'ui/StyledText/StyledText';

interface IUserSearchResultRow {
    id: number;
    username: string;
    fullname: string;
}

interface ISelectFreeOption {
    label?: string | ReactElement;
    value: string;
}

interface ISelectUserOption {
    label?: string | ReactElement;
    value: number;
    isUser: boolean;
}

type ISelectOption = ISelectFreeOption | ISelectUserOption;

function getUserName(user: IUserSearchResultRow) {
    return (user.fullname || user.username || 'Unknown').trim();
}

const loadOptions = debounce(
    (name, callback) => {
        SearchUserResource.search({ name }).then(({ data }) => {
            callback(
                data.map((user: IUserSearchResultRow) => ({
                    value: user.id,
                    label: (
                        <UserBadge
                            uid={user.id}
                            name={getUserName(user)}
                            mini
                        />
                    ),
                    isUser: true,
                }))
            );
        });
    },
    1000,
    {
        leading: true,
    }
);

interface IUserSelectProps {
    value: ISelectOption[] | undefined;
    onChange: (values: ISelectOption[]) => any;
    usePortalMenu?: boolean;
    // When true, free-text (non-user) options are validated as email addresses.
    // Leave false for non-email targets such as Slack channels or Teams.
    validateEmail?: boolean;
    selectProps?: Partial<AsyncCreatableProps<any, boolean>>;
}

export const MultiCreatableUserSelect: React.FunctionComponent<
    IUserSelectProps
> = ({
    value,
    onChange,
    usePortalMenu = true,
    validateEmail = false,
    selectProps = {},
}) => {
    const [searchText, setSearchText] = React.useState('');
    const userReactSelectStyle = React.useMemo(
        () =>
            makeReactSelectStyle(
                usePortalMenu,
                multiCreatableReactSelectStyles
            ),
        [usePortalMenu]
    );
    if (usePortalMenu) {
        selectProps.menuPortalTarget = overlayRoot;
    }

    // Helper to check if an option is a user (not email)
    const isUserOption = (option: ISelectOption): option is ISelectUserOption =>
        'isUser' in option && option.isUser;

    const valueWithLabel = useMemo(
        () =>
            (value ?? []).map((v) => ({
                ...v,
                label:
                    v.label ??
                    (isUserOption(v) ? (
                        <UserBadge uid={v.value} mini />
                    ) : (
                        v.value
                    )),
            })),
        [value]
    );

    const handleChange = (newValues: ISelectOption[]) => {
        // Validate all email options
        if (validateEmail) {
            const invalidEmail = newValues.find((option) => {
                if (isUserOption(option)) {
                    return false;
                }

                const email = String(option.value).trim();
                return (
                    !email ||
                    !Yup.string().email().required().isValidSync(email)
                );
            });

            if (invalidEmail) {
                const email = String(invalidEmail.value).trim();
                toast.error(`Invalid email address: "${email}"`);
                setSearchText(email);
                return;
            }
        }

        // Silently trim email values and labels before passing to parent
        const trimmedValues = newValues.map((v) => {
            if (isUserOption(v)) {
                return v;
            }
            const trimmedValue = String(v.value).trim();
            return {
                ...v,
                value: trimmedValue,
                label:
                    typeof v.label === 'string' ? v.label.trim() : trimmedValue,
            };
        });

        onChange(trimmedValues);
    };

    return (
        <AccentText>
            <AsyncCreatableSelect
                styles={userReactSelectStyle}
                loadOptions={loadOptions}
                defaultOptions={[]}
                inputValue={searchText}
                onInputChange={(text) => setSearchText(text)}
                noOptionsMessage={() => (searchText ? 'No user found.' : null)}
                allowCreateWhileLoading
                onChange={handleChange}
                value={valueWithLabel}
                isMulti
                {...selectProps}
            />
        </AccentText>
    );
};
