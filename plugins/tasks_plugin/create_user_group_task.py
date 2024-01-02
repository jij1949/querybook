from const.user import UserGroup
from logic.user import create_or_update_user_group
from app.flask_app import celery
from logic.schedule import with_task_logging


@celery.task(bind=True)
@with_task_logging()
def create_user_group_task(self):
    name = "group1"
    display_name = "GROUP1"
    email = "jvalvo@expediagroup.com"
    description = "this is a group"
    members = []
    create_or_update_user_group(UserGroup(name=name, display_name=display_name, email=email, description=description,
                                          members=members))
