import threading
import time

from app.db import DBSession
from const.query_execution import QueryExecutionStatus
from lib.logger import get_logger
from lib.stats_logger import ACTIVE_TASKS, ACTIVE_WORKERS, stats_logger
from models.query_execution import QueryExecution
from sqlalchemy.sql import func

LOG = get_logger(__file__)


def send_stats_logger_metrics(celery):
    while True:
        try:
            # Celery stats #
            i = celery.control.inspect()

            active = i.active() or {}

            active_workers = list(active.keys())
            active_tasks = 0
            for worker in active_workers:
                if worker in active:
                    active_tasks += len(active[worker])

            stats_logger.gauge(ACTIVE_WORKERS, len(active_workers))
            stats_logger.gauge(ACTIVE_TASKS, active_tasks)

            # Querybook stats #
            with DBSession() as session:
                # Count the number of queries that are in each state
                query_status_count = (
                    session.query(QueryExecution.status, func.count())
                    .group_by(QueryExecution.status)
                    .all()
                )

                for status, count in query_status_count:
                    stats_logger.gauge(
                        f"query_executions.status.{QueryExecutionStatus(status).name.lower()}",
                        count,
                    )

        except Exception:
            LOG.exception("Error collecting celery stats")

        time.sleep(10)


def start_stats_logger_monitor(celery):
    thread = threading.Thread(
        target=send_stats_logger_metrics, args=[celery], daemon=True
    )
    thread.start()
