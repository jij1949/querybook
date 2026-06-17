import React from 'react';

import { CatalogType } from 'lib/utils/catalog-type';

import AwsGlueSvg from './aws-glue.svg';
import DatabricksSvg from './databricks.svg';

interface CatalogTypeIconProps {
    type: CatalogType;
    size?: number;
}

export const CatalogTypeIcon: React.FC<CatalogTypeIconProps> = ({
    type,
    size = 16,
}) => {
    if (type === 'glue') {
        return (
            <span aria-hidden="true">
                <AwsGlueSvg width={size} height={size} />
            </span>
        );
    }

    if (type === 'databricks') {
        return (
            <span aria-hidden="true">
                <DatabricksSvg width={size} height={size} />
            </span>
        );
    }

    return null;
};
