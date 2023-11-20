from app.flask_app import celery
from logic.query_execution import clean_up_query_execution
from logic.schedule import clean_up_stuck_task_run_records, with_task_logging


@celery.task(bind=True)
@with_task_logging()
def clean_up_query_execution_task(self):
    # Built-in clean up for query executions that are marked running but can't be found in the celery queue
    clean_up_query_execution()

    # Clean up any task run record that are "stuck" in running state, but no query executions are running
    clean_up_stuck_task_run_records()
