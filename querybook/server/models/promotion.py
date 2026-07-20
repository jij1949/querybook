import sqlalchemy as sql
from sqlalchemy.orm import backref, relationship

from app import db
from const.db import now, description_length, url_length
from const.promotion import PromotionStatus
from lib.sqlalchemy import CRUDMixin
from lib.utils.serialize import with_formatted_date

Base = db.Base


class PromotionRequest(Base, CRUDMixin):
    __tablename__ = "promotion_request"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = sql.Column(sql.Integer, primary_key=True, autoincrement=True)
    source_datadoc_id = sql.Column(
        sql.Integer, sql.ForeignKey("data_doc.id", ondelete="CASCADE"), nullable=False
    )
    target_datadoc_id = sql.Column(
        sql.Integer, sql.ForeignKey("data_doc.id", ondelete="SET NULL"), nullable=True
    )
    source_environment_id = sql.Column(
        sql.Integer,
        sql.ForeignKey("environment.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_environment_id = sql.Column(
        sql.Integer,
        sql.ForeignKey("environment.id", ondelete="CASCADE"),
        nullable=False,
    )
    status = sql.Column(
        sql.Enum(PromotionStatus),
        default=PromotionStatus.PENDING_REVIEW,
        nullable=False,
        index=True,
    )
    requested_by = sql.Column(
        sql.Integer, sql.ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_by = sql.Column(
        sql.Integer, sql.ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    review_comment = sql.Column(sql.String(length=description_length), nullable=True)
    github_pr_url = sql.Column(sql.String(length=url_length), nullable=True)
    created_at = sql.Column(sql.DateTime, default=now, nullable=False)
    updated_at = sql.Column(sql.DateTime, default=now, onupdate=now, nullable=False)

    assigned_reviewers = relationship(
        "User",
        secondary="promotion_reviewer",
        backref=backref(
            "assigned_promotion_requests", cascade="all", passive_deletes=True
        ),
    )

    @with_formatted_date
    def to_dict(self):
        return {
            "id": self.id,
            "source_datadoc_id": self.source_datadoc_id,
            "target_datadoc_id": self.target_datadoc_id,
            "source_environment_id": self.source_environment_id,
            "target_environment_id": self.target_environment_id,
            "status": self.status.value if self.status is not None else None,
            "requested_by": self.requested_by,
            "reviewed_by": self.reviewed_by,
            "review_comment": self.review_comment,
            "github_pr_url": self.github_pr_url,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "reviewer_ids": [r.id for r in self.assigned_reviewers],
        }


class PromotionReviewer(Base, CRUDMixin):
    __tablename__ = "promotion_reviewer"
    __table_args__ = (
        sql.UniqueConstraint(
            "promotion_request_id", "uid", name="unique_promotion_reviewer"
        ),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    id = sql.Column(sql.Integer, primary_key=True, autoincrement=True)
    promotion_request_id = sql.Column(
        sql.Integer,
        sql.ForeignKey("promotion_request.id", ondelete="CASCADE"),
        nullable=False,
    )
    uid = sql.Column(
        sql.Integer, sql.ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    created_at = sql.Column(sql.DateTime, default=now, nullable=False)

    @with_formatted_date
    def to_dict(self):
        return {
            "id": self.id,
            "promotion_request_id": self.promotion_request_id,
            "uid": self.uid,
            "created_at": self.created_at,
        }
