import React, { useCallback, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import styled from 'styled-components';

import { CatalogSortKey, SchemaTableSortKey } from 'const/metastore';
import { useIntersectionObserver } from 'hooks/useIntersectionObserver';
import {
    changeCatalogSchemaSort,
    changeCatalogsSort,
    changeTableSort,
    searchCatalogs,
    searchSchemasByCatalog,
    searchTableBySchema,
    searchUncategorizedSchemas,
} from 'redux/dataTableSearch/action';
import { defaultCatalogSchemaSortBy, defaultSortSchemaTableBy } from 'redux/dataTableSearch/const';
import { ITableSearchResult } from 'redux/dataTableSearch/types';
import { Dispatch, IStoreState } from 'redux/store/types';

import { CatalogItem, ConnectedSchemaTableItem } from './CatalogItem';

const CatalogList = styled.div`
    flex: 1 1 200px;
    overflow-y: auto;
`;

const IntersectionElement = styled.div`
    width: 100%;
    height: 1px;
`;

export const CatalogTableView: React.FC<{
    tableRowRenderer: (table: ITableSearchResult) => React.ReactNode;
    selectedTableId: number;
    hideEmptySchemas: boolean;
}> = ({
    tableRowRenderer,
    selectedTableId,
    hideEmptySchemas,
}) => {
    const dispatch: Dispatch = useDispatch();
    const [intersectElement, setIntersectElement] =
        useState<HTMLDivElement | null>(null);
    const [uncategorizedSentinel, setUncategorizedSentinel] =
        useState<HTMLDivElement | null>(null);
    const [expandedCatalogIds, setExpandedCatalogIds] = useState<Set<number>>(
        new Set()
    );

    const toggleCatalog = useCallback((catalogId: number) => {
        setExpandedCatalogIds((prev) => {
            const next = new Set(prev);
            if (next.has(catalogId)) {
                next.delete(catalogId);
            } else {
                next.add(catalogId);
            }
            return next;
        });
    }, []);

    const { catalogIds, catalogResultById, sortCatalogsBy, done } = useSelector(
        (state: IStoreState) => state.dataTableSearch.catalogs
    );

    const schemaSortByIds = useSelector(
        (state: IStoreState) => state.dataTableSearch.schemas.schemaSortByIds
    );

    const catalogSchemaSortByIds = useSelector(
        (state: IStoreState) => state.dataTableSearch.catalogs.catalogSchemaSortByIds
    );

    // Uncategorized schemas — schemas loaded in the schemas subtree with no catalog_id
    const uncategorizedSchemas = useSelector((state: IStoreState) =>
        state.dataTableSearch.schemas.schemaIds
            .map((id) => state.dataTableSearch.schemas.schemaResultById[id])
            .filter((s) => !s.catalog_id)
    );

    const uncategorizedDone = useSelector(
        (state: IStoreState) => state.dataTableSearch.schemas.done
    );

    useIntersectionObserver({
        intersectElement,
        onIntersect: () => {
            dispatch(searchCatalogs());
        },
        deps: [catalogIds],
        disabled: done,
    });

    useIntersectionObserver({
        intersectElement: uncategorizedSentinel,
        onIntersect: () => {
            dispatch(searchUncategorizedSchemas());
        },
        deps: [uncategorizedSchemas],
        disabled: uncategorizedDone,
    });

    return (
        <CatalogList>
            {catalogIds.map((catalogId) => {
                const catalog = catalogResultById[catalogId];

                const catalogSchemaSort =
                    catalogSchemaSortByIds[catalogId] ?? defaultCatalogSchemaSortBy;

                return (
                    <CatalogItem
                        key={catalogId}
                        name={catalog.name}
                        schemaCount={catalog.schema_count}
                        schemas={catalog.schemas ?? []}
                        schemasDone={catalog.schemasDone}
                        selectedTableId={selectedTableId}
                        tableRowRenderer={tableRowRenderer}
                        schemasSortOrder={catalogSchemaSort}
                        onSchemasSortChanged={(sortKey, sortAsc) =>
                            dispatch(changeCatalogSchemaSort(catalogId, sortKey, sortAsc))
                        }
                        onLoadMoreSchemas={() =>
                            dispatch(searchSchemasByCatalog(catalogId))
                        }
                        hideEmptySchemas={hideEmptySchemas}
                        onSchemaSort={(schemaId, sortKey, sortAsc) =>
                            dispatch(changeTableSort(schemaId, sortKey, sortAsc))
                        }
                        onSchemaLoadMore={(schema) =>
                            dispatch(
                                searchTableBySchema(
                                    schema.name,
                                    schema.id,
                                    catalog.name
                                )
                            )
                        }
                        schemaSortByIds={schemaSortByIds}
                        isExpanded={expandedCatalogIds.has(catalogId)}
                        onToggle={() => toggleCatalog(catalogId)}
                    />
                );
            })}

            {uncategorizedSchemas.length > 0 && (
                <div className="mb12">
                    <div
                        className="navigator-header pl8"
                        style={{ height: 32, display: 'flex', alignItems: 'center' }}
                    >
                        <span className="one-line-ellipsis" style={{ flex: 1 }}>
                            Uncategorized
                        </span>
                    </div>
                    {uncategorizedSchemas.map((schema) => {
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
                                    dispatch(changeTableSort(schema.id, sortKey, sortAsc))
                                }
                                onLoadMore={() =>
                                    dispatch(
                                        searchTableBySchema(schema.name, schema.id, undefined)
                                    )
                                }
                            />
                        );
                    })}
                    <div ref={setUncategorizedSentinel} />
                </div>
            )}

            <IntersectionElement ref={setIntersectElement} />
        </CatalogList>
    );
};
