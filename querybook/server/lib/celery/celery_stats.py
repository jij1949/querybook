import time
import threading
from app.db import DBSession
from const.query_execution import QueryExecutionStatus
from lib.logger import get_logger
from lib.stats_logger import (
    stats_logger,
    ACTIVE_WORKERS,
    ACTIVE_TASKS,
    QUERY_INITIALIZED,
)
from models.query_execution import QueryExecution

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
                # Count the number of queries that are in the initialized state
                # AKA "Send to Worker"
                # This indicates a bottleneck on the Querybook worker side
                initialized_queries = (
                    session.query(QueryExecution)
                    .filter(QueryExecution.status == QueryExecutionStatus.INITIALIZED)
                    .count()
                )
                stats_logger.gauge(QUERY_INITIALIZED, initialized_queries)

        except Exception:
            LOG.exception("Error collecting celery stats")

        time.sleep(10)


def start_stats_logger_monitor(celery):
    thread = threading.Thread(
        target=send_stats_logger_metrics, args=[celery], daemon=True
    )
    thread.start()
