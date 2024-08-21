import re

from app.flask_app import celery
from logic.schedule import with_task_logging
from app.db import DBSession
from lib.logger import get_logger
from logic.vector_store import record_table
from models.metastore import DataSchema, DataTable


LOG = get_logger(__file__)


@celery.task(bind=True)
@with_task_logging()
def ingest_vector_index(
    self,
    batch_size: int = 100,
    schema_regex: str = "querybook2",
    top_tier_only: bool = False,
):
    with DBSession() as session:

        schema_offset = 0
        while True:

            schemas = (
                session.query(DataSchema).offset(schema_offset).limit(batch_size).all()
            )

            for schema in schemas:
                if not re.match(schema_regex, schema.name):
                    # Skip non matching schema
                    continue

                LOG.info(f"Vector indexing schema: {schema.name}")

                table_offset = 0

                while True:
                    tables = (
                        session.query(DataTable)
                        .filter(DataTable.schema_id == schema.id)
                        .offset(table_offset)
                        .limit(batch_size)
                        .all()
                    )

                    for table in tables:

                        if top_tier_only and not table.golden:
                            # Skip non top tier tables
                            continue

                        full_table_name = f"{table.data_schema.name}.{table.name}"
                        LOG.info(f"Ingesting table: {full_table_name}")
                        record_table(
                            table=table, ingest_sample_queries=True, session=session
                        )

                    if len(tables) < batch_size:
                        break

                    table_offset += batch_size

                schema_offset += batch_size
