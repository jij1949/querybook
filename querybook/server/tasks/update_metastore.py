from celery import chain as celery_chain

from app.flask_app import celery
from const.schedule import TaskRunStatus
from lib.logger import get_logger
from logic.schedule import (
    create_task_run_record_for_celery_task,
    update_task_run_record,
)

LOG = get_logger(__file__)


@celery.task(bind=True)
def update_metastore(self, id, *args, **kwargs):
    """Dispatcher.

    Non-combo loaders: inline task-logging identical to the old
    ``@with_task_logging()`` wrapper.

    Combo loaders: creates the combo-level TaskRunRecord in RUNNING state
    immediately so it appears in Run History, then builds a sequential Celery
    chain.  The record_id is passed to the terminal callback which updates it
    to SUCCESS or FAILURE once the chain completes.
    """
    from lib.metastore import get_metastore_loader, load_metastore

    loader = get_metastore_loader(id)
    units = loader.get_sync_units()

    if len(units) == 1:
        record_id = create_task_run_record_for_celery_task(self)
        try:
            load_metastore(id)
            update_task_run_record(id=record_id, status=TaskRunStatus.SUCCESS)
        except Exception as e:
            update_task_run_record(
                id=record_id, error_message=str(e), status=TaskRunStatus.FAILURE
            )
            raise
    else:
        shadow = self.request.get("shadow", f"update_metastore_{id}")

        # task_run_record.name has a FK to task_schedule.name.  Create per-child
        # anchor rows (enabled=False, no cron trigger) so child task records
        # can be inserted without violating the constraint.
        from sqlalchemy.exc import IntegrityError

        from logic.schedule import create_task_schedule, get_task_schedule_by_name

        for unit_id in units:
            child_name = f"update_metastore_{id}_child_{unit_id}"
            if not get_task_schedule_by_name(child_name):
                try:
                    create_task_schedule(
                        name=child_name,
                        task="tasks.update_metastore.update_metastore_child",
                        # Dummy cron — schedule is disabled (enabled=False) so Beat
                        # never fires it.  A non-NULL value prevents AttributeError in
                        # any code that calls TaskSchedule.get_cron() unconditionally.
                        cron="0 0 * * *",
                        enabled=False,
                        kwargs={"combo_id": id, "child_id": unit_id},
                        commit=True,
                    )
                except IntegrityError:
                    # Another concurrent dispatcher created the same anchor row —
                    # the row now exists, which is all we need. Proceed normally.
                    pass

        # Create the combo-level record in RUNNING state now so it is visible
        # in Run History immediately.  Finalize will update it when done.
        record_id = create_task_run_record_for_celery_task(self)

        child_sigs = [
            update_metastore_child.si(
                combo_id=id, child_id=unit_id, parent_record_id=record_id
            ).set(shadow=f"update_metastore_{id}_child_{unit_id}")
            for unit_id in units
        ]
        finalize_sig = finalize_combo_metastore.si(
            combo_id=id, unit_ids=list(units), record_id=record_id
        ).set(shadow=shadow)
        try:
            celery_chain(*child_sigs, finalize_sig).delay()
            LOG.info(f"[update_metastore] combo chain enqueued for metastore_id={id}")
        except Exception as e:
            LOG.error(
                f"[update_metastore] failed to enqueue combo chain for metastore_id={id}: {e}"
            )
            update_task_run_record(
                id=record_id, error_message=str(e), status=TaskRunStatus.FAILURE
            )
            raise


@celery.task(bind=True)
def update_metastore_child(
    self, combo_id, child_id, parent_record_id=None, *args, **kwargs
):
    """Run one child sync.  All logic lives in ComboMetastoreLoader.run_child_sync."""
    from lib.metastore import get_metastore_loader

    loader = get_metastore_loader(combo_id)
    loader.run_child_sync(self, child_id, parent_record_id=parent_record_id)


@celery.task(bind=True)
def finalize_combo_metastore(self, combo_id, unit_ids, record_id, *args, **kwargs):
    """Terminal callback for combo chains.  Updates the existing combo TaskRunRecord
    (created by the dispatcher) to SUCCESS or FAILURE."""
    from lib.metastore import get_metastore_loader

    loader = get_metastore_loader(combo_id)
    loader.run_finalize_sync(unit_ids, record_id=record_id)
