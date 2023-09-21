from app.flask_app import celery
from logic.query_execution import clean_up_query_execution
from logic.schedule import with_task_logging


@celery.task(bind=True)
@with_task_logging()
def clean_up_query_execution_task(self):
    clean_up_query_execution()
