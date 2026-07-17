import inspect
import math
import traceback
from abc import ABCMeta, abstractclassmethod, abstractmethod
from typing import Dict, List, Optional, Tuple, overload

import gevent
from app.db import DBSession, with_session
from const.data_element import DataElementTuple, DataElementAssociationTuple
from const.metastore import (
    DataCatalog,
    DataColumn,
    DataOwnerType,
    DataSchema,
    DataTable,
    MetadataType,
    MetastoreLoaderConfig,
)
from lib.form import AllFormField
from lib.logger import get_logger
from lib.utils import json
from lib.utils.utils import with_exception
from logic.data_element import create_column_data_element_association
from logic.elasticsearch import delete_es_table_by_id, update_table_by_id
from logic.metastore import (
    count_data_schema,
    create_catalog,
    create_column,
    create_schema,
    create_table,
    create_table_information,
    create_table_ownerships,
    create_table_warnings,
    delete_catalog,
    delete_column,
    delete_schema,
    delete_table,
    get_all_catalogs,
    get_catalog_by_id,
    get_catalog_by_name,
    get_column_by_table_id,
    get_schema_by_name,
    get_table_by_schema_id,
    get_table_by_schema_id_and_name,
    iterate_data_schema,
    parse_schema_identifier,
)
from logic.tag import create_column_tags, create_table_tags

from .utils import MetastoreTableACLChecker

LOG = get_logger(__name__)


