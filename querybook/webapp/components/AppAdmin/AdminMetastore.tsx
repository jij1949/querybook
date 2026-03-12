import { clone } from 'lodash';
import moment from 'moment';
import React from 'react';
import { useParams } from 'react-router-dom';

import { AdminAuditLogButton } from 'components/AdminAuditLog/AdminAuditLogButton';
import { TaskEditor } from 'components/Task/TaskEditor';
import { IAdminACLControl, IAdminMetastore } from 'const/admin';
import { useResource } from 'hooks/useResource';
import history from 'lib/router-history';
import { generateFormattedDate } from 'lib/utils/datetime';
import { AdminMetastoreResource } from 'resource/admin/metastore';
import { TextButton } from 'ui/Button/Button';
import { InfoButton } from 'ui/Button/InfoButton';
import { Card } from 'ui/Card/Card';
import { DebouncedInput } from 'ui/DebouncedInput/DebouncedInput';
import { FormField } from 'ui/Form/FormField';
import { SimpleField } from 'ui/FormikField/SimpleField';
import { GenericCRUD } from 'ui/GenericCRUD/GenericCRUD';
import { Icon } from 'ui/Icon/Icon';
import { Level } from 'ui/Level/Level';
import { Loading } from 'ui/Loading/Loading';
import { Markdown } from 'ui/Markdown/Markdown';
import {
    getDefaultFormValue,
    SmartForm,
    updateValue,
    validateForm,
} from 'ui/SmartForm/SmartForm';
import { Tabs } from 'ui/Tabs/Tabs';
import { ToggleSwitch } from 'ui/ToggleSwitch/ToggleSwitch';

import { AdminDeletedList } from './AdminDeletedList';

import './AdminMetastore.scss';

interface IProps {
    metastores: IAdminMetastore[];
    loadMetastores: () => Promise<any>;
}

