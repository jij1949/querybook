import React, { useEffect, useMemo, useState } from 'react';

import { DataDocTemplateVarForm } from 'components/DataDocTemplateButton/DataDocTemplateVarForm';
import { IDataDoc, IDataDocMeta } from 'const/datadoc';
import { TextButton } from 'ui/Button/Button';
import { AccentText } from 'ui/StyledText/StyledText';

import { DataDocTemplateInfoButton } from './DataDocTemplateInfoButton';

import './WarningBanner.scss';
import { Icon } from 'ui/Icon/Icon';
import { hasQueryContainUnlimitedSelect } from '../../lib/sql-helper/sql-limiter';

interface IProps {
    changeDataDocMeta: (docId: number, meta: IDataDocMeta) => Promise<void>;
    dataDoc: IDataDoc;
    isEditable?: boolean;
}

function checkCellsForSelectWithoutLimit(cells) {
    for (const cell of cells) {
        if (hasQueryContainUnlimitedSelect(cells[0].context) !== undefined) {
            return true;
        }
    }
    return false;
}

export const DataDocTemplateCell: React.FunctionComponent<IProps> = ({
    changeDataDocMeta,
    dataDoc,
    isEditable,
}) => {
    const hasMeta = useMemo(
        () => dataDoc.meta.variables.length > 0,
        [dataDoc.meta]
    );
    const [showFacade, setShowFacade] = useState(!hasMeta && isEditable);
    useEffect(() => {
        setShowFacade(!hasMeta && isEditable);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [dataDoc.id]);

    if (!hasMeta && !isEditable) {
        return <div className="DataDocTemplateCell mb24" />;
    }

    let contentDOM: React.ReactNode;
    if (showFacade) {
        contentDOM = (
            <div className="flex-row ">
                <TextButton
                    icon="Plus"
                    className="mr4"
                    title="New Variable"
                    onClick={() => setShowFacade(false)}
                />
                <DataDocTemplateInfoButton style="icon" />
            </div>
        );
    } else {
        contentDOM = (
            <>
                {checkCellsForSelectWithoutLimit(dataDoc.dataDocCells) ? (
                    <div className="banner">
                        This doc contains query cells with <code>select</code>{' '}
                        but no <code>limit</code>, denoted by{' '}
                        <Icon name="AlertTriangle" />. This affects scheduled or
                        multi-cell executions.
                    </div>
                ) : null}
                <div className=" flex-row ph8">
                    <AccentText
                        className="mr12"
                        size="text"
                        weight="bold"
                        color="light"
                    >
                        Variables
                    </AccentText>
                    <DataDocTemplateInfoButton style="icon" />
                </div>
                <DataDocTemplateVarForm
                    isEditable={isEditable}
                    variables={dataDoc.meta.variables}
                    onSave={(newVariables) => {
                        if (newVariables.length === 0) {
                            setShowFacade(true);
                        }
                        return changeDataDocMeta(dataDoc.id, {
                            ...dataDoc.meta,
                            variables: newVariables,
                        });
                    }}
                />
            </>
        );
    }

    return <div className="DataDocTemplateCell mb24 ph12">{contentDOM}</div>;
};