class BaseMetastoreLoader(metaclass=ABCMeta):
    loader_config: MetastoreLoaderConfig = MetastoreLoaderConfig({})

    # Whether syncing this loader connects to a service that requires a
    # projected OIDC token (only available on K8s workers). Drives Celery
    # queue routing to k8s-only. Override in loaders that need it.
    REQUIRES_OIDC_WORKER = False

    def _method_accepts_param(self, method_name: str, param_name: str) -> bool:
        """Check if a method accepts a specific parameter using runtime introspection.

        This method uses Python's inspect module to examine method signatures at runtime.
        Results could be cached for performance, but we start without caching to measure
        the raw overhead.

        Args:
            method_name: Name of the method to check
            param_name: Name of the parameter to look for

        Returns:
            True if the method accepts the parameter (explicitly or via **kwargs)
            False otherwise
        """
        try:
            method = getattr(self, method_name)
            sig = inspect.signature(method)
            return param_name in sig.parameters
        except (AttributeError, ValueError):
            # If inspection fails (method doesn't exist or signature unavailable),
            # assume parameter is not supported
            return False

    def __init__(self, metastore_dict: Dict):
        self.metastore_id = metastore_dict["id"]
        self.acl_checker = MetastoreTableACLChecker(metastore_dict["acl_control"])
        self.catalog_display_config = metastore_dict.get("catalog_display_config", {})
        self.enable_catalog_support = self.catalog_display_config.get(
            "enable_catalog_support", False
        )

    def get_catalog_display_name(self, catalog_name: str = None) -> str:
        """Get the display name for a catalog in this metastore.

        Args:
            catalog_name: The actual catalog name from the metastore.
                         If None, returns the configured display name or None.

        Returns:
            The display name if configured, otherwise returns the catalog_name as-is.
        """
        if not self.catalog_display_config:
            return catalog_name

        configured_display_name = self.catalog_display_config.get(
            "catalog_display_name"
        )
        if configured_display_name:
            return configured_display_name

        return catalog_name

    def _apply_catalog_settings(self, schema: DataSchema) -> DataSchema:
        """
        Apply catalog support settings to a schema.

        Logic:
        - If enable_catalog_support is False: return schema with catalog=None
        - If enable_catalog_support is True and schema has no catalog: create default catalog
        - If enable_catalog_support is True and schema has catalog: return as-is

        Args:
            schema: DataSchema from loader

        Returns:
            DataSchema with catalog settings applied
        """
        if not self.enable_catalog_support:
            # Catalog support disabled - strip any catalog information
            return DataSchema(name=schema.name, catalog=None)

        # Catalog support enabled
        if schema.catalog:
            # Loader provided a catalog, use it
            return schema

        # Loader didn't provide a catalog, create default
        default_catalog_name = self.catalog_display_config.get(
            "catalog_display_name", "default"
        )
        default_catalog = DataCatalog(
            name=default_catalog_name, description="Default catalog"
        )
        return DataSchema(name=schema.name, catalog=default_catalog)

    @classmethod
    def get_sandbox_catalog_names(cls, metastore_dict: Dict) -> List[str]:
        """Return sandbox catalog names from metastore params.

        Override in subclasses that need custom aggregation (e.g. ComboLoader).
        """
        params = metastore_dict.get("metastore_params") or {}
        val = params.get("sandbox_catalog_names", "")
        if not val:
            return []
        if isinstance(val, list):
            return val
        return [s.strip() for s in val.split(",") if s.strip()]

    @classmethod
    def get_table_metastore_link(
        cls, metadata_type: MetadataType, schema_name: str, table_name: str
    ) -> str:
        """Return the external metastore link of the table metadata if it has an accessible page for the given type.

        Args:
            metadata_type (MetadataType): metadata type
            schema_name (str): table schema name
            table_name (str): table name

        Returns:
            str: external metastore link of the table metadata.
        """
        return None

    @classmethod
    def get_data_element_metastore_link(cls, name: str) -> str:
        """Return the external metastore link of the data elementif it has an accessible page.

        Args:
            name (str): data element name

        Returns:
            str: external metastore link of the data element.
        """
        return None

    @classmethod
    def get_table_owner_types(cls) -> list[DataOwnerType]:
        """Return all the owner types the meatstore supports.

        Override this method if loading table owners from metastore is enabled
        and your metastore supports owner types.

        E.g.
        [
            DataOwnerType(
                name="CREATOR",
                display_name="Table Creator",
                description="Person who created the table",
            ),
            DataOwnerType(
                name="BUSINESS_OWNER",
                display_name="Owners",
                description="Person or group who is responsible for business related aspects of the table",
            ),
        ]


        The `display_name` will be rendered as the field label in the detailed table view, which is `Owners` by default.
        """
        return [
            DataOwnerType(
                name=None, display_name="Owners", description="People who own the table"
            )
        ]

    def _ensure_catalog_exists(self, catalog_tuple: DataCatalog, session=None):
        """
        Ensure catalog exists in database, create if not found.

        Args:
            catalog_tuple: DataCatalog NamedTuple with catalog metadata (minimally just name)
            session: Database session

        Returns:
            DataCatalog ORM object
        """
        if not catalog_tuple:
            LOG.warning("No catalog information provided to ensure_catalog_exists")
            return None

        catalog_name = catalog_tuple.name
        db_catalog = get_catalog_by_name(
            catalog_name, self.metastore_id, session=session
        )

        if db_catalog:
            LOG.info(
                f"Found existing catalog: id={db_catalog.id}, name={db_catalog.name}"
            )
            # Merge any new properties the loader stamped (e.g. catalog_type).
            # Only updates when properties are explicitly provided — safe for loaders
            # that don't set them.
            if catalog_tuple.properties:
                db_catalog.properties = {
                    **(db_catalog.properties or {}),
                    **catalog_tuple.properties,
                }
        else:
            LOG.info(
                f"Catalog '{catalog_name}' not found in database, creating new one"
            )

            # Try to get more detailed catalog info if the loader supports it
            detailed_catalog = catalog_tuple
            if hasattr(self, "get_catalog_info"):
                try:
                    fetched_catalog = self.get_catalog_info(catalog_name)
                    if fetched_catalog:
                        detailed_catalog = fetched_catalog
                except Exception as e:
                    LOG.error(
                        f"Could not get detailed catalog info for '{catalog_name}': {e}"
                    )

            db_catalog = create_catalog(
                name=detailed_catalog.name,
                description=(
                    detailed_catalog.description
                    if detailed_catalog.description
                    else None
                ),
                metastore_id=self.metastore_id,
                owner=detailed_catalog.owner if detailed_catalog.owner else None,
                properties=(
                    detailed_catalog.properties if detailed_catalog.properties else None
                ),
                commit=False,
                session=session,
            )
            # Flush to ensure the catalog gets an ID and is available in this transaction
            session.flush()
        return db_catalog

    @with_session
    def sync_table(
        self, schema_name: str, table_name: str, session=None
    ) -> Optional[int]:
        """Given a full qualified table name, sync the table with metastore.
          - If table is not in the allow list or in the deny list,
            or it doesn't exsit in neither metastore nor database,
            do nothing, return None
          - If table exists in metastore, sync the table from metastore
            to database, return table id
          - If table doesn't exsit in metastore, but exists in database,
            delete it from database, return -1

        Arguments:
            schema_name {str} -- the schema name
            table_name {str} -- the table name

        Returns:
            Optional[int] -- None | table id | -1
        """
        try:
            LOG.info("Syncing table %s.%s" % (schema_name, table_name))

            # Parse schema identifier to extract catalog and schema first
            catalog_tuple, parsed_schema_name, db_schema = parse_schema_identifier(
                schema_name, self.metastore_id, session=session
            )

            # Build qualified schema name for ACL checking
            qualified_schema_name = (
                f"{catalog_tuple.name}.{parsed_schema_name}"
                if catalog_tuple
                else parsed_schema_name
            )

            # return None if the table is not in the allow list or in the deny list
            if not self.acl_checker.is_table_valid(qualified_schema_name, table_name):
                return None

            # get table from metastore
            if self._method_accepts_param("get_table_and_columns", "catalog_name"):
                table, columns = self.get_table_and_columns(
                    parsed_schema_name,
                    table_name,
                    catalog_name=catalog_tuple.name if catalog_tuple else None,
                )
            else:
                # Fallback for loaders without catalog_name parameter
                table, columns = self.get_table_and_columns(
                    parsed_schema_name,
                    table_name,
                )

            # Handle catalog if present
            catalog_id = None
            if catalog_tuple:
                db_catalog = self._ensure_catalog_exists(catalog_tuple, session=session)
                catalog_id = db_catalog.id if db_catalog else None

            # get table from querybook database
            db_table = None
            if db_schema:
                db_table = get_table_by_schema_id_and_name(
                    db_schema.id, table_name, session=session
                )

            # table doesn't exsit in neither metastore nor database
            if not table and not db_table:
                return None

            # table doesn't exist in metastore, delete the table in database
            if not table:
                LOG.error(
                    f"Table {schema_name}.{table_name} ({db_table.id}) doesn't exist in metastore, deleting it from database"
                )
                delete_table(table_id=db_table.id, session=session)
                return -1

            # table exists in metastore, sync it
            schema_is_newly_created = False
            if db_schema is None:
                # Create the schema first if doesn't exist in database
                schema_is_newly_created = True
                db_schema = create_schema(
                    name=parsed_schema_name,
                    catalog_id=catalog_id,
                    table_count=1,
                    metastore_id=self.metastore_id,
                    commit=False,
                    session=session,
                )

            table_id = self._create_table_table(
                db_schema.id,
                parsed_schema_name,
                table_name,
                table,
                columns,
                session=session,
                catalog_name=catalog_tuple.name if catalog_tuple else None,
            )
            # Remove creation of new schema if we failed to create table
            if table_id is None and schema_is_newly_created:
                session.expunge(db_schema)

            return table_id

        except Exception:
            LOG.error(traceback.format_exc())
            return None

    @with_session
    def sync_create_or_update_table(
        self, schema_name: str, table_name: str, session=None
    ) -> int:
        """DEPRECATED!!! PLEASE USE `sync_table` INSTEAD.
        Given a full qualified table name,
        sync the data in metastore with database.
        Note: if table does not exist, this doesn't create a new table. But
        it does create an empty schema.

        Arguments:
            schema_name {str} -- the schema name
            table_name {str} -- the table name

        Returns:
            int -- the table id
        """
        schema_is_newly_created = False
        data_schema = get_schema_by_name(
            schema_name, self.metastore_id, session=session
        )

        if data_schema is None:
            # If no schema, create it
            # However, if the table turns out to not exist
            # then we will reset the transaction to remove it
            schema_is_newly_created = True
            data_schema = create_schema(
                name=schema_name,
                table_count=1,
                metastore_id=self.metastore_id,
                commit=False,
                session=session,
            )

        table_id = self._create_table_table(
            data_schema.id, schema_name, table_name, session=session
        )

        # Remove creation of new schema if we failed to create table
        if table_id is None and schema_is_newly_created:
            session.expunge(data_schema)

        return table_id

    @with_session
    def sync_delete_table(self, schema_name, table_name, session=None):
        """DEPRECATED!!! PLEASE USE `sync_table` INSTEAD.
        Given a full qualified table name,
        Remove the table if it exists

        Arguments:
            schema_name {str} -- the schema name
            table_name {str} -- the table name

        """
        # Double check if the table is indeed removed
        table_exists = self.check_if_table_exists(schema_name, table_name)
        # If no schema, then table doesn't exist
        schema = get_schema_by_name(schema_name, self.metastore_id, session=session)
        if not table_exists and schema is not None:
            table = get_table_by_schema_id_and_name(
                schema.id, table_name, session=session
            )
            if table:
                delete_table(table_id=table.id, session=session)

    def check_if_table_exists(self, schema_name: str, table_name: str) -> bool:
        """Check if schema_name.table_name exists in DB

        Args:
            schema_name (str): Name of schema
            table_name (str): Name of table

        Returns:
            bool: True if exists, False otherwise
        """
        try:
            table_names = self.get_all_table_names_in_schema(schema_name)
            return table_name in table_names
        except Exception:
            # Assume table does not exist if an exception occurred while
            # trying to fetch all tables under schema
            return False

    def check_if_schema_exists(self, schema_name: str) -> bool:
        """Similar to above, but only checks if schema exists in DB

        Args:
            schema_name (str): Name of schema (may be 'catalog.schema' or just 'schema')

        Returns:
            bool: True if exists
        """
        schemas = self.get_all_schema_names()
        # Check both the schema name directly and catalog.schema format
        for schema in schemas:
            # Backward compatibility: convert string schema names to DataSchema objects
            if isinstance(schema, str):
                schema = DataSchema(name=schema, catalog=None)

            if schema.name == schema_name:
                return True
            if schema.catalog:
                if f"{schema.catalog.name}.{schema.name}" == schema_name:
                    return True
        return False

    def load(self):
        """Sync this metastore to the DB.  Non-combo loaders use this directly."""
        schemas = self._get_all_filtered_schemas()
        self._load_scoped(schemas)

    def get_sync_units(self) -> List[int]:
        """Return the unit IDs this loader will sync.  Base returns [self.metastore_id];
        ComboMetastoreLoader overrides to return all child IDs."""
        return [self.metastore_id]

    def load_unit(self, unit_id: int) -> None:
        """Sync a single unit.  Base delegates to load(); combo overrides to load_child()."""
        self.load()

    def _load_scoped(self, schemas: List["DataSchema"]):
        """Sync schemas to the DB: prune stale rows then upsert fresh ones."""
        schema_tables = []

        with DBSession() as session:
            current_schema_count = count_data_schema(self.metastore_id, session=session)
            LOG.info(
                f"Found {len(schemas)} schemas in metastore {self.metastore_id}, local schema count: {current_schema_count}"
            )

            self.delete_schema_not_in_metastore(
                self.metastore_id,
                schemas,
                session=session,
            )
            self.delete_catalog_not_in_metastore(
                self.metastore_id,
                schemas,
                session=session,
            )
            for schema in schemas:
                # Get filtered table names for the schema
                # The method handles both catalog extraction for qualified names (ACL checking)
                # and simple schema name for metastore API calls
                table_names = self._get_all_filtered_table_names(schema)

                LOG.info(
                    f"Processing schema '{schema.name}' (catalog={schema.catalog.name if schema.catalog else None}) with {len(table_names)} tables"
                )

                # Handle catalog if present
                catalog_id = None
                if schema.catalog:
                    db_catalog = self._ensure_catalog_exists(
                        schema.catalog, session=session
                    )
                    catalog_id = db_catalog.id if db_catalog else None

                # Create or update schema with catalog_id
                schema_id = create_schema(
                    name=schema.name,
                    catalog_id=catalog_id,
                    table_count=len(table_names),
                    metastore_id=self.metastore_id,
                    session=session,
                ).id

                self.delete_table_not_in_metastore(
                    schema_id, table_names, session=session
                )
                # Use just the schema name (not qualified) for table operations
                # The metastore APIs expect the simple schema/database name
                # Extract catalog name from DataSchema object to pass explicitly
                catalog_name = schema.catalog.name if schema.catalog else None
                schema_tables += [
                    (schema_id, schema.name, table_name, catalog_name)
                    for table_name in table_names
                ]

            # Commit all catalog and schema changes before proceeding to table creation
            session.commit()

        self._create_tables_batched(schema_tables)

    def get_latest_partition(
        self, schema_name: str, table_name: str, conditions: Dict[str, str] = None
    ):
        partitions = self.get_partitions(schema_name, table_name, conditions)
        latest_partition = partitions[-1] if partitions and len(partitions) else None
        return latest_partition

    def _create_tables_batched(self, schema_tables):
        """Create greenlets for create table batches

        Arguments:
            schema_tables {List[schema_id, schema_name, table_name]} -- List of configs to load table
        """
        batch_size = self._get_batch_size(len(schema_tables))
        greenlets = []
        thread_num = 0
        while True:
            table_batch = schema_tables[
                (thread_num * batch_size) : ((thread_num + 1) * batch_size)
            ]
            thread_num += 1

            if len(table_batch):
                greenlets.append(gevent.spawn(self._create_tables, table_batch))
            else:
                break
        gevent.joinall(greenlets)

    def _create_tables(self, schema_tables):
        with DBSession() as session:
            for schema_id, schema_name, table, catalog_name in schema_tables:
                self._create_table_table(
                    schema_id,
                    schema_name,
                    table,
                    from_batch=True,
                    session=session,
                    catalog_name=catalog_name,
                )

    @with_session
    def _create_table_table(
        self,
        schema_id,
        schema_name,
        table_name,
        table=None,
        columns=None,
        from_batch=False,
        session=None,
        catalog_name: Optional[str] = None,
    ):
        """Create or update a table.
        If detailed table info is given (parameter table and columns), it will just use
        them to create/update the table.  Otherwise, it will try to get the table
        info from the metastore first and then create/update.
        """
        if not table:
            try:
                if self._method_accepts_param("get_table_and_columns", "catalog_name"):
                    table, columns = self.get_table_and_columns(
                        schema_name, table_name, catalog_name
                    )
                else:
                    # Fallback for loaders without catalog_name parameter
                    table, columns = self.get_table_and_columns(schema_name, table_name)
            except Exception:
                LOG.error(traceback.format_exc())

        if not table:
            return None

        try:
            table_id = create_table(
                name=table.name,
                type=table.type,
                owner=table.owner,
                table_created_at=table.table_created_at,
                table_updated_by=table.table_updated_by,
                table_updated_at=table.table_updated_at,
                data_size_bytes=table.data_size_bytes,
                location=table.location,
                column_count=len(columns),
                schema_id=schema_id,
                golden=table.golden,
                boost_score=table.boost_score,
                commit=False,
                session=session,
            ).id
            create_table_information(
                data_table_id=table_id,
                description=table.description,
                latest_partitions=json.dumps(
                    table.latest_partitions or (table.partitions or [])[-5:]
                ),
                earliest_partitions=json.dumps(
                    table.earliest_partitions or (table.partitions or [])[:5]
                ),
                hive_metastore_description=table.raw_description,
                partition_keys=table.partition_keys,
                custom_properties=table.custom_properties,
                table_links=table.table_links,
                session=session,
            )
            if table.warnings is not None:
                create_table_warnings(
                    table_id=table_id,
                    warnings=table.warnings,
                    commit=False,
                    session=session,
                )

            delete_column_not_in_metastore(
                table_id,
                set(map(lambda c: c.name, columns)),
                commit=False,
                session=session,
            )

            for column in columns:
                column_id = create_column(
                    name=column.name,
                    type=column.type,
                    comment=column.comment,
                    description=column.description,
                    table_id=table_id,
                    commit=False,
                    session=session,
                ).id

                # create tags only if the metastore is configured to sync tags
                if self.loader_config.can_load_external_metadata(MetadataType.TAG):
                    create_column_tags(
                        column_id=column_id,
                        tags=column.tags,
                        commit=False,
                        session=session,
                    )

                # create data element associations only if the metastore is configured to sync data elements
                if self.loader_config.can_load_external_metadata(
                    MetadataType.DATA_ELEMENT
                ):
                    data_element_association = (
                        self._populate_column_data_element_association(
                            column.data_element
                        )
                    )
                    create_column_data_element_association(
                        metastore_id=self.metastore_id,
                        column_id=column_id,
                        data_element_association=data_element_association,
                        commit=False,
                        session=session,
                    )

            # create tags only if the metastore is configured to sync tags
            if self.loader_config.can_load_external_metadata(MetadataType.TAG):
                create_table_tags(
                    table_id=table_id,
                    tags=table.tags,
                    commit=False,
                    session=session,
                )

            # load owners if the metastore is configured to sync table owners
            if self.loader_config.can_load_external_metadata(MetadataType.OWNER):
                create_table_ownerships(
                    table_id=table_id,
                    owners=table.owners,
                    commit=False,
                    session=session,
                )
            session.commit()
            update_table_by_id(
                table_id,
                update_vector_store=not from_batch,
                session=session,
            )
            return table_id
        except Exception:
            session.rollback()
            LOG.error(traceback.format_exc())

    def _populate_column_data_element_association(
        self, data_element_association: DataElementAssociationTuple
    ) -> DataElementAssociationTuple:
        """If the value_data_element or key_data_element is a name instead of DataElementTuple,
        this function will help to replace the name with the actual DataElementTuple"""
        if data_element_association is None:
            return None

        value_data_element = data_element_association.value_data_element
        if type(value_data_element) is str:
            value_data_element = self.get_data_element(value_data_element)

        key_data_element = data_element_association.key_data_element
        if type(key_data_element) is str:
            key_data_element = self.get_data_element(key_data_element)

        return data_element_association._replace(
            value_data_element=value_data_element, key_data_element=key_data_element
        )

    def _filter_schemas(self, raw_schemas: List) -> List["DataSchema"]:
        """Apply this loader's catalog settings and ACL to a list of raw schema objects.

        Accepts both DataSchema namedtuples and plain strings (backward-compat).
        Returns only schemas that pass catalog settings and ACL validation.

        Used by :meth:`_get_all_filtered_schemas` for normal single-loader syncs,
        and by :class:`ComboMetastoreLoader` ``load_child`` to apply the *combo's*
        settings to child-sourced raw schemas rather than each child's own settings.
        """
        filtered = []
        for schema in raw_schemas:
            # Backward compatibility: convert string schema names to DataSchema objects
            if isinstance(schema, str):
                schema = DataSchema(name=schema, catalog=None)

            # Apply catalog settings BEFORE filtering
            schema = self._apply_catalog_settings(schema)

            # Build qualified name for ACL checking
            qualified_name = (
                f"{schema.catalog.name}.{schema.name}"
                if schema.catalog
                else schema.name
            )
            if self.acl_checker.is_schema_valid(qualified_name):
                filtered.append(schema)
        return filtered

    @with_exception
    def _get_all_filtered_schemas(self) -> List["DataSchema"]:
        all_schemas = self.get_all_schema_names()
        return self._filter_schemas(all_schemas)

    @with_exception
    def _get_all_filtered_table_names(self, schema: DataSchema) -> List[str]:
        # Build qualified name from DataSchema object for ACL checking
        qualified_schema_name = (
            f"{schema.catalog.name}.{schema.name}" if schema.catalog else schema.name
        )

        # Extract catalog name to pass explicitly
        catalog_name = schema.catalog.name if schema.catalog else None

        if self._method_accepts_param("get_all_table_names_in_schema", "catalog_name"):
            table_names = self.get_all_table_names_in_schema(schema.name, catalog_name)
        else:
            # Fallback for loaders without catalog_name parameter
            table_names = self.get_all_table_names_in_schema(schema.name)

        return [
            table_name
            for table_name in table_names
            if self.acl_checker.is_table_valid(qualified_schema_name, table_name)
        ]

    def _get_batch_size(self, num_tables: int):
        parallelization_setting = self._get_parallelization_setting()
        num_threads = parallelization_setting["num_threads"]
        min_batch_size = parallelization_setting["min_batch_size"]

        batch_size = max(int(math.ceil(num_tables / num_threads)), min_batch_size)
        return batch_size

    def get_partitions(
        self, schema_name: str, table_name: str, conditions: Dict[str, str] = None
    ) -> List[str]:
        """Override this method to return a list of the given table's partitions
        Returns None by default.

        Returns:
            List[str] -- [partition keys]
        """
        return None

    @abstractmethod
    def get_all_schema_names(self) -> List["DataSchema"] | List[str]:
        """Override this to get a list of all schemas with their catalog information

        Returns:
            List[DataSchema] -- List of DataSchema NamedTuples with name and optional catalog
        """
        pass

    @overload
    def get_all_table_names_in_schema(self, schema_name: str) -> List[str]:
        """Get table names using 2-level naming (schema.table)"""
        pass

    @overload
    def get_all_table_names_in_schema(
        self, schema_name: str, catalog_name: Optional[str]
    ) -> List[str]:
        """Get table names using 3-level naming (catalog.schema.table)"""
        pass

    @abstractmethod
    def get_all_table_names_in_schema(
        self, schema_name: str, catalog_name: Optional[str] = None
    ) -> List[str]:
        """Override this to get a list of all table names under given schema

        Arguments:
            schema_name {str}
            catalog_name {Optional[str]}

        Returns:
            List[str] -- [A list of tbale names]
        """
        pass

    @overload
    def get_table_and_columns(
        self, schema_name: str, table_name: str
    ) -> Tuple[DataTable, List[DataColumn]]:
        """Get table metadata using 2-level naming (schema.table)"""
        pass

    @overload
    def get_table_and_columns(
        self, schema_name: str, table_name: str, catalog_name: Optional[str]
    ) -> Tuple[DataTable, List[DataColumn]]:
        """Get table metadata using 3-level naming (catalog.schema.table)"""
        pass

    @abstractmethod
    def get_table_and_columns(
        self, schema_name: str, table_name: str, catalog_name: Optional[str] = None
    ) -> Tuple[DataTable, List[DataColumn]]:
        """Override this to get the table given by schema name and table name, and a list of its columns

        Arguments:
            schema_name {[str]}
            table_name {[str]}
            catalog_name {Optional[str]}

        Returns:
            Tuple[DataTable, List[DataColumn]] -- Return [null, null] if not found
        """
        pass

    def get_data_element(self, data_element_name: str) -> Optional[DataElementTuple]:
        """Override this to get data element by name"""
        pass

    def get_schema_location(self, schema_name: str) -> str:
        """Get schema location, used by table uploader"""
        pass

    @abstractclassmethod
    def get_metastore_params_template(self) -> AllFormField:
        """Override this to get the form field required for the metastore

        Returns:
            AllFormField -- The form field template
        """
        pass

    def _get_parallelization_setting(self):
        """Override this to have different parallelism.

           The num_threads determines the maximum number of threads
           that will be used. The min_batch_size determines the minimum
           number of tables each threads will process.

           For example, if you have num_threads at 2 and min_batch_size at 100.
           Then only 1 thread would be used unless you process more than 100 tables.

        Returns:
            dict: 'num_threads' | 'min_batch_size' -> int
        """
        return {"num_threads": 10, "min_batch_size": 50}

    @classmethod
    def serialize_loader_class(cls):
        return {
            "name": cls.__name__,
            "template": cls.get_metastore_params_template().to_dict(),
        }

    @with_session
    def delete_schema_not_in_metastore(self, metastore_id, schemas, session=None):
        """Delete schemas from DB that are not in the metastore."""
        expected_schemas = {
            (schema.catalog.name if schema.catalog else None, schema.name)
            for schema in schemas
        }

        for data_schema in iterate_data_schema(metastore_id, session=session):
            LOG.info("checking schema %d" % data_schema.id)

            catalog_name = None
            if data_schema.catalog_id:
                db_catalog = get_catalog_by_id(data_schema.catalog_id, session=session)
                catalog_name = db_catalog.name if db_catalog else None

            schema_key = (catalog_name, data_schema.name)
            if schema_key not in expected_schemas:
                for table in data_schema.tables:
                    table_id = table.id
                    delete_table(table_id=table_id, commit=False, session=session)
                    delete_es_table_by_id(table_id)
                delete_schema(id=data_schema.id, commit=False, session=session)
                LOG.info(f"Deleted schema {data_schema.name} ({data_schema.id})")

        session.commit()

    @with_session
    def delete_catalog_not_in_metastore(self, metastore_id, schemas, session=None):
        """Delete catalogs from DB that are no longer present in the metastore.

        Must be called after delete_schema_not_in_metastore so child schemas
        are already removed before the catalog row is deleted.
        """
        expected_catalogs = {
            schema.catalog.name for schema in schemas if schema.catalog is not None
        }

        for db_catalog in get_all_catalogs(metastore_id, session=session):
            if db_catalog.name not in expected_catalogs:
                delete_catalog(catalog_id=db_catalog.id, commit=False, session=session)
                LOG.info(
                    f"Deleted orphaned catalog {db_catalog.name} ({db_catalog.id})"
                )

        session.commit()

    @with_session
    def delete_table_not_in_metastore(self, schema_id, table_names, session=None):
        BATCH_SIZE = 500
        delete_count = 0
        db_tables = get_table_by_schema_id(schema_id, session=session)

        with session.no_autoflush:
            for data_table in db_tables:
                if data_table.name not in table_names:
                    table_id = data_table.id
                    delete_table(table_id=table_id, commit=False, session=session)
                    delete_es_table_by_id(table_id)
                    LOG.info(f"Deleted table {data_table.name} ({table_id})")

                    delete_count += 1
                    if delete_count % BATCH_SIZE == 0:
                        session.commit()
                        LOG.info(f"Committed batch of {BATCH_SIZE} deletions")

            # Final commit for any remaining deletions
            if delete_count % BATCH_SIZE != 0:
                session.commit()
                LOG.info(
                    f"Committed final batch of {delete_count % BATCH_SIZE} deletions"
                )

        LOG.info(f"Deleted a total of {delete_count} tables from schema {schema_id}")


@with_session
def delete_column_not_in_metastore(table_id, column_names, commit=True, session=None):
    db_columns = get_column_by_table_id(table_id, session=session)

    for column in db_columns:
        if column.name not in column_names:
            delete_column(id=column.id, commit=False, session=session)
            LOG.info("deleted column %d" % column.id)
    if commit:
        session.commit()
    else:
        session.flush()
