import { startCase } from 'lodash';
import React, { useCallback, useEffect, useMemo, useRef } from 'react';
import { useDispatch, useSelector } from 'react-redux';

import { EntitySelect } from 'components/Search/EntitySelect';
import { ComponentType, ElementType } from 'const/analytics';
import { IQueryMetastore } from 'const/metastore';
import { useToggleState } from 'hooks/useToggleState';
import { trackClick } from 'lib/analytics';
import {
    changeCatalogsSort,
    changeSchemasSort,
    updateTableSort,
} from 'redux/dataTableSearch/action';
import { ITableSearchFilters } from 'redux/dataTableSearch/types';
import { IStoreState } from 'redux/store/types';
import { DataElementResource, TableTagResource } from 'resource/table';
import { SoftButton } from 'ui/Button/Button';
import { IconButton } from 'ui/Button/IconButton';
import { OrderByButton } from 'ui/OrderByButton/OrderByButton';
import { Popover } from 'ui/Popover/Popover';
import { SearchBar } from 'ui/SearchBar/SearchBar';
import { Title } from 'ui/Title/Title';
import { ToggleSwitch } from 'ui/ToggleSwitch/ToggleSwitch';
import { TrendingFlame } from 'ui/TrendingFlame/TrendingFlame';

import './DataTableNavigatorSearch.scss';

