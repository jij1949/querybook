from const.promotion import PromotionStatus


def test_promotion_status_members_and_values():
    assert PromotionStatus.PENDING_REVIEW.value == 0
    assert PromotionStatus.APPROVED.value == 1
    assert PromotionStatus.MERGING.value == 2
    assert PromotionStatus.PUBLISHED.value == 3
    assert PromotionStatus.REJECTED.value == 4
    assert PromotionStatus.FAILED.value == 5
    assert {s.name for s in PromotionStatus} == {
        "PENDING_REVIEW", "APPROVED", "MERGING", "PUBLISHED", "REJECTED", "FAILED",
    }
