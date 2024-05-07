import React from 'react';
import { IconButton } from 'ui/Button/IconButton';
import { DataDocResource } from '../../resource/dataDoc';
import toast from 'react-hot-toast';

interface IProps {
    docId: number;
}

export const DataDocJsonDownloadButton: React.FunctionComponent<IProps> = ({
    docId,
}) => {
    const download = async () => {
        try {
            const doc = await DataDocResource.get(docId);
            const docJson = JSON.stringify(doc, null, 2);
            const jsonDocTitle = `${doc.data.id}_${doc.data.title}.json`;
            const fileResult = new File([docJson], jsonDocTitle, {
                type: 'application/json',
            });

            // Create a temporary URL to download the file
            const url = window.URL.createObjectURL(fileResult);
            const a = document.createElement('a');
            // Create an anchor tag and click it to download the file
            a.href = url;
            a.download = fileResult.name;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        } catch (e) {
            toast.error('Failed to download JSON');
        }
    };

    return (
        <IconButton
            icon="Download"
            onClick={download}
            tooltip={'Download JSON'}
            tooltipPos={'left'}
            title="JSON"
        />
    );
};