export const DataTableNavigatorSearch: React.FC<{
    queryMetastore: IQueryMetastore;
    searchString: string;
    onSearch: (s: string) => void;
    searchFilters: ITableSearchFilters;
    updateSearchFilter: <K extends keyof ITableSearchFilters>(
        filterKey: K,
        filterVal: ITableSearchFilters[K]
    ) => void;
    resetSearchFilter: () => void;

    showTableSearchResult: boolean;
    showCatalogView: boolean;
    hideEmptySchemas: boolean;
    onHideEmptySchemasChange: (v: boolean) => void;
}> = ({
    queryMetastore,
    searchString,
    onSearch,
    searchFilters,
    updateSearchFilter,
    resetSearchFilter,

    showTableSearchResult,
    showCatalogView,
    hideEmptySchemas,
    onHideEmptySchemasChange,
}) => {
    const [showSearchFilter, , toggleSearchFilter] = useToggleState(false);
    const filterButtonRef = useRef<HTMLAnchorElement>();
    const searchFiltersSize = useMemo(
        () => Object.keys(searchFilters).length,
        [searchFilters]
    );

    useEffect(() => {
        resetSearchFilter();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [queryMetastore]);

    const { asc: sortTableAsc, key: sortTableKey } = useSelector(
        (state: IStoreState) => state.dataTableSearch.sortTablesBy
    );

    const { key: sortSchemaKey, asc: sortSchemaAsc } = useSelector(
        (state: IStoreState) => state.dataTableSearch.schemas.sortSchemasBy
    );

    const { key: sortCatalogKey, asc: sortCatalogAsc } = useSelector(
        (state: IStoreState) => state.dataTableSearch.catalogs.sortCatalogsBy
    );

    const updateTags = useCallback(
        (newTags: string[]) => {
            updateSearchFilter('tags', newTags.length ? newTags : null);
        },
        [updateSearchFilter]
    );

    const dispatch = useDispatch();

    // Hardcoding to true to always show data elements filter
    // Since Data Elements are stored per-metastore, the default behavior doesn't work
    // if the same Data Elements are used across metastores
    const queryMetastoreHasDataElements = true; // !!queryMetastore.flags?.has_data_element;
    const showCatalogFilter = queryMetastore?.catalog_display_config?.show_catalog_in_ui ?? false;

    const searchFiltersPickerDOM = showSearchFilter && (
        <Popover
            onHide={toggleSearchFilter}
            anchor={filterButtonRef.current}
            layout={['right', 'top']}
        >
            <div className="DataTableNavigatorSearchFilter">
                <SoftButton
                    title="Reset"
                    className="filter-reset-button"
                    size="small"
                    onClick={resetSearchFilter}
                />
                <div>
                    <SearchFilterRow
                        title="Trending"
                        className="toggle-padding"
                    >
                        <div className="flex-row">
                            <ToggleSwitch
                                checked={searchFilters.golden}
                                onChange={(checked) =>
                                    updateSearchFilter(
                                        'golden',
                                        checked ? true : null
                                    )
                                }
                            />
                            <TrendingFlame className="ml4" />
                        </div>
                    </SearchFilterRow>
                    {showCatalogFilter && (
                        <SearchFilterRow title="Catalog">
                            <SearchBar
                                value={searchFilters?.catalog ?? ''}
                                onSearch={(s: string) =>
                                    updateSearchFilter(
                                        'catalog',
                                        s.length ? s : null
                                    )
                                }
                                placeholder="Full catalog name"
                            />
                        </SearchFilterRow>
                    )}
                    <SearchFilterRow
                        title="Hide empty schemas"
                        className="toggle-padding"
                    >
                        <ToggleSwitch
                            checked={hideEmptySchemas}
                            onChange={onHideEmptySchemasChange}
                        />
                    </SearchFilterRow>
                    <SearchFilterRow title="Schema">
                        <SearchBar
                            value={searchFilters?.schema ?? ''}
                            onSearch={(s: string) =>
                                updateSearchFilter(
                                    'schema',
                                    s.length ? s : null
                                )
                            }
                            placeholder="Full schema name"
                        />
                    </SearchFilterRow>
                    {queryMetastoreHasDataElements && (
                        <SearchFilterRow title="Data Elements">
                            <EntitySelect
                                selectedEntities={
                                    searchFilters?.data_elements || []
                                }
                                loadEntities={DataElementResource.search}
                                onEntitiesChange={(dataElements) =>
                                    updateSearchFilter(
                                        'data_elements',
                                        dataElements.length
                                            ? dataElements
                                            : null
                                    )
                                }
                                placeholder="data elements"
                            />
                        </SearchFilterRow>
                    )}
                    <SearchFilterRow title="Tags">
                        <EntitySelect
                            selectedEntities={searchFilters?.tags || []}
                            loadEntities={TableTagResource.search}
                            onEntitiesChange={updateTags}
                            placeholder="Tag name"
                            mini
                        />
                    </SearchFilterRow>
                </div>
            </div>
        </Popover>
    );

    return (
        <div className="DataTableNavigatorSearch flex-row">
            <SearchBar
                value={searchString}
                onSearch={onSearch}
                placeholder="Search by Name"
                transparent
            />

            {showTableSearchResult && (
                <OrderByButton
                    className="mr4"
                    asc={sortTableAsc}
                    hideAscToggle={sortTableKey === 'relevance'}
                    orderByField={startCase(sortTableKey)}
                    orderByFieldSymbol={sortTableKey === 'name' ? 'Aa' : 'Rl'}
                    onAscToggle={() => {
                        dispatch(updateTableSort(null, !sortTableAsc));
                    }}
                    onOrderByFieldToggle={() => {
                        trackClick({
                            component: ComponentType.TABLE_NAVIGATOR_SEARCH,
                            element: ElementType.TABLE_ORDER_BY_BUTTON,
                        });
                        dispatch(
                            updateTableSort(
                                sortTableKey === 'name' ? 'relevance' : 'name'
                            )
                        );
                    }}
                />
            )}

            {!showTableSearchResult && showCatalogView && (
                <OrderByButton
                    className="mr4"
                    asc={sortCatalogAsc}
                    orderByField={sortCatalogKey === 'name' ? 'Name' : 'Schema Count'}
                    orderByFieldSymbol={sortCatalogKey === 'name' ? 'Aa' : 'Sc'}
                    onAscToggle={() => {
                        dispatch(changeCatalogsSort(null, !sortCatalogAsc));
                    }}
                    onOrderByFieldToggle={() => {
                        dispatch(
                            changeCatalogsSort(
                                sortCatalogKey === 'name' ? 'schema_count' : 'name'
                            )
                        );
                    }}
                />
            )}

            {!showTableSearchResult && !showCatalogView && (
                <OrderByButton
                    className="mr4"
                    asc={sortSchemaAsc}
                    orderByField={startCase(sortSchemaKey)}
                    orderByFieldSymbol={sortSchemaKey === 'name' ? 'Aa' : 'Tc'}
                    onAscToggle={() => {
                        dispatch(changeSchemasSort(null, !sortSchemaAsc));
                    }}
                    onOrderByFieldToggle={() => {
                        dispatch(
                            changeSchemasSort(
                                sortSchemaKey === 'table_count'
                                    ? 'name'
                                    : 'table_count'
                            )
                        );
                    }}
                />
            )}

            <IconButton
                ref={filterButtonRef}
                size={'18px'}
                className="table-search-filter-button"
                noPadding
                onClick={toggleSearchFilter}
                icon="Sliders"
                active={searchFiltersSize > 0}
                ping={searchFiltersSize > 0 ? String(searchFiltersSize) : null}
            />
            {searchFiltersPickerDOM}
        </div>
    );
};

const SearchFilterRow: React.FC<{ title: string; className?: string }> = ({
    title,
    children,
    className,
}) => (
    <div className={`search-filter-row ${className ?? ''}`}>
        <Title className="mr8 search-filter-title" size="xsmall">
            {title}
        </Title>
        <div className="search-filter-row-item">{children}</div>
    </div>
);
