from lib.query_executor.base_client import CursorBaseClass

from app.flask_app import celery
from lib.utils import json
from logic.schedule import with_task_logging
from app.db import DBSession
from lib.logger import get_logger
from logic.admin import get_query_engine_by_id
from lib.query_executor.all_executors import get_executor_class


LOG = get_logger(__file__)

# Query to get the top tier tables
query_template = """
    SELECT
        d.source_data_lake,
        d.source_schema_name,
        d.table_name,
        d.trending,
        d.popularity,
        d.importance_score
    FROM plat_metrics.cleansed_eg_table_discovery d
    WHERE
        popularity <= {popularity_threshold}
    ORDER BY d.popularity ASC
    OFFSET {offset}
    LIMIT {limit}
"""


@celery.task(bind=True)
@with_task_logging()
def top_tier_task(
    self,
    # Trino query engine ID to run queries with
    query_engine_id: int = 1,
    # Number of rows to fetch in each batch
    batch_size: int = 10000,
    # Maximum number of rows to fetch (across all batches); set to 0 to fetch all rows
    limit: int = 25000,
    # Popularity threshold for top tier tables
    popularity_threshold: int = 20000,
):
    with DBSession() as session:
        (
            executor,
            executor_params,
            engine_dict,
        ) = _get_executor_and_params_by_engine_id(query_engine_id, session=session)
        try:
            # Create a new table in session using raw SQL
            session.execute("DROP TABLE IF EXISTS eg_top_tier_table")
            session.execute(
                """
                CREATE TABLE eg_top_tier_table (
                    source_data_lake VARCHAR(255),
                    source_schema_name VARCHAR(255),
                    table_name VARCHAR(255),
                    trending BOOLEAN,
                    popularity INT,
                    importance_score FLOAT
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

                LOG.info(f"Top Tier Task: Batch offset: {offset}, limit: {batch_limit}")
                paged_query = query_template.format(
                    limit=batch_limit,
                    offset=offset,
                    popularity_threshold=popularity_threshold,
                )
                cursor.run(paged_query)
                cursor.poll_until_finish()

                # Retrieve all results
                rows = cursor.get_rows()
                if not rows:
                    break

                LOG.info(
                    f"Top Tier Task: Batch Results: {len(rows)} rows, offset: {offset}"
                )
                LOG.debug(f"First row: {rows[0]}")

                values = [
                    {
                        "source_data_lake": source_data_lake,
                        "source_schema_name": source_schema_name,
                        "table_name": table_name,
                        "trending": trending,
                        "popularity": popularity,
                        "importance_score": importance_score,
                    }
                    for (
                        (
                            source_data_lake,
                            source_schema_name,
                            table_name,
                            trending,
                            popularity,
                            importance_score,
                        )
                    ) in rows
                ]

                session.execute(
                    """
                    INSERT INTO eg_top_tier_table (
                        source_data_lake, source_schema_name, table_name,
                        trending, popularity, importance_score
                    ) VALUES (
                        :source_data_lake, :source_schema_name, :table_name,
                        :trending, :popularity, :importance_score
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
                    LOG.debug(f"Top Tier Task: Reached limit of {limit} rows")
                    break

            LOG.debug(f"Top Tier Task completed 🎉")

        except Exception as e:
            LOG.error(f"Top Tier Task failed: {e}")
            session.rollback()
            raise e


def _get_executor_and_params_by_engine_id(engine_id: int, session=None):
    engine = get_query_engine_by_id(engine_id, session=session)

    if engine is None or engine.deleted_at is not None:
        raise ValueError(f"Engine {engine_id} does not exist or is deleted")

    executor_params = engine.get_engine_params()
    executor = get_executor_class(engine.language, engine.executor)
    return executor, executor_params, engine.to_dict_admin()
