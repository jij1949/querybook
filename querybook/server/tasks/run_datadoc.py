from celery import chain
from celery.contrib.abortable import AbortableTask

from app.db import with_session, DBSession
from app.flask_app import celery, socketio

from const.db import (
    description_length,
)
from const.query_execution import QueryExecutionStatus, QueryExecutionType
from const.schedule import TaskRunStatus

from lib.logger import get_logger
from lib.query_analysis.templating import render_templated_query
from lib.scheduled_datadoc.export import export_datadoc
from lib.scheduled_datadoc.legacy import convert_if_legacy_datadoc_schedule
from lib.scheduled_datadoc.notification import notifiy_on_datadoc_complete

from logic import datadoc as datadoc_logic
from logic import query_execution as qe_logic
from logic import schedule as schedule_logic
from logic.schedule import (
    create_task_run_record_for_celery_task,
    update_task_run_record,
)
from tasks.run_query import run_query_task
import re

LOG = get_logger(__file__)
GENERIC_QUERY_FAILURE_MSG = "Execution did not finish successfully, workflow failed"

# List of regex patterns for error messages that shouldn't retry
NON_RETRYABLE_ERRORS = [
    r'\{"line": .*, "char": .*, "message": .*\}',
    r"Exceeded CPU limit of",
    r"Query exceeded distributed user memory limit of",
    r"Query exceeded maximum time limit of",
    r"Query exceeded per-node memory limit of",
    r"Query killed\. Message: Killed via web UI",
    r"Query killed\. No message provided\.",
    r"Query was canceled",
    # r"Access Denied: Cannot",
    # r"Array subscript must be less than or equal to array length",
    # r"Cannot apply operator: ",
    # r"Cannot cast .* to .*",
    # r"Cannot unnest type:",
    # r"Could not parse rfc1738",
    # r"Decimal overflow",
    # r"Division by zero",
    # r"Filter required on .* for at least one partition column: .*",
    # r"Invalid format: \"\"",
    # r"Invalid partition value ",
    # r"Invalid position .* and length .* in page with .* positions",
    # r"Key not present in map:",
    # r"Modifying Hive table rows is only supported for transactional tables",
    # r"Partition no longer exists",
    # r"Query exceeded the maximum execution time limit of",
    # r"Query exceeded the maximum planning time limit of",
    # r"Remote page is too large",
    # r"ROW comparison not supported",
    # r"Row type must have at least 1 field",
    # r"Size of pages index cannot exceed",
    # r"SQL array indices start at 1",
    # r"Unable to cast",
    # r"Unknown type",
    # r"Unsupported Hive type:",
    # r"Unsupported Trino column type",
    # r"Value cannot be cast to",
]


@celery.task(bind=True)
def run_datadoc(self, *args, **kwargs):
    """
    This function wraps run_datadoc_with_config to convert
    legacy schedule config to current
    """
    run_datadoc_with_config(self, *args, **convert_if_legacy_datadoc_schedule(kwargs))


def run_datadoc_with_config(
    self,
    doc_id,
    start_index=0,
    notifications=[],
    user_id=None,
    execution_type=QueryExecutionType.SCHEDULED.value,
    # Exporting related settings
    exports=[],
    retry={"delay_sec": 0, "max_retries": 0, "enabled": False},
    disable_if_running_doc=False,
    *args,
    **kwargs,
):
    tasks_to_run = []
    record_id = None

    with DBSession() as session:
        if disable_if_running_doc:
            runs, _ = schedule_logic.get_task_run_record_run_by_name(
                name=schedule_logic.get_data_doc_schedule_name(doc_id), session=session
            )
            # Don't run datadoc if the most recent run is still in progress
            if runs and runs[0].status == TaskRunStatus.RUNNING:
                return

        data_doc = datadoc_logic.get_data_doc_by_id(doc_id, session=session)
        if not data_doc or data_doc.archived:
            return

        runner_id = user_id if user_id is not None else data_doc.owner_uid
        query_cells = (data_doc.get_query_cells())[start_index:]

        # Create db entry record only for scheduled run
        if execution_type == QueryExecutionType.SCHEDULED.value:
            record_id = create_task_run_record_for_celery_task(self, session=session)

        completion_params = {
            "doc_id": doc_id,
            "user_id": user_id,
            "record_id": record_id,
            "notifications": notifications,
            "exports": exports,
        }

        # Prepping chain jobs each unit is a [make_qe_task, run_query_task] combo
        for _, query_cell in enumerate(query_cells):
            # Skip disabled cells
            if query_cell.meta.get("disabled", False):
                continue

            engine_id = query_cell.meta["engine"]

            raw_query = query_cell.context

            # Skip empty cells
            if not raw_query or raw_query.isspace():
                continue

            try:
                query = render_templated_query(
                    raw_query,
                    data_doc.meta_variables,
                    engine_id,
                    user_id,
                    session=session,
                )

                # # Disable automatic limit for now
                # engine = admin_logic.get_query_engine_by_id(engine_id, session=session)
                # limit = query_cell.meta.get("limit", -1)

                # # If meta["limit"] is set and > 0, apply limit to the query
                # row_limit_enabled = engine.get_feature_params().get("row_limit", False)
                # if row_limit_enabled and limit >= 0:
                #     query = transform_to_limited_query(query, limit, engine.language)

            except Exception as e:
                on_datadoc_completion(
                    is_success=False,
                    error_msg=f"Error rendering template: {str(e)}",
                    **completion_params,
                )
                raise Exception(e)

            start_query_execution_kwargs = {
                "cell_id": query_cell.id,
                "query_execution_params": {
                    "query": query,
                    "engine_id": engine_id,
                    "uid": runner_id,
                },
                "data_doc_id": doc_id,
            }

            tasks_to_run.append(
                _run_datadoc_cell.si(
                    **start_query_execution_kwargs,
                    previous_query_result=(QueryExecutionStatus.DONE.value, 0),
                    execution_type=execution_type,
                    retry=retry,
                )
                if len(tasks_to_run) == 0
                else _run_datadoc_cell.s(
                    **start_query_execution_kwargs,
                    execution_type=execution_type,
                    retry=retry,
                )
            )

    chain(*tasks_to_run).apply_async(
        link=on_datadoc_run_success.s(
            completion_params=completion_params,
        ),
        link_error=on_datadoc_run_failure.s(completion_params=completion_params),
    )


