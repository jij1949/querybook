from enum import Enum


class TaskRunStatus(Enum):
    RUNNING = 0
    SUCCESS = 1
    FAILURE = 2


class NotifyOn(Enum):
    ALL = 0
    ON_FAILURE = 1
    ON_SUCCESS = 2


class ScheduleTaskType(Enum):
    PROD = "prod"
    USER = "user"

DATADOC_SCHEDULE_PREFIX = "run_data_doc_"

UserTaskNames = set(["tasks.run_datadoc.run_datadoc"])