export const AdminMetastore: React.FunctionComponent<IProps> = ({
    metastores,
    loadMetastores,
}) => {
    const { id: metastoreId } = useParams();

    const [showTaskEditor, setShowTaskEditor] = React.useState<boolean>(false);

    const { data: metastoreLoaders } = useResource(
        AdminMetastoreResource.getAllLoaders
    );

    const {
        data: metastoreUpdateSchedule,
        forceFetch: loadMetastoreUpdateSchedule,
    } = useResource(
        React.useCallback(
            () => AdminMetastoreResource.getUpdateSchedule(metastoreId),
            [metastoreId]
        )
    );

    React.useEffect(() => {
        if (metastoreUpdateSchedule?.id) {
            setShowTaskEditor(true);
        }
    }, [metastoreUpdateSchedule]);

    const createMetastore = React.useCallback(
        async (metastore: IAdminMetastore) => {
            const { data } = await AdminMetastoreResource.create(
                metastore.name,
                metastore.metastore_params,
                metastore.loader,
                metastore.acl_control,
                metastore.catalog_display_config
            );

            await loadMetastores();
            history.push(`/admin/metastore/${data.id}/`);

            return data;
        },
        []
    );

    const saveMetastore = React.useCallback(
        async (metastore: Partial<IAdminMetastore>) => {
            const { data } = await AdminMetastoreResource.update(
                metastoreId,
                metastore
            );

            return data as IAdminMetastore;
        },
        [metastoreId]
    );

    const deleteMetastore = React.useCallback(
        (metastore: IAdminMetastore) =>
            AdminMetastoreResource.delete(metastore.id),
        []
    );

    const recoverMetastore = React.useCallback(async (mId: number) => {
        const { data } = await AdminMetastoreResource.recover(mId);

        await loadMetastores();
        history.push(`/admin/metastore/${mId}/`);

        return data;
    }, []);

    const itemValidator = React.useCallback(
        (metastore: IAdminMetastore) => {
            const errors: Partial<Record<keyof IAdminMetastore, string>> = {};

            if ((metastore.name || '').length === 0) {
                errors.name = 'Name cannot be empty';
            } else if ((metastore.name || '').length > 255) {
                errors.name = 'Name is too long';
            }

            const loader = (metastoreLoaders || []).find(
                (l) => l.name === metastore.loader
            );
            if (!loader) {
                errors.loader = 'Invalid loader';
            }
            const formValid = validateForm(
                metastore.metastore_params,
                loader.template
            );
            if (!formValid[0]) {
                errors.metastore_params = `Error found in loader params ${formValid[2]}: ${formValid[1]}`;
            }

            if (metastore.acl_control.type) {
                for (const [
                    index,
                    table,
                ] of metastore.acl_control.tables.entries()) {
                    if (!table) {
                        errors.acl_control = `Table at index ${index} is empty`;
                        break;
                    }
                }
            }
            return errors;
        },
        [metastoreLoaders]
    );

    const getMetastoreACLControlDOM = (
        aclControl: IAdminACLControl,
        onChange: (fieldName: string, fieldValue: any) => void
    ) => {
        if (aclControl.type == null) {
            return (
                <div className="AdminMetastore-acl-button">
                    <TextButton
                        onClick={() =>
                            onChange('acl_control', {
                                type: 'denylist',
                                tables: [],
                            })
                        }
                        title="Create Allowlist/Denylist"
                    />
                </div>
            );
        }

        const helpContent = `
### ACL Pattern Syntax

**Catalog-level wildcards (all schemas/tables in catalog):**
- \`catalog.*.*\` - Explicit form (recommended)
- \`catalog.*\` - Shorthand form

**Schema-level wildcards:**
- \`schema.*\` - All tables in schema (2-level)
- \`catalog.schema.*\` - All tables in schema (3-level)

**Exact table matches:**
- \`table_name\` - Single table in default schema
- \`schema.table_name\` - Specific table (2-level)
- \`catalog.schema.table_name\` - Specific table (3-level)

**Prefix wildcards:**
- \`schema.prefix_*\` - Tables starting with prefix (2-level)
- \`catalog.schema.prefix_*\` - Tables starting with prefix (3-level)

**Examples:**
- \`production.*.*\` - All production catalog data
- \`staging.analytics.*\` - All tables in staging.analytics
- \`dev.test.temp_*\` - All temp tables in dev.test

**Note:** Patterns are case-sensitive and matched at sync time.
`.trim();

        const tablesDOM = (
            <div>
                <div className="flex-row" style={{ alignItems: 'center', marginBottom: '8px' }}>
                    <span style={{ marginRight: '8px' }}>
                        {aclControl.type === 'denylist' ? 'Tables to Denylist' : 'Tables to Allowlist'}
                    </span>
                    <InfoButton layout={['right']}>
                        <Markdown>{helpContent}</Markdown>
                    </InfoButton>
                </div>
                <SmartForm
                    formField={{
                        field_type: 'list',
                        of: {
                            description:
                                aclControl.type === 'denylist'
                                    ? 'Table to Denylist'
                                    : 'Table to Allowlist',
                            field_type: 'string',
                            helper: '',
                            hidden: false,
                            required: true,
                        },
                        max: null,
                        min: 1,
                    }}
                    value={aclControl.tables}
                    onChange={(path, value) =>
                        onChange(
                            `acl_control.tables`,
                            updateValue(aclControl.tables, path, value)
                        )
                    }
                />
            </div>
        );
        return (
            <>
                <div className="AdminMetastore-acl-warning flex-row">
                    <Icon name="AlertOctagon" />
                    {aclControl.type === 'denylist'
                        ? 'All tables will be allowed unless specified.'
                        : 'All tables will be denied unless specified.'}
                </div>
                <div className="AdminMetastore-acl-top horizontal-space-between">
                    <Tabs
                        selectedTabKey={aclControl.type}
                        items={[
                            { name: 'Denylist', key: 'denylist' },
                            { name: 'Allowlist', key: 'allowlist' },
                        ]}
                        onSelect={(key) => {
                            onChange('acl_control', { type: key, tables: [] });
                        }}
                    />
                    <TextButton
                        title={
                            aclControl.type === 'denylist'
                                ? 'Remove Denylist'
                                : 'Remove Allowlist'
                        }
                        onClick={() => onChange('acl_control', {})}
                    />
                </div>
                {tablesDOM}
            </>
        );
    };

    const getMetastoreCatalogDisplaySettingsDOM = (
        catalogDisplayConfig: {
            enable_catalog_support: boolean;
            show_catalog_in_ui: boolean;
            catalog_display_name?: string
        },
        onChange: (fieldName: string, fieldValue: any) => void
    ) => {
        // Ensure we have a valid config object
        const config = catalogDisplayConfig || {
            enable_catalog_support: false,
            show_catalog_in_ui: false
        };

        const handleEnableCatalogChange = (checked: boolean) => {
            const newConfig = {
                ...config,
                enable_catalog_support: checked,
            };
            onChange('catalog_display_config', newConfig);
        };

        const handleShowCatalogChange = (checked: boolean) => {
            const newConfig = {
                ...config,
                show_catalog_in_ui: checked,
            };
            onChange('catalog_display_config', newConfig);
        };

        const handleDisplayNameChange = (value: string) => {
            const newConfig = {
                ...config,
                catalog_display_name: value,
            };
            onChange('catalog_display_config', newConfig);
        };

        return (
            <>
                <FormField
                    stacked
                    label="Enable Catalog Support"
                    help="When enabled, catalogs will be synced from the metastore. When disabled, no catalogs are created (schemas only)."
                >
                    <ToggleSwitch
                        checked={config?.enable_catalog_support ?? false}
                        onChange={handleEnableCatalogChange}
                    />
                </FormField>
                <FormField
                    stacked
                    label="Show Catalog in UI"
                    help="When enabled, catalog names will be shown in table displays throughout the UI (e.g., catalog.schema.table)"
                >
                    <ToggleSwitch
                        checked={config?.show_catalog_in_ui ?? false}
                        onChange={handleShowCatalogChange}
                    />
                </FormField>
                <FormField
                    stacked
                    label="Default Catalog Name"
                    help="Used only when 'Enable Catalog Support' is on and the loader doesn't provide a catalog name. Leave empty to use 'default'."
                >
                    <DebouncedInput
                        value={config?.catalog_display_name ?? ''}
                        onChange={handleDisplayNameChange}
                        inputProps={{
                            className: 'input',
                            placeholder: "default"
                        }}
                    />
                </FormField>
            </>
        );
    };

    const renderMetastoreItem = (
        item: IAdminMetastore,
        onChange: (fieldName: string, fieldValue: any) => void
    ) => {
        const loader = (metastoreLoaders || []).find(
            (l) => l.name === item.loader
        );

        const updateLoader = (loaderName: string) => {
            const newLoader = (metastoreLoaders || []).find(
                (l) => l.name === loaderName
            );
            if (newLoader) {
                onChange(
                    'metastore_params',
                    getDefaultFormValue(newLoader.template)
                );
                onChange('loader', newLoader.name);
            }
        };

        const logDOM = item.id != null && (
            <div className="right-align">
                <AdminAuditLogButton
                    itemType="query_metastore"
                    itemId={item.id}
                />
            </div>
        );

        return (
            <>
                <div className="AdminForm-top">
                    {logDOM}
                    <SimpleField stacked name="name" type="input" />
                </div>
                <div className="AdminForm-main">
                    <div className="AdminForm-left">
                        <SimpleField
                            stacked
                            name="loader"
                            type="react-select"
                            options={Object.values(metastoreLoaders).map(
                                (l) => ({
                                    value: l.name,
                                    label: l.name,
                                })
                            )}
                            onChange={updateLoader}
                        />

                        {loader && (
                            <div className="AdminForm-section">
                                <div className="AdminForm-section-top flex-row">
                                    <div className="AdminForm-section-title">
                                        Loader Params
                                    </div>
                                </div>
                                <div className="AdminForm-section-content">
                                    <SmartForm
                                        formField={loader.template}
                                        value={item.metastore_params}
                                        onChange={(path, value) =>
                                            onChange(
                                                'metastore_params',
                                                updateValue(
                                                    item.metastore_params,
                                                    path,
                                                    value
                                                )
                                            )
                                        }
                                    />
                                </div>
                            </div>
                        )}
                        <div className="AdminForm-section">
                            <div className="AdminForm-section-top flex-row horizontal-space-between">
                                <div className="AdminForm-section-title">
                                    Catalog Settings
                                </div>
                                <InfoButton layout={['bottom', 'right']}>
                                    <Markdown>{`Control how catalog support works in this metastore.

**Enable Catalog Support**: Controls whether catalogs are synced from the metastore at all.
- When ON: If the metastore provides catalogs (Databricks, Glue), they are synced. If not (SQLAlchemy, Hive), a default catalog is created.
- When OFF: No catalogs are created, only schemas (backward compatible mode).

**Show Catalog in UI**: Controls display of catalogs in the UI.
- When ON: Table names shown as \`catalog.schema.table\`
- When OFF: Table names shown as \`schema.table\`

**Default Catalog Name**: Used only when "Enable Catalog Support" is ON and the loader doesn't provide catalog names (e.g., SQLAlchemy, Hive). Defaults to "default" if empty.

For Databricks and Glue, this field is ignored as they provide their own catalog names.`}</Markdown>
                                </InfoButton>
                            </div>
                            <div className="AdminForm-section-content">
                                {getMetastoreCatalogDisplaySettingsDOM(
                                    item.catalog_display_config,
                                    onChange
                                )}
                            </div>
                        </div>

                        <div className="AdminForm-section">
                            <div className="AdminForm-section-top flex-row horizontal-space-between">
                                <div className="AdminForm-section-title">
                                    ACL Control
                                </div>
                                <InfoButton layout={['bottom', 'right']}>
                                    <Markdown>{`Access Control Lists (ACL)
are used to limit access to tables in the metastore. If no ACL rules are specified,
all schemas/tables are allowed.  Either an allowlist or a denylist can be configured.

Each value in the list should be in one of the following formats:

- \`schema.*\`: Allow or deny all tables in a schema
- \`schema.table*\`: Allow or deny all tables in a schema matching a prefix
- \`schema.table\`: Allow or deny a specific table
- \`catalog.schema.*\`: Allow or deny all tables in a catalog schema
- \`catalog.schema.table\`: Allow or deny a specific table with catalog
- \`catalog.*\`: Allow or deny all schemas and tables in a catalog

This feature affects both the metastore sync and the query engine.`}</Markdown>
                                </InfoButton>
                            </div>
                            <div className="AdminForm-section-content">
                                {getMetastoreACLControlDOM(
                                    item.acl_control,
                                    onChange
                                )}
                            </div>
                        </div>
                        {metastoreId !== 'new' && (
                            <div className="AdminForm-section">
                                <div className="AdminForm-section-top flex-row">
                                    <div className="AdminForm-section-title">
                                        Update Schedule
                                    </div>
                                </div>
                                <div className="AdminForm-section-content">
                                    {showTaskEditor ? (
                                        <div className="AdminMetastore-TaskEditor">
                                            <TaskEditor
                                                task={
                                                    metastoreUpdateSchedule ?? {
                                                        cron: '0 0 * * *',
                                                        name: `update_metastore_${metastoreId}`,
                                                        task: 'tasks.update_metastore.update_metastore',
                                                        task_type: 'prod',
                                                        enabled: true,
                                                        args: [
                                                            Number(metastoreId),
                                                        ],
                                                    }
                                                }
                                                onTaskCreate={
                                                    loadMetastoreUpdateSchedule
                                                }
                                            />
                                        </div>
                                    ) : (
                                        <div className="AdminMetastore-TaskEditor-button center-align">
                                            <TextButton
                                                title="Create Schedule"
                                                onClick={() =>
                                                    setShowTaskEditor(true)
                                                }
                                            />
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </>
        );
    };

    if (metastoreId === 'new') {
        if (metastoreLoaders) {
            const defaultLoader = metastoreLoaders[0];

            const newMetastore: IAdminMetastore = {
                id: null,
                created_at: moment().unix(),
                updated_at: moment().unix(),
                deleted_at: null,
                name: '',
                loader: defaultLoader.name,
                // Only StructForm form for template
                metastore_params: getDefaultFormValue(
                    defaultLoader.template
                ) as Record<string, unknown>,
                acl_control: {},
                catalog_display_config: {
                    enable_catalog_support: false,
                    show_catalog_in_ui: false,
                    catalog_display_name: '',
                },
            };
            return (
                <div className="AdminMetastore">
                    <div className="AdminForm">
                        <GenericCRUD
                            item={newMetastore}
                            createItem={createMetastore}
                            renderItem={renderMetastoreItem}
                            validate={itemValidator}
                        />
                    </div>
                </div>
            );
        } else {
            return <Loading />;
        }
    }

    const metastoreItem = metastores?.find(
        (metastore) => Number(metastoreId) === metastore.id
    );

    if (
        metastoreId === 'deleted' ||
        (metastoreItem && metastoreItem.deleted_at !== null)
    ) {
        const deletedMetastores = metastoreItem?.deleted_at
            ? [metastoreItem]
            : metastores?.filter((ms) => ms.deleted_at);
        return (
            <div className="AdminMetastore">
                <div className="AdminLanding-top">
                    <div className="AdminLanding-desc">
                        Deleted metastores can be recovered.
                    </div>
                </div>
                <div className="AdminLanding-content">
                    <AdminDeletedList
                        items={deletedMetastores}
                        onRecover={recoverMetastore}
                        keysToShow={[
                            'created_at',
                            'deleted_at',
                            'loader',
                            'metastore_params',
                        ]}
                    />
                </div>
            </div>
        );
    }

    if (metastoreItem) {
        if (metastoreLoaders) {
            return (
                <div className="AdminMetastore">
                    <div className="AdminForm">
                        <GenericCRUD
                            item={metastoreItem}
                            deleteItem={deleteMetastore}
                            onDelete={() => history.push('/admin/metastore/')}
                            updateItem={saveMetastore}
                            validate={itemValidator}
                            renderItem={renderMetastoreItem}
                            onItemCUD={loadMetastores}
                        />
                    </div>
                </div>
            );
        } else {
            return <Loading />;
        }
    } else {
        const getCardDOM = () =>
            clone(metastores)
                .filter((ms) => ms.deleted_at == null)
                .sort((m1, m2) => m2.updated_at - m1.updated_at)
                .slice(0, 5)
                .map((m) => (
                    <Card
                        key={m.id}
                        title={m.name}
                        onClick={() =>
                            history.push(`/admin/metastore/${m.id}/`)
                        }
                        height="160px"
                        width="240px"
                    >
                        {' '}
                        <div className="AdminLanding-card-content">
                            <div className="AdminLanding-card-content-top">
                                Last Updated
                            </div>
                            <div className="AdminLanding-card-content-date">
                                {generateFormattedDate(m.updated_at)}
                            </div>
                        </div>
                    </Card>
                ));
        return (
            <div className="AdminMetastore">
                <div className="AdminLanding">
                    <div className="AdminLanding-top">
                        <Level>
                            <div className="AdminLanding-title">Metastore</div>
                            <AdminAuditLogButton itemType="query_metastore" />
                        </Level>
                        <div className="AdminLanding-desc">
                            Metastores hold metadata for the tables, such as
                            schemas and deny/allowlists.
                        </div>
                    </div>
                    <div className="AdminLanding-content">
                        <div className="AdminLanding-cards flex-row">
                            {metastores && getCardDOM()}
                            <Card
                                title="+"
                                onClick={() =>
                                    history.push('/admin/metastore/new/')
                                }
                                height="160px"
                                width="240px"
                            >
                                create a new metastore
                            </Card>
                        </div>
                    </div>
                </div>
            </div>
        );
    }
};
