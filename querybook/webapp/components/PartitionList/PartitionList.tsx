import React, { useMemo } from 'react';

import { Tag } from 'ui/Tag/Tag';

export const PartitionList: React.FunctionComponent<{
    partitionString: string;
}> = ({ partitionString }) => {
    const partitions = useMemo(() => {
        try {
            return JSON.parse(partitionString);
        } catch (e) {
            return null;
        }
    }, [partitionString]);

    if (!partitions) {
        return null;
    }

    // Tag for each partition
    return (
        <div className="flex-row flex-wrap">
            {partitions.map((partition) => (
                <Tag key={partition} mini={true}>
                    {partition}
                </Tag>
            ))}
        </div>
    );
};
