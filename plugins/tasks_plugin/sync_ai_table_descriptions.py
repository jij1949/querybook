from lib.query_executor.base_client import CursorBaseClass

from app.flask_app import celery
from logic.schedule import with_task_logging
from app.db import DBSession
from lib.logger import get_logger
from logic.admin import get_query_engine_by_id
from lib.query_executor.all_executors import get_executor_class


LOG = get_logger(__file__)

# Query to get the generated table descriptions
query_template = """
    SELECT
        d.source_data_lake,
        d.source_schema_name,
        d.table_name,
        d.business_value,
        d.table_purpose,
        d.key_characteristics,
        d.partition_information
    FROM plat_metrics.cleansed_eg_table_discovery_descriptions d
    ORDER BY d.table_name
    OFFSET {offset}
    LIMIT {limit}
"""


@celery.task(bind=True)
@with_task_logging()
def sync_ai_table_descriptions_task(
    self,
    # Trino query engine ID to run queries with
    query_engine_id: int = 1,
    # Number of rows to fetch in each batch
    batch_size: int = 10000,
    # Maximum number of rows to fetch (across all batches); set to 0 to fetch all rows
    limit: int = 25000,
):
    with DBSession() as session:
        (
            executor,
            executor_params,
            engine_dict,
        ) = _get_executor_and_params_by_engine_id(query_engine_id, session=session)
        try:
            # Create a new table in session using raw SQL
            session.execute("DROP TABLE IF EXISTS eg_table_descriptions_table")
            session.execute(
                """
                CREATE TABLE eg_table_descriptions_table (
                    source_data_lake VARCHAR(255),
                    source_schema_name VARCHAR(255),
                    table_name VARCHAR(255),
                    business_value TEXT,
                    table_purpose TEXT,
                    key_characteristics TEXT,
                    partition_information TEXT
                )
                """
            )

            # By default this runs as the query engine user, but you can set a proxy user
            # executor_params["proxy_user"] = "dbauman"

            cursor: CursorBaseClass = executor._get_client(executor_params).cursor()

            offset = 0

            while True:
                # Ensure we don't fetch more than the overall limit
                batch_limit = (
                    batch_size if limit == 0 else min(batch_size, limit - offset)
                )

                LOG.info(f"Sync AI Table Descriptions Task: Batch offset: {offset}, limit: {batch_limit}")
                paged_query = query_template.format(
                    limit=batch_limit,
                    offset=offset,
                )
                cursor.run(paged_query)
                cursor.poll_until_finish()

                # Retrieve all results
                rows = cursor.get_rows()
                if not rows:
                    break

                LOG.info(
                    f"Sync AI Table Descriptions Task: Batch Results: {len(rows)} rows, offset: {offset}"
                )
                LOG.debug(f"First row: {rows[0]}")

                values = [
                    {
                        "source_data_lake": source_data_lake,
                        "source_schema_name": source_schema_name,
                        "table_name": table_name,
                        "business_value": business_value,
                        "table_purpose": table_purpose,
                        "key_characteristics": key_characteristics,
                        "partition_information": partition_information
                    }
                    for (
                        (
                            source_data_lake,
                            source_schema_name,
                            table_name,
                            business_value,
                            table_purpose,
                            key_characteristics,
                            partition_information
                        )
                    ) in rows
                ]

                session.execute(
                    """
                    INSERT INTO eg_table_descriptions_table (
                        source_data_lake, source_schema_name, table_name,
                        business_value, table_purpose, key_characteristics,
                        partition_information
                    ) VALUES (
                        :source_data_lake, :source_schema_name, :table_name,
                        :business_value, :table_purpose, :key_characteristics,
                        :partition_information
                    )
                    """,
                    values,
                )
                session.commit()

                # Increment the offset
                offset += batch_size

                # If we get fewer than the batch size, we're done
                if len(rows) < batch_size:
                    break

                # If we have a limit and we've reached it, we're done
                if limit and offset >= limit:
                    LOG.debug(f"Sync AI Table Descriptions Task: Reached limit of {limit} rows")
                    break

            LOG.debug("Sync AI Table Descriptions Task completed 🎉")

        except Exception as e:
            LOG.error(f"Sync AI Table Descriptions Task failed: {e}")
            session.rollback()
            raise e


def _get_executor_and_params_by_engine_id(engine_id: int, session=None):
    engine = get_query_engine_by_id(engine_id, session=session)

    if engine is None or engine.deleted_at is not None:
        raise ValueError(f"Engine {engine_id} does not exist or is deleted")

    executor_params = engine.get_engine_params()
    executor = get_executor_class(engine.language, engine.executor)
    return executor, executor_params, engine.to_dict_admin()
