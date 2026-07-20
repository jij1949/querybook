from enum import Enum


class PromotionStatus(Enum):
    PENDING_REVIEW = 0
    APPROVED = 1
    MERGING = 2
    PUBLISHED = 3
    REJECTED = 4
    FAILED = 5
