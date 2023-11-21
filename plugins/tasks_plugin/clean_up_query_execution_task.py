from app.db import with_session
from app.flask_app import celery
from lib.logger import get_logger
from logic.query_execution import clean_up_query_execution
from logic.schedule import (
    DATADOC_SCHEDULE_PREFIX,
    get_task_schedule_by_name,
    with_task_logging,
)

from sqlalchemy import text
from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import func, and_, select

from app.flask_app import celery
from app.db import with_session
from const.query_execution import QueryExecutionStatus
from const.schedule import TaskRunStatus
from lib.logger import get_logger

from models.query_execution import QueryExecution
from models.schedule import (
    TaskRunRecord,
)
from models.datadoc import DataCell, DataCellQueryExecution, DataDoc, DataDocDataCell
from tasks.run_datadoc import on_datadoc_completion

LOG = get_logger(__file__)


@celery.task(bind=True)
@with_task_logging()
def clean_up_query_execution_task(self):
    # Built-in clean up for query executions that are marked running but can't be found in the celery queue
    clean_up_query_execution()

    # Clean up any task run record that are "stuck" in running state, but no query executions are running
    clean_up_stuck_task_run_records()


@with_session
def clean_up_stuck_task_run_records(dry_run=False, session=None):
    trr = aliased(TaskRunRecord)

    # Subquery to count running query executions for each task run record
    running_query_executions_subquery = (
        select(func.count())
        .select_from(trr)
        .join(DataDoc, trr.name == func.concat(DATADOC_SCHEDULE_PREFIX, DataDoc.id))
        .join(DataDocDataCell, DataDoc.id == DataDocDataCell.data_doc_id)
        .join(DataCell, DataDocDataCell.data_cell_id == DataCell.id)
        .outerjoin(
            DataCellQueryExecution, DataCell.id == DataCellQueryExecution.data_cell_id
        )
        .outerjoin(
            QueryExecution,
            QueryExecution.id == DataCellQueryExecution.query_execution_id,
        )
        .filter(
            trr.name == func.concat(DATADOC_SCHEDULE_PREFIX, DataDoc.id),
            QueryExecution.status == QueryExecutionStatus.RUNNING,
            QueryExecution.id.isnot(None),
        )
        .scalar_subquery()
    )

    # Select running TaskRunRecords which have no running query executions
    # Ignore system tasks and tasks that are less than an hour old
    matching_records = (
        session.query(
            trr,
            running_query_executions_subquery.label("running_query_executions_count"),
        )
        .filter(
            and_(
                trr.status == TaskRunStatus.RUNNING,
                trr.name.like(f"{DATADOC_SCHEDULE_PREFIX}%"),
                trr.created_at < (func.now() - text("INTERVAL 1 HOUR")),
                running_query_executions_subquery == 0,
            )
        )
        .all()
    )

    LOG.info(f"Found {len(matching_records)} stuck TaskRunRecords to update")

    # Print or process the matching records as needed
    for record, count in matching_records:
        doc_id = int(record.name[len(DATADOC_SCHEDULE_PREFIX) :])
        task_schedule = get_task_schedule_by_name(record.name, session=session)

        LOG.debug(
            f"!> Record ID: {record.id}, Record Name: {record.name}, Record Created At: {record.created_at}, Running Query Executions Count: {count}"
        )

        if not dry_run:
            on_datadoc_completion(
                doc_id=doc_id,
                record_id=record.id,
                is_success=False,
                error_msg="Task failed due to an internal Querybook error; no running query executions found.",
                notifications=task_schedule.kwargs.get("notifications", []),
                exports=task_schedule.kwargs.get("exports", []),
                user_id=task_schedule.kwargs.get("user_id"),
            )
