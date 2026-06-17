import qs from 'qs';
import * as React from 'react';
import { useDispatch, useSelector } from 'react-redux';

import { ITag } from 'const/tag';
import { stopPropagationAndDefault } from 'lib/utils/noop';
import { navigateWithinEnv } from 'lib/utils/query-string';
import { useRankedTags } from 'lib/utils/tag';
import { Dispatch, IStoreState } from 'redux/store/types';
import {
    deleteTableTag,
    fetchTableTagsFromTableIfNeeded,
} from 'redux/tag/action';
import { tagsInTableSelector } from 'redux/tag/selector';
import { ContextMenu } from 'ui/ContextMenu/ContextMenu';
import { Icon } from 'ui/Icon/Icon';
import { Menu, MenuItem } from 'ui/Menu/Menu';
import { HoverIconTag } from 'ui/Tag/HoverIconTag';

import { CatalogTypeIcon } from 'components/CatalogTypeIcon/CatalogTypeIcon';
import { getCatalogType } from 'lib/utils/catalog-type';

import { CreateDataTableTag } from './CreateDataTableTag';
import { TableTagConfigModal } from './TableTagConfigModal';

import './DataTableTags.scss';

interface IProps {
    tableId: number;
    readonly?: boolean;
    mini?: boolean;
    showType?: boolean;
}

export const DataTableTags: React.FunctionComponent<IProps> = ({
    tableId,
    readonly = false,
    mini = false,
    showType = true,
}) => {
    const isUserAdmin = useSelector(
        (state: IStoreState) => state.user.myUserInfo.isAdmin
    );
    const dispatch: Dispatch = useDispatch();
    const loadTags = React.useCallback(
        () => dispatch(fetchTableTagsFromTableIfNeeded(tableId)),
        [tableId]
    );
    const deleteTag = React.useCallback(
        (tagName: string) => dispatch(deleteTableTag(tableId, tagName)),
        [tableId]
    );

    const tags = useRankedTags(
        useSelector((state: IStoreState) => tagsInTableSelector(state, tableId))
    );

    React.useEffect(() => {
        loadTags();
    }, []);

    const listDOM = (tags || [])
        .filter((tag) => tag.meta?.hidden !== true)
        .map((tag) => (
            <TableTag
                tag={tag}
                readonly={readonly}
                deleteTag={deleteTag}
                key={tag.id}
                isUserAdmin={isUserAdmin}
                mini={mini}
                showType={showType}
            />
        ));

    return (
        <div className="DataTableTags flex-row">
            {listDOM}
            {readonly ? null : (
                <CreateDataTableTag tableId={tableId} tags={tags} />
            )}
        </div>
    );
};

export const TableTag: React.FC<{
    tag: ITag;

    isUserAdmin?: boolean;
    readonly?: boolean;
    deleteTag?: (tagName: string) => void;
    mini?: boolean;
    showType?: boolean;
}> = ({ tag, readonly, deleteTag, isUserAdmin, mini, showType = true }) => {
    const tagMeta = tag.meta ?? {};
    const tagRef = React.useRef<HTMLSpanElement>();
    const [showConfigModal, setShowConfigModal] = React.useState(false);

    const handleDeleteTag = React.useCallback(
        (e: React.MouseEvent<HTMLSpanElement>) => {
            stopPropagationAndDefault(e);
            deleteTag(tag.name);
        },
        [deleteTag, tag.name]
    );
    const handleTagClick = React.useCallback(() => {
        navigateWithinEnv(
            `/search/?${qs.stringify({
                searchType: 'Table',
                'searchFilters[tags][0]': tag.name,
            })}`,
            {
                isModal: true,
            }
        );
    }, [tag.name]);

    // user can update if it is not readonly and passes the admin check
    const canUserUpdate = !(readonly || (tagMeta.admin && !isUserAdmin));
    const canUserDelete = !readonly && canUserUpdate;

    const renderContextMenu = () => (
        <Menu>
            <MenuItem onClick={() => setShowConfigModal(true)}>
                <Icon name="Settings" className="mr8" size={20} />
                Configure Tag
            </MenuItem>
            <MenuItem onClick={handleDeleteTag}>
                <Icon name="Trash2" className="mr8" size={20} />
                Remove Tag
            </MenuItem>
        </Menu>
    );

    // Split the tag type out of the tag name if included
    // Example: 'File Format: Parquet' -> 'Parquet'
    const tagName = tag.name.startsWith(tagMeta.type + ': ')
        ? tag.name.substring(tagMeta.type.length + 2)
        : tag.name;

    const catalogType = getCatalogType({
        catalogType: tagMeta?.catalog_type,
    });
    const customIcon =
        catalogType !== 'unknown' ? (
            <CatalogTypeIcon type={catalogType} size={12} />
        ) : undefined;

    return (
        <div className="TableTag">
            {canUserUpdate && (
                <ContextMenu
                    anchorRef={tagRef}
                    renderContextMenu={renderContextMenu}
                />
            )}

            {showConfigModal && (
                <TableTagConfigModal
                    tag={tag}
                    onHide={() => setShowConfigModal(false)}
                />
            )}
            <HoverIconTag
                key={tag.id}
                name={tagName}
                type={tagMeta.type}
                icon={tagMeta.icon}
                customIcon={customIcon}
                iconOnHover={canUserDelete ? 'X' : null}
                onIconHoverClick={canUserDelete ? handleDeleteTag : null}
                tooltip={tagMeta.tooltip}
                tooltipPos={'up'}
                color={tagMeta.color}
                onClick={handleTagClick}
                ref={tagRef}
                mini={mini}
                showType={showType}
            />
        </div>
    );
};
