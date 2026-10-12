import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AGENT_SERVICE = PROJECT_ROOT / "agent-service"

if str(AGENT_SERVICE) not in sys.path:
    sys.path.insert(0, str(AGENT_SERVICE))

from app.planner import make_plan
from app.reviewer import apply_review_policy
from app.classifier import synthetic_candidates


def test_planner_never_proposes_trash_or_archive():
    candidates = synthetic_candidates()
    planned = make_plan("Review promotions", candidates)

    assert len(planned) == len(candidates)
    assert all(
        item["proposed_action"] not in {"trash", "archive"}
        for item in planned
    )


def test_protected_messages_are_kept():
    planned = make_plan("Review promotions", synthetic_candidates())
    reviewed = apply_review_policy(planned)

    protected_ids = {
        "demo-work-001",
        "demo-sent-001",
    }

    for item in reviewed:
        if item["message_id"] in protected_ids:
            assert item["proposed_action"] == "keep"
            assert item["review_status"] == "skipped_protected"


def test_uncertain_message_requires_manual_review():
    planned = make_plan("Review promotions", synthetic_candidates())
    reviewed = apply_review_policy(planned)

    unknown = next(
        item for item in reviewed
        if item["message_id"] == "demo-unknown-001"
    )

    assert unknown["proposed_action"] == "keep"
    assert unknown["review_status"] == "manual_review_required"


def test_promotion_is_review_candidate_not_deletion():
    planned = make_plan("Review promotions", synthetic_candidates())
    reviewed = apply_review_policy(planned)

    promotion = next(
        item for item in reviewed
        if item["message_id"] == "demo-promo-001"
    )

    assert promotion["proposed_action"] == "keep"
    assert promotion["review_status"] == "eligible_for_human_review"


def test_reviewer_fails_closed_for_unknown_action():
    candidate = {
        "message_id": "unexpected-action-1",
        "category": "promotion",
        "is_sent": False,
        "is_draft": False,
        "is_work_related": False,
        "is_personally_protected": False,
        "classification_confident": True,
        "proposed_action": "permanently_delete",
    }

    reviewed = apply_review_policy([candidate])

    assert reviewed[0]["proposed_action"] == "keep"
