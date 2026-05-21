import React, { useMemo, useState } from 'react';
import { useSelector } from 'react-redux';
import styled from 'styled-components';

import {
    IDataSchema,
    SchemaSortKey,
    SchemaTableSortKey
} from 'const/metastore';
import { useIntersectionObserver } from 'hooks/useIntersectionObserver';
import { defaultSortSchemaTableBy } from 'redux/dataTableSearch/const';
import { ITableSearchResult } from 'redux/dataTableSearch/types';
import { IStoreState } from 'redux/store/types';
import { IconButton } from 'ui/Button/IconButton';
import { Icon } from 'ui/Icon/Icon';
import { OrderByButton } from 'ui/OrderByButton/OrderByButton';
import { Title } from 'ui/Title/Title';

import { SchemaTableItem } from '../SchemaTableView/SchemaTableItem';

import './CatalogItem.scss';

// Reads only its own schema's tables/count from Redux — prevents the whole
// CatalogItem (or uncategorized section) from re-rendering when an unrelated schema loads tables.
export const ConnectedSchemaTableItem: React.FC<{
    schema: IDataSchema;
    selectedTableId: number;
    tableRowRenderer: (table: ITableSearchResult) => React.ReactNode;
    sortOrder: { asc: boolean; key: SchemaTableSortKey };
    onSortChanged: (
        sortKey?: SchemaTableSortKey | null,
        sortAsc?: boolean | null
    ) => void;
    onLoadMore: () => Promise<any>;
}> = ({
    schema,
    selectedTableId,
    tableRowRenderer,
    sortOrder,
    onSortChanged,
    onLoadMore
}) => {
    const schemaData = useSelector(
        (state: IStoreState) =>
            state.dataTableSearch.schemas.schemaResultById[schema.id]
    );

    return (
        <SchemaTableItem
            name={schema.name}
            total={schemaData?.count ?? schema.table_count}
            tables={schemaData?.tables ?? []}
            selectedTableId={selectedTableId}
            tableRowRenderer={tableRowRenderer}
            sortOrder={sortOrder}
            onSortChanged={onSortChanged}
            onLoadMore={onLoadMore}
        />
    );
};

const StyledItem = styled.div`
    height: 32px;
`;

const CatalogIconButton = styled(IconButton)`
    padding: 4px;
`;

export const CatalogItem: React.FC<{
    name: string;
    schemaCount: number;
    schemas: IDataSchema[];
    schemasDone: boolean;
    selectedTableId: number;
    tableRowRenderer: (table: ITableSearchResult) => React.ReactNode;
    schemasSortOrder: { asc: boolean; key: SchemaSortKey };
    onSchemasSortChanged: (
        sortKey?: SchemaSortKey | null,
        sortAsc?: boolean | null
    ) => void;
    onLoadMoreSchemas: () => Promise<any>;
    hideEmptySchemas: boolean;
    onSchemaSort: (
        schemaId: number,
        sortKey?: SchemaTableSortKey | null,
        sortAsc?: boolean | null
    ) => void;
    onSchemaLoadMore: (schema: IDataSchema) => Promise<any>;
    schemaSortByIds: Record<number, { asc: boolean; key: SchemaTableSortKey }>;
    isExpanded: boolean;
    onToggle: () => void;
}> = ({
    name,
    schemaCount,
    schemas,
    schemasDone,
    selectedTableId,
    tableRowRenderer,
    schemasSortOrder,
    onSchemasSortChanged,
    onLoadMoreSchemas,
    hideEmptySchemas,
    onSchemaSort,
    onSchemaLoadMore,
    schemaSortByIds,
    isExpanded,
    onToggle
}) => {
    const [loadMoreElement, setLoadMoreElement] =
        useState<HTMLDivElement | null>(null);

    useIntersectionObserver({
        intersectElement: loadMoreElement,
        onIntersect: onLoadMoreSchemas,
        deps: [schemas],
        disabled: schemasDone || !isExpanded
    });

    const visibleSchemas = useMemo(
        () =>
            hideEmptySchemas
                ? (schemas ?? []).filter((s) => s.table_count > 0)
                : schemas ?? [],
        [schemas, hideEmptySchemas]
    );

    return (
        <div className="CatalogItem mb12">
            <StyledItem className="horizontal-space-between navigator-header pl8">
                <div
                    className="catalog-name flex1 flex-row"
                    onClick={() => onToggle()}
                >
                    <Icon name="BookOpen" size={14} />
                    <Title size="small" className="one-line-ellipsis ml4">
                        {name}
                    </Title>
                    <span className="catalog-label">Catalog</span>
                </div>
                <OrderByButton
                    asc={schemasSortOrder.asc}
                    orderByField={
                        schemasSortOrder.key === 'name' ? 'Name' : 'Table Count'
                    }
                    orderByFieldSymbol={
                        schemasSortOrder.key === 'name' ? 'Aa' : 'Tc'
                    }
                    onAscToggle={() =>
                        onSchemasSortChanged(null, !schemasSortOrder.asc)
                    }
                    onOrderByFieldToggle={() =>
                        onSchemasSortChanged(
                            schemasSortOrder.key === 'name'
                                ? 'table_count'
                                : 'name'
                        )
                    }
                />
                <div className="flex-row">
                    <CatalogIconButton
                        onClick={() => onToggle()}
                        icon={isExpanded ? 'ChevronDown' : 'ChevronRight'}
                    />
                </div>
            </StyledItem>

            {isExpanded && (
                <div className="catalog-schemas">
                    {schemaCount === 0 ? (
                        <div className="empty-section-message">
                            No schemas in {name}
                        </div>
                    ) : (
                        <>
                            {visibleSchemas.map((schema) => {
                                const schemaSortOrder =
                                    schemaSortByIds[schema.id] ??
                                    defaultSortSchemaTableBy;
                                return (
                                    <ConnectedSchemaTableItem
                                        key={schema.id}
                                        schema={schema}
                                        selectedTableId={selectedTableId}
                                        tableRowRenderer={tableRowRenderer}
                                        sortOrder={schemaSortOrder}
                                        onSortChanged={(sortKey, sortAsc) =>
                                            onSchemaSort(
                                                schema.id,
                                                sortKey,
                                                sortAsc
                                            )
                                        }
                                        onLoadMore={() =>
                                            onSchemaLoadMore(schema)
                                        }
                                    />
                                );
                            })}
                            <div ref={setLoadMoreElement} />
                        </>
                    )}
                </div>
            )}
        </div>
    );
};
