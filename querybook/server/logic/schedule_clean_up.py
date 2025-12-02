from app.db import with_session
from lib.logger import get_logger
from models.datadoc import DataDoc
from models.schedule import TaskSchedule
from const.schedule import DATADOC_SCHEDULE_PREFIX

LOG = get_logger(__file__)

@with_session
def clean_up_schedules_in_environment(user_id: int, environment_id: int, session=None):
    datadocs = (
        session.query(DataDoc)
        .filter(
            DataDoc.owner_uid == user_id,
            DataDoc.environment_id == environment_id
        )
        .all()
    )

    deleted_count = 0

    for datadoc in datadocs:
        schedule_name = f"{DATADOC_SCHEDULE_PREFIX}{datadoc.id}"
        schedule = session.query(TaskSchedule).filter(TaskSchedule.name == schedule_name).first()

        
        if schedule:
            LOG.info(
                f"Deleting schedule {schedule_name} (ID: {schedule.id}) for datadoc {datadoc.id} "
                f"(user {user_id}, environment {environment_id})"
            )
            try:
                session.delete(schedule)
                deleted_count += 1
            except Exception as e:
                LOG.error(
                    f"Failed to delete schedule {schedule_name} (ID: {schedule.id}): {str(e)}"
                )

    # Commit all deletions at once
    if deleted_count > 0:
        session.commit()
        LOG.info(
            f"Successfully deleted {deleted_count} schedule(s) for user {user_id} "
            f"in environment {environment_id}"
        )
    else:
        LOG.info(
            f"No schedules found for user {user_id} in environment {environment_id}"
        )

    return deleted_count
