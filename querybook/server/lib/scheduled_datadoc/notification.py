from typing import Dict, List
import json

from app.db import DBSession, with_session
from const.schedule import NotifyOn
from env import QuerybookSettings
from lib.logger import get_logger
from lib.notify.utils import notify_recipients, notify_user
from logic.datadoc import get_data_doc_by_id
from models.user import User

LOG = get_logger(__file__)


def notifiy_on_datadoc_complete(
    doc_id: int,
    is_success: bool,
    notifications: List[Dict],
    error_msg: str,
    export_urls: List[str],
):
    for notification in notifications:
        notify_with = notification["with"]
        notify_on = notification["on"]
        notify_to_recipients = notification["config"].get("to", [])
        notify_to_users = notification["config"].get("to_user", [])

        if _should_notify(notify_with, notify_on, is_success):
            with DBSession() as session:
                notification_params = _get_datadoc_notification_params(
                    doc_id, is_success, error_msg, export_urls, session=session
                )

                # Log notification attempt
                log_data = {
                    "event": "scheduled_datadoc_notification",
                    "doc_id": doc_id,
                    "doc_title": notification_params.get("doc_title"),
                    "doc_url": notification_params.get("doc_url"),
                    "is_success": is_success,
                    "notification_type": notify_with,
                    "recipients": notify_to_recipients,
                    "users": notify_to_users
                }

                if not is_success and error_msg:
                    log_data["failure_reason"] = error_msg

                # notify recipients in config.to
                if notify_to_recipients:
                    try:
                        notify_recipients(
                            recipients=notify_to_recipients,
                            template_name="datadoc_completion_notification",
                            template_params=notification_params,
                            notifier_name=notify_with,
                        )
                        LOG.info(f"Scheduled DataDoc notification sent: {json.dumps(log_data)}")
                    except Exception as e:
                        LOG.error(f"Scheduled DataDoc notification failed: {json.dumps(log_data)}")

                # notify users(user_id) in config.to_user
                for user_id in notify_to_users:
                    try:
                        user = User.get(id=user_id, session=session)
                        notify_user(
                            user=user,
                            template_name="datadoc_completion_notification",
                            template_params=notification_params,
                            notifier_name=notify_with,
                            session=session,
                        )
                        LOG.info(f"Scheduled DataDoc notification sent: {json.dumps(log_data)}")
                    except Exception as e:
                        LOG.error(f"Scheduled DataDoc notification failed: {json.dumps(log_data)}")


def _should_notify(notify_with: str, notify_on: NotifyOn, is_success: bool):
    return bool(notify_with) and (
        notify_on == NotifyOn.ALL.value
        or (
            (notify_on == NotifyOn.ON_SUCCESS.value and is_success)
            or (notify_on == NotifyOn.ON_FAILURE.value and not is_success)
        )
    )


@with_session
def _get_datadoc_notification_params(
    doc_id: int, is_success: bool, error_msg: str, export_urls: List[str], session=None
):
    datadoc = get_data_doc_by_id(doc_id, session=session)
    doc_title = datadoc.title or "Untitled"
    env_name = datadoc.environment.name
    doc_url = f"{QuerybookSettings.PUBLIC_URL}/{env_name}/datadoc/{doc_id}/"

    return dict(
        is_success=is_success,
        doc_title=doc_title,
        doc_url=doc_url,
        doc_id=doc_id,
        export_urls=export_urls,
        error_msg=error_msg,
    )
