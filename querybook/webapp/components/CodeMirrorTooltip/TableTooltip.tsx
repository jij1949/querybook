import { ContentState } from 'draft-js';
import React from 'react';

import { DataTableTags } from 'components/DataTableTags/DataTableTags';
import { IDataColumn, IDataSchema, IDataTable } from 'const/metastore';
import { setSidebarTableId } from 'lib/querybookUI';
import { IconButton } from 'ui/Button/IconButton';
import { ShowMoreText } from 'ui/ShowMoreText/ShowMoreText';
import {Icon} from "../../ui/Icon/Icon";

interface IProps {
    table: IDataTable;
    columns: IDataColumn[];
    schema: IDataSchema;
    openTableModal?: () => any;
}

export const TableTooltip: React.FunctionComponent<IProps> = ({
    table,
    columns,
    schema,
    openTableModal,
}) => {
    const tableName =
        table && schema ? `${schema.name}.${table.name}` : table.name;
    const description = table.description
        ? (table.description as ContentState).getPlainText()
        : '';

    const location = table.location;

    const lastPartitions = table.latest_partitions ?? '[]';

    const seeDetailsButton = openTableModal && (
        <IconButton
            size={18}
            onClick={openTableModal}
            noPadding
            icon={'ExternalLink'}
            tooltip={'Details'}
            tooltipPos={'left'}
            className="ml4"
        />
    );
    const pinToSidebarButton = (
        <IconButton
            noPadding
            size={18}
            onClick={() => setSidebarTableId(table.id)}
            icon={'Sidebar'}
            tooltip={'Pin'}
            tooltipPos={'left'}
        />
    );

    const descriptionDOM = description && (
        <>
            <div className="tooltip-title">Description</div>
            <div className="tooltip-content">
                <ShowMoreText text={description} />
            </div>
        </>
    );
    const tagsDOM = <DataTableTags tableId={table.id} readonly mini />;
    const partitionDOM = lastPartitions && lastPartitions !== '[]' && (
        <>
            <div className="tooltip-title">Latest Partitions</div>
            <div className="tooltip-content">
                <ShowMoreText text={lastPartitions} />
            </div>
        </>
    );

    const partitionKeyList = table.column_info?.partition_keys ?? [];
    const isPartitionKey = (column) => partitionKeyList.some((key) => key === column.name);

    const columnsDOM = (
        <>
            <div className="tooltip-title">Column Names</div>
            <div className="tooltip-content">
                {(columns || []).map((col) => (
                    <div key={col.id}>
                        {`- ${col.name}: ${col.type}`} {isPartitionKey(col) && <Icon name={"Key"} size={12}/>}
                    </div>
                ))}
            </div>
        </>
    );

    const locationDOM = location && (
        <>
            <div className="tooltip-title">Location</div>
            <div className="tooltip-content">{location}</div>
        </>
    );

    const contentDOM = (
        <>
            <div className="table-tooltip-header flex-row">
                <div>{tableName}</div>
                <div className="flex-row mt4 ml4">
                    {pinToSidebarButton}
                    {seeDetailsButton}
                </div>
            </div>
            {descriptionDOM}
            {tagsDOM}
            {partitionDOM}
            {columnsDOM}
            {locationDOM}
        </>
    );

    return <div className="rich-text-content ">{contentDOM}</div>;
};
