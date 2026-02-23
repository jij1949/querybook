import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import styled from 'styled-components';

import { SchemaTableSortKey } from 'const/metastore';
import { useIntersectionObserver } from 'hooks/useIntersectionObserver';
import { getSchemaDisplayName } from 'lib/utils/table-identifier';
import {
    changeTableSort,
    searchSchemas,
    searchTableBySchema,
} from 'redux/dataTableSearch/action';
import { defaultSortSchemaTableBy } from 'redux/dataTableSearch/const';
import type { ITableSearchResult } from 'redux/dataTableSearch/types';
import { Dispatch, IStoreState } from 'redux/store/types';

import { SchemaTableItem } from './SchemaTableItem';

const SchemasList = styled.div`
    flex: 1 1 200px;
    overflow-y: auto;
`;

const IntersectionElement = styled.div`
    width: 100%;
    height: 1px;
`;

export const SchemaTableView: React.FunctionComponent<{
    tableRowRenderer: (table: ITableSearchResult) => React.ReactNode;
    selectedTableId: number;
}> = ({ tableRowRenderer, selectedTableId }) => {
    const schemas = useSelector(
        (state: IStoreState) => state.dataTableSearch.schemas
    );
    const metastoreId = useSelector(
        (state: IStoreState) => state.dataTableSearch.metastoreId
    );
    const metastore = useSelector(
        (state: IStoreState) =>
            state.dataSources.queryMetastoreById[metastoreId]
    );

    const dispatch: Dispatch = useDispatch();
    const [intersectElement, setIntersectElement] =
        useState<HTMLDivElement>(null);

    useIntersectionObserver({
        intersectElement,
        onIntersect: () => {
            dispatch(searchSchemas());
        },
        deps: [schemas.schemaIds],
        disabled: schemas.done,
    });

    return (
        <SchemasList>
            {schemas.schemaIds.map((schemaId) => {
                const schema = schemas.schemaResultById[schemaId];
                const schemaSortOrder =
                    schemas.schemaSortByIds[schemaId] ??
                    defaultSortSchemaTableBy;
                
                // Determine if we should show catalog based on metastore settings
                const showCatalog =
                    metastore?.catalog_display_config?.show_catalog_in_ui ??
                    false;
                const schemaDisplayName = getSchemaDisplayName(
                    schema,
                    showCatalog
                );

                return (
                    <SchemaTableItem
                        key={`${schema.id}-${schemaDisplayName}`}
                        name={schemaDisplayName}
                        total={schema.count}
                        tables={schema.tables}
                        sortOrder={schemaSortOrder}
                        selectedTableId={selectedTableId}
                        tableRowRenderer={tableRowRenderer}
                        onSortChanged={(
                            sortKey?: SchemaTableSortKey | null,
                            sortAsc?: boolean | null
                        ) =>
                            dispatch(
                                changeTableSort(schema.id, sortKey, sortAsc)
                            )
                        }
                        onLoadMore={() =>
                            dispatch(
                                searchTableBySchema(
                                    schema.name,
                                    schema.id,
                                    schema.catalog?.name
                                )
                            )
                        }
                    />
                );
            })}

            <IntersectionElement ref={setIntersectElement} />
        </SchemasList>
    );
};
