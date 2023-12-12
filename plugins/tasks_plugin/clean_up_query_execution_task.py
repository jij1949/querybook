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
from sqlalchemy.sql.expression import func, and_

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
    # Select running TaskRunRecords
    # Ignore system tasks and tasks that are less than an hour old
    running_task_run_records = (
        session.query(TaskRunRecord)
        .filter(
            and_(
                TaskRunRecord.status == TaskRunStatus.RUNNING,
                TaskRunRecord.name.like(f"{DATADOC_SCHEDULE_PREFIX}%"),
                TaskRunRecord.created_at < (func.now() - text("INTERVAL 1 HOUR")),
            )
        )
        .all()
    )

    LOG.info(
        f"Found {len(running_task_run_records)} running TaskRunRecords, checking for stuck records"
    )

    # Map comprehension to filter out any TaskRunRecords that have running query executions
    stuck_task_run_records = [
        record.id
        for record in running_task_run_records
        if (
            session.query(QueryExecution)
            .join(DataCellQueryExecution)
            .join(DataCell)
            .join(DataDocDataCell)
            .join(DataDoc)
            .filter(
                QueryExecution.status == QueryExecutionStatus.RUNNING,
                DataDoc.id == int(record.name[len(DATADOC_SCHEDULE_PREFIX) :]),
            )
            .count()
            == 0
        )
    ]

    LOG.info(f"Found {len(stuck_task_run_records)} stuck TaskRunRecords to update")

    # Check if there are any running query executions for each task run record
    for record_id in stuck_task_run_records:
        # Note: on_datadoc_completion commits the session, so we need to re-query the record
        # to avoid an error when accessing the previously-retrieved records
        # That's why we're looping through record_ids instead of records

        record = session.query(TaskRunRecord).get(record_id)
        doc_id = int(record.name[len(DATADOC_SCHEDULE_PREFIX) :])
        task_schedule = get_task_schedule_by_name(record.name, session=session)

        LOG.debug(
            f"!> Stuck Record ID: {record.id}, Record Name: {record.name}, Record Created At: {record.created_at}"
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
