from sqlalchemy import and_, or_, func

from app.db import with_session
from app.flask_app import celery
from lib.logger import get_logger
from logic.schedule import (
    DATADOC_SCHEDULE_PREFIX,
    delete_task_schedule,
    with_task_logging,
)
from models.datadoc import DataDoc
from models.environment import Environment, UserEnvironment
from models.schedule import TaskSchedule
from models.user import User

logger = get_logger(__name__)


@with_session
def get_orphaned_scheduled_datadocs(session=None, dryrun=False):
    # Query to find all scheduled datadocs where owner no longer has access
    orphaned_schedules = (
        session.query(
            DataDoc.id.label("doc_id"),
            DataDoc.title.label("doc_title"),
            TaskSchedule.id.label("task_id"),
            User.deleted.label("user_deleted"),
            Environment.deleted_at.label("env_deleted_at"),
            Environment.public.label("env_public"),
        )
        .join(User, DataDoc.owner_uid == User.id)
        .join(Environment, DataDoc.environment_id == Environment.id)
        .join(
            TaskSchedule,
            TaskSchedule.name == func.concat(DATADOC_SCHEDULE_PREFIX, DataDoc.id),
        )
        .outerjoin(
            UserEnvironment,
            and_(
                User.id == UserEnvironment.user_id,
                Environment.id == UserEnvironment.environment_id,
            ),
        )
        .filter(
            or_(
                User.deleted == True,  # Owner is deleted
                Environment.deleted_at.isnot(None),  # Environment is deleted
                and_(
                    Environment.public == False,  # Environment is private
                    UserEnvironment.user_id.is_(None),  # No user_environment entry
                ),
            )
        )
        .all()
    )
    
    orphaned_list = []
    for schedule in orphaned_schedules:   
        orphaned_list.append({
            "doc_id": schedule.doc_id,
            "doc_title": schedule.doc_title,
            "task_id": schedule.task_id,
        })
    
    return orphaned_list


@with_session
def remove_orphaned_schedules(session=None, dryrun=False):
    orphaned_schedules = get_orphaned_scheduled_datadocs(session=session, dryrun=dryrun)
    
    if dryrun:
        if len(orphaned_schedules) == 0:
            logger.info("No orphaned schedules found.")
        else:
            logger.info(
                f"Found {len(orphaned_schedules)} orphaned schedules: {orphaned_schedules}"
            )
        return

    if not orphaned_schedules:
        return []
        
    # Remove each orphaned schedule
    removed_schedules = []
    for schedule_info in orphaned_schedules:
        try:
            delete_task_schedule(
                schedule_info["task_id"], commit=False, session=session
            )
            removed_schedules.append(schedule_info)
        except Exception as e:
            logger.error(
                f"Failed to remove schedule for DataDoc ID: {schedule_info['doc_id']} "
                f"(Task ID: {schedule_info['task_id']}): {str(e)}"
            )
    
    # Commit all deletions at once
    if removed_schedules:
        session.commit()
    
    return removed_schedules


@celery.task(bind=True)
@with_task_logging()
def cleanup_orphaned_schedules(self, dryrun=False):
    removed_schedules = remove_orphaned_schedules(dryrun=dryrun)
    
    if not removed_schedules or len(removed_schedules) == 0:
        logger.info("No orphaned schedules were removed.")
    else:
        logger.info(
            f"{len(removed_schedules)} orphaned schedules were removed: {removed_schedules}"
        )
