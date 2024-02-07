import re

from logic.metastore import get_all_table
from app.flask_app import celery
from logic.schedule import with_task_logging
from app.db import DBSession
from lib.logger import get_logger
from logic.metastore import get_all_table
from logic.vector_store import record_table


LOG = get_logger(__file__)


@celery.task(bind=True)
@with_task_logging()
def ingest_vector_index(
    self,
    batch_size: int = 100,
    schema_regex: str = "querybook2",
):
    with DBSession() as session:
        batch_size = 100
        offset = 0

        while True:
            tables = get_all_table(
                limit=batch_size,
                offset=offset,
                session=session,
            )

            for table in tables:
                if not re.match(schema_regex, table.data_schema.name):
                    continue

                full_table_name = f"{table.data_schema.name}.{table.name}"
                LOG.info(f"Ingesting table: {full_table_name}")
                record_table(table=table, ingest_sample_queries=True, session=session)

            if len(tables) < batch_size:
                break

            offset += batch_size
