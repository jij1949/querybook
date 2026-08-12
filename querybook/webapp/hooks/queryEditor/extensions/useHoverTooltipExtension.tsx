import {
    EditorView,
    hoverTooltip,
    HoverTooltipSource,
} from '@uiw/react-codemirror';
import React, { MutableRefObject, useCallback, useMemo } from 'react';
import ReactDOM from 'react-dom';
import { Provider, useSelector } from 'react-redux';

import { FunctionDocumentationTooltipByName } from 'components/CodeMirrorTooltip/FunctionDocumentationTooltip';
import { TableColumnTooltip } from 'components/CodeMirrorTooltip/TableColumnTooltip';
import { TableTooltipByName } from 'components/CodeMirrorTooltip/TableTooltip';
import { getTokenAtOffset, offsetToPos } from 'lib/codemirror/utils';
import { SqlParser } from 'lib/sql-helper/sql-parser';
import { getTableTokenDisplayName } from 'lib/utils/table-identifier';
import { reduxStore } from 'redux/store';
import { IStoreState } from 'redux/store/types';

export const useHoverTooltipExtension = ({
    sqlParserRef,
    metastoreId,
    language,
    hidePin,
}: {
    sqlParserRef: MutableRefObject<SqlParser>;
    metastoreId: number;
    language: string;
    hidePin?: boolean;
}) => {
    // Get metastore to check catalog display settings
    const metastore = useSelector((state: IStoreState) =>
        metastoreId ? state.dataSources.queryMetastoreById[metastoreId] : null
    );
    const showCatalog =
        metastore?.catalog_display_config?.show_catalog_in_ui ?? false;

    const getTableAtCursor = useCallback(
        (editorView: EditorView) => {
            const selection = editorView.state.selection.main;
            const v5Pos = offsetToPos(editorView.state, selection.from);
            return sqlParserRef.current.getTableAtPos(v5Pos);
        },
        [sqlParserRef.current]
    );

    const getHoverTooltips: HoverTooltipSource = useCallback(
        (view: EditorView, pos: number, side: -1 | 1) => {
            const v5Pos = offsetToPos(view.state, pos);

            const token = getTokenAtOffset(view.state, pos);
            if (!token) {
                return null;
            }

            const nextChar = view.state.doc.sliceString(token.to, token.to + 1);

            let table = null;
            let column = null;
            const context = sqlParserRef.current.getContextAtPos(v5Pos);

            let tooltipComponent = null;
            if (nextChar === '(') {
                tooltipComponent = (
                    <FunctionDocumentationTooltipByName
                        language={language}
                        functionName={token.text}
                    />
                );
            } else if (context === 'table') {
                table = sqlParserRef.current.getTableAtPos(v5Pos);
                if (table) {
                    // Always include the catalog (when present) in the lookup
                    // name so the tooltip can resolve catalog-qualified
                    // references — including the mid-migration fallback to the
                    // legacy prefixed name. Display formatting inside the
                    // tooltip still respects the metastore's catalog settings.
                    const tableFullName = getTableTokenDisplayName(
                        table,
                        showCatalog || Boolean(table.catalog)
                    );
                    tooltipComponent = (
                        <TableTooltipByName
                            metastoreId={metastoreId}
                            tableFullName={tableFullName}
                            hidePinItButton={hidePin ?? false}
                        />
                    );
                }
            } else if (context === 'column') {
                column = sqlParserRef.current.getColumnAtPos(v5Pos, token.text);
                if (column) {
                    tooltipComponent = <TableColumnTooltip column={column} />;
                }
            }

            if (!tooltipComponent) {
                return null;
            }

            return {
                pos: token.from,
                end: token.to,
                create: (view: EditorView) => {
                    const container = document.createElement('div');
                    ReactDOM.render(
                        <Provider store={reduxStore}>
                            {tooltipComponent}
                        </Provider>,
                        container
                    );

                    return { dom: container };
                },
            };
        },
        [sqlParserRef, language, metastoreId]
    );

    const extension = useMemo(
        () => hoverTooltip(getHoverTooltips, {}),
        [getHoverTooltips]
    );
    return { extension, getTableAtCursor };
};
