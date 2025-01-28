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
    d.platinum,
    d.popularity,
    d.importance_score,
    d.collibra_table_link,
    d.collibra_tags,
    d.deprecation_status,
    d.deprecation_date,
    d.deprecation_notes
    FROM plat_metrics.cleansed_eg_table_discovery d
    ORDER BY d.popularity ASC
    LIMIT {limit}
"""


@celery.task(bind=True)
@with_task_logging()
def top_tier_task(
    self,
    query_engine_id: int = 1,
    min_user_count: int = 10,
    min_number_of_queries: int = 30,
    limit: int = 10000,
):
    with DBSession() as session:
        (
            executor,
            executor_params,
            engine_dict,
        ) = _get_executor_and_params_by_engine_id(query_engine_id, session=session)
        try:
            # By default this runs as the query engine user, but you can set a proxy user
            # executor_params["proxy_user"] = "dbauman"

            cursor: CursorBaseClass = executor._get_client(executor_params).cursor()

            LOG.debug(f"Running Top Tier query...")
            formatted_query = query_template.format(
                min_user_count=min_user_count,
                min_number_of_queries=min_number_of_queries,
                limit=limit,
            )
            cursor.run(formatted_query)
            cursor.poll_until_finish()

            # Retrieve all results
            rows = cursor.get_rows()
            LOG.info(f"Top Tier Task results: {len(rows)} rows")
            # Log first row
            if len(rows) == 0:
                return
            LOG.info(f"First row: {rows[0]}")

            # Create a new table in session using raw SQL, and insert the rows
            session.execute("DROP TABLE IF EXISTS eg_top_tier_table")
            session.execute(
                """
                CREATE TABLE eg_top_tier_table (
                    source_data_lake VARCHAR(255),
                    source_schema_name VARCHAR(255),
                    table_name VARCHAR(255),
                    trending BOOLEAN,
                    platinum BOOLEAN,
                    popularity INT,
                    importance_score FLOAT,
                    collibra_table_link VARCHAR(255),
                    collibra_tags JSON,
                    deprecation_status VARCHAR(255),
                    deprecation_date VARCHAR(255),
                    deprecation_notes TEXT
                )
                """
            )
            values = [
                {
                    "source_data_lake": source_data_lake,
                    "source_schema_name": source_schema_name,
                    "table_name": table_name,
                    "trending": trending,
                    "platinum": platinum,
                    "popularity": popularity,
                    "importance_score": importance_score,
                    "collibra_table_link": collibra_table_link,
                    "collibra_tags": (
                        json.dumps(collibra_tags) if collibra_tags else None
                    ),
                    "deprecation_status": (
                        deprecation_status if deprecation_status else None
                    ),
                    "deprecation_date": deprecation_date if deprecation_date else None,
                    "deprecation_notes": (
                        deprecation_notes if deprecation_notes else None
                    ),
                }
                for (
                    (
                        source_data_lake,
                        source_schema_name,
                        table_name,
                        trending,
                        platinum,
                        popularity,
                        importance_score,
                        collibra_table_link,
                        collibra_tags,
                        deprecation_status,
                        deprecation_date,
                        deprecation_notes,
                    )
                ) in rows
            ]

            session.execute(
                """
                INSERT INTO eg_top_tier_table (
                    source_data_lake, source_schema_name, table_name,
                    trending, platinum, popularity, importance_score,
                    collibra_table_link, collibra_tags, deprecation_status,
                    deprecation_date, deprecation_notes
                ) VALUES (
                    :source_data_lake, :source_schema_name, :table_name,
                    :trending, :platinum, :popularity, :importance_score,
                    :collibra_table_link, :collibra_tags, :deprecation_status,
                    :deprecation_date, :deprecation_notes
                )
                """,
                values,
            )
            session.commit()
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