@celery.task(bind=True, base=AbortableTask)
def _run_datadoc_cell(
    self,
    previous_query_result,
    cell_id,
    query_execution_params,
    data_doc_id,
    execution_type,
    retry,
):
    previous_query_status, previous_query_execution_id = previous_query_result
    if previous_query_status != QueryExecutionStatus.DONE.value:
        raise Exception(get_datadoc_error_message(previous_query_execution_id))

    with DBSession() as session:
        query_execution = qe_logic.create_query_execution(
            **query_execution_params, session=session
        )
        datadoc_logic.append_query_executions_to_data_cell(
            cell_id,
            [query_execution.id],
            session=session,
        )

        socketio.emit(
            "data_doc_query_execution",
            (
                None,
                query_execution.to_dict(),
                cell_id,
            ),
            namespace="/datadoc",
            room=data_doc_id,
        )

    # Run synchronously
    query_run_status, query_execution_id = run_query_task(
        query_execution_id=query_execution.id,
        execution_type=execution_type,
        celery_task=self,
    )
    if (
        retry["enabled"] is True
        and retry["max_retries"] != 0
        and query_run_status == QueryExecutionStatus.ERROR.value
        and not should_not_retry(get_datadoc_error_message(query_execution.id))
    ):

        self.retry(
            countdown=retry["delay_sec"],
            max_retries=retry["max_retries"],
            exc=Exception(
                f"MaxRetriesExceededError - {get_datadoc_error_message(query_execution.id)}"
            ),
        )

    return (query_run_status, query_execution_id)


@with_session
def get_datadoc_error_message(query_execution_id, session=None):
    _, data_cell_id = qe_logic.get_datadoc_id_from_query_execution_id(
        query_execution_id, session=session
    )[0]
    data_cell_name = datadoc_logic.get_data_cell_by_id(
        data_cell_id, session=session
    ).meta.get("title", f"Untitled Cell Id [{data_cell_id}]")
    query_execution_error = qe_logic.get_query_execution_error(
        query_execution_id, session=session
    )
    query_execution_error_message = (
        query_execution_error.error_message_extracted
        if query_execution_error.error_message_extracted
        else query_execution_error.error_message
    )
    error_msg = (
        f'Failure in "{data_cell_name}": {query_execution_error_message}'
        if query_execution_error_message is not None
        else GENERIC_QUERY_FAILURE_MSG
    )[:description_length]
    return error_msg


def should_not_retry(error_message):
    return any(re.search(pattern, error_message) for pattern in NON_RETRYABLE_ERRORS)


@celery.task
def on_datadoc_run_success(
    last_query_result,
    completion_params,
    **kwargs,
):
    last_query_status, last_query_execution_id = last_query_result

    is_success = last_query_status == QueryExecutionStatus.DONE.value
    error_msg = (
        None if is_success else get_datadoc_error_message(last_query_execution_id)
    )

    return on_datadoc_completion(
        is_success=is_success, error_msg=error_msg, **completion_params
    )


@celery.task
def on_datadoc_run_failure(
    request,
    exc,
    traceback,
    completion_params,
    **kwargs,
):

    error_msg = "DataDoc failed to run. Task {0!r} raised error: {1!r}".format(
        request.id, exc
    )
    return on_datadoc_completion(
        is_success=False, error_msg=error_msg, **completion_params
    )


def on_datadoc_completion(
    doc_id,
    user_id,
    record_id,
    # Export settings
    exports,
    notifications,
    # Success/Failure handling
    is_success,
    error_msg=None,
):
    try:
        export_urls = []
        if is_success:
            export_urls = export_datadoc(doc_id, user_id, exports)

        notifiy_on_datadoc_complete(
            doc_id,
            is_success,
            notifications,
            error_msg,
            export_urls,
        )

    except Exception as e:
        is_success = False
        error_msg = str(e)
        LOG.error(e, exc_info=True)
    finally:
        # when record_id is None, it's trigerred by adhoc datadoc run, no need to update the record.
        if record_id:
            update_task_run_record(
                id=record_id,
                status=TaskRunStatus.SUCCESS if is_success else TaskRunStatus.FAILURE,
                error_message=error_msg,
            )

    return is_success
