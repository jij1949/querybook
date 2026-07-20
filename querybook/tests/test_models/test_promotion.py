from const.promotion import PromotionStatus
from models.promotion import PromotionRequest, PromotionReviewer
from models.user import User
from models.environment import Environment
from models.datadoc import DataDoc
from app.db import DBSession


def test_create_promotion_request_defaults(db_engine):
    with DBSession() as session:
        corp = Environment.create(
            fields={"name": "promo-defaults-corp"}, session=session
        )
        dw = Environment.create(fields={"name": "promo-defaults-dw"}, session=session)
        requester = User.create(
            fields={"username": "promo-defaults-requester"}, session=session
        )
        source_doc = DataDoc.create(
            fields={"environment_id": corp.id, "title": "src"}, session=session
        )
        req = PromotionRequest.create(
            fields={
                "source_datadoc_id": source_doc.id,
                "source_environment_id": corp.id,
                "target_environment_id": dw.id,
                "requested_by": requester.id,
            },
            session=session,
        )
        assert req.id is not None
        assert req.status == PromotionStatus.PENDING_REVIEW
        assert req.target_datadoc_id is None
        assert req.github_pr_url is None
        assert req.to_dict()["status"] == PromotionStatus.PENDING_REVIEW.value


def test_assigned_reviewers_relationship(db_engine):
    with DBSession() as session:
        corp = Environment.create(
            fields={"name": "promo-reviewers-corp"}, session=session
        )
        dw = Environment.create(fields={"name": "promo-reviewers-dw"}, session=session)
        requester = User.create(
            fields={"username": "promo-reviewers-requester"}, session=session
        )
        source_doc = DataDoc.create(
            fields={"environment_id": corp.id, "title": "src"}, session=session
        )
        reviewer1 = User.create(
            fields={"username": "promo-reviewer-1"}, session=session
        )
        reviewer2 = User.create(
            fields={"username": "promo-reviewer-2"}, session=session
        )
        req = PromotionRequest.create(
            fields={
                "source_datadoc_id": source_doc.id,
                "source_environment_id": corp.id,
                "target_environment_id": dw.id,
                "requested_by": requester.id,
            },
            session=session,
        )
        PromotionReviewer.create(
            fields={"promotion_request_id": req.id, "uid": reviewer1.id},
            session=session,
        )
        PromotionReviewer.create(
            fields={"promotion_request_id": req.id, "uid": reviewer2.id},
            session=session,
        )
        refetched = PromotionRequest.get(id=req.id, session=session)
        expected = sorted([reviewer1.id, reviewer2.id])
        assert sorted(r.id for r in refetched.assigned_reviewers) == expected
        assert set(refetched.to_dict()["reviewer_ids"]) == set(expected)
