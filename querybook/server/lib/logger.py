import logging
import sys

from celery import current_task
from env import QuerybookSettings


class CeleryTaskContextFilter(logging.Filter):
    """Inject a Celery task-context segment onto each log record.

    Inside a running Celery task the segment is "[task=<name> task_id=<id>] ";
    otherwise it is an empty string so non-task (e.g. web server) logs stay clean.
    """

    def filter(self, record):
        # This runs on every log line, and an exception raised here would
        # propagate out of the logging call itself (the stdlib does not catch
        # filter errors). current_task is a proxy that resolves to None outside
        # a worker, but resolve it defensively so an unexpected state (e.g. a
        # monkey-patched task) can never break logging.
        try:
            task = current_task
            request = getattr(task, "request", None) if task else None
            task_id = getattr(request, "id", None) if request else None
            task_name = getattr(task, "name", "-") if task_id else "-"
        except Exception:
            task_id = None
            task_name = "-"

        record.celery_task_context = (
            f"[task={task_name} task_id={task_id}] " if task_id else ""
        )
        return True


def get_logger(module):
    log_format = (
        '[%(asctime)s] %(celery_task_context)s- %(name)s - %(levelname)-8s"%(message)s"'
    )
    date_format = "%Y-%m-%d %a %H:%M:%S"
    log = logging.getLogger(module)

    # Guard against duplicate handlers if get_logger is called again for the
    # same module (previously each call stacked another stderr handler).
    if log.handlers:
        return log

    # Our handlers emit directly; don't also propagate to Celery's hijacked
    # root logger (that was the source of the duplicated log lines).
    log.propagate = False

    try:
        formatter = logging.Formatter(fmt=log_format, datefmt=date_format)
        # Attach the filter to each handler, not the logger. Handler filters run
        # for every record the handler processes, including records that reach it
        # by propagation from a descendant logger; a logger-level filter would
        # not run for those, leaving celery_task_context unset and raising a
        # KeyError in the formatter.
        context_filter = CeleryTaskContextFilter()

        log_stream_handler = logging.StreamHandler(sys.stderr)
        log_stream_handler.setFormatter(formatter)
        log_stream_handler.addFilter(context_filter)
        log.addHandler(log_stream_handler)

        if QuerybookSettings.LOG_LOCATION is not None:
            log_file_handler = logging.FileHandler(QuerybookSettings.LOG_LOCATION)
            log_file_handler.setFormatter(formatter)
            log_file_handler.addFilter(context_filter)
            log.addHandler(log_file_handler)
    except IOError:
        print("{} not found".format(QuerybookSettings.LOG_LOCATION))
    finally:
        # Avoid debug logs in production
        log.setLevel(logging.INFO if QuerybookSettings.PRODUCTION else logging.DEBUG)
        return log
