import React, { useMemo } from 'react';
import { Modal } from '../../ui/Modal/Modal';
import {
    FileUploaderArea,
    UploadType,
} from '../TableUploader/FileUploaderArea';
import { Formik, useFormikContext } from 'formik';
import { AccentText } from '../../ui/StyledText/StyledText';
import { AsyncButton } from '../../ui/AsyncButton/AsyncButton';
import { DataDocResource } from '../../resource/dataDoc';
import toast from 'react-hot-toast';
import { normalizeRawDataDoc } from '../../redux/dataDoc/action';
import { navigateWithinEnv } from '../../lib/utils/query-string';
import { useSelector } from 'react-redux';
import { IStoreState } from 'redux/store/types';

interface IUploadDataDocWindowProps {
    onHide: () => void;
}

export interface IDataDocUploadFormikForm {
    file: File | null;
}

export const UploadDataDocWindow: React.FC<IUploadDataDocWindowProps> = ({
    onHide,
}) => (
    <>
        <Formik
            initialValues={useMemo(() => ({ file: null }), [])}
            onSubmit={null}
        >
            <DataDocUploaderFormModal onHide={onHide} />
        </Formik>
    </>
);

const DataDocUploaderFormModal: React.FC<{
    onHide: () => void;
}> = ({ onHide }) => {
    const { values, setFieldValue } =
        useFormikContext<IDataDocUploadFormikForm>();

    const currentEnvId = useSelector(
        (state: IStoreState) => state.environment.currentEnvironmentId
    );

    const modalTitleDOM = (
        <AccentText size={'large'} weight={'bold'}>
            Upload a JSON File
        </AccentText>
    );

    const handleSubmit = async () => {
        try {
            const fileReader = new FileReader();
            fileReader.onload = async () => {
                try {
                    // Read contents of uploaded file
                    const fileContent = fileReader.result as string;
                    const jsonData = JSON.parse(fileContent).data;

                    // Create DataDoc
                    const createDataDocPromise = DataDocResource.create(
                        jsonData.cells,
                        currentEnvId,
                        jsonData.meta,
                        jsonData.title,
                        jsonData.public
                    );

                    const { data: rawDataDoc } = await toast.promise(
                        createDataDocPromise,
                        {
                            loading: 'Creating DataDoc...',
                            success: 'DataDoc created!',
                            error: 'Fail to create DataDoc',
                        },
                        {
                            success: {
                                duration: 10000,
                            },
                            error: {
                                duration: 10000,
                            },
                        }
                    );
                    const { dataDoc } = normalizeRawDataDoc(rawDataDoc);

                    // Redirect to the newly created DataDoc
                    if (dataDoc.id) {
                        navigateWithinEnv(`/datadoc/${dataDoc.id}`);
                    }
                } catch (e) {
                    toast.error('Invalid JSON file');
                    return;
                }
            };
            fileReader.readAsText(values.file);
        } catch (e) {
            toast.error('Failed to upload DataDoc');
        }
    };

    const submitButtonDOM = (
        <div style={{ float: 'right', marginBottom: '1rem' }}>
            <AsyncButton
                color="confirm"
                icon="Check"
                title="Confirm Upload"
                onClick={handleSubmit}
                disabled={!values.file}
            />
        </div>
    );

    return (
        <Modal
            onHide={onHide}
            topDOM={modalTitleDOM}
            bottomDOM={submitButtonDOM}
        >
            <div className="center-align mv12">
                <FileUploaderArea
                    onUpload={(f) => setFieldValue('file', f)}
                    file={values.file}
                    uploadType={UploadType.DataDoc}
                />
            </div>
        </Modal>
    );
};
