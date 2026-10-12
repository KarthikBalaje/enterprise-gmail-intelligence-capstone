
"""End-to-end safety tests for the cleanup planning workflow."""
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AGENT_APP = PROJECT_ROOT / "agent-service" / "app"

if str(AGENT_APP.parent) not in sys.path:
    sys.path.insert(0, str(AGENT_APP.parent))

if str(AGENT_APP) not in sys.path:
    sys.path.insert(0, str(AGENT_APP))

from graph import build_cleanup_plan


def test_cleanup_plan_is_dry_run_and_never_executes_actions():
    candidates = [
        {
            "message_id": "promo-001",
            "category": "promotion",
            "is_sent": False,
            "is_draft": False,
            "is_work_related": False,
            "is_personally_protected": False,
            "classification_confident": True,
        },
        {
            "message_id": "personal-001",
            "category": "promotion",
            "is_personally_protected": True,
            "classification_confident": True,
        },
    ]

    result = build_cleanup_plan(
        request_id="test-request-001",
        user_request="Review promotional emails",
        candidates=candidates,
    )

    assert result["mode"] == "gmail-metadata-dry-run"
    assert result["actions_executed"] == 0
    assert result["approval_required"] is True
    assert result["source"] == "gmail_metadata"
    assert len(result["candidates"]) == 2

    by_id = {
        item["message_id"]: item
        for item in result["candidates"]
    }

    assert by_id["promo-001"]["proposed_action"] == "keep"
    assert (
        by_id["promo-001"]["review_status"]
        == "eligible_for_human_review"
    )

    assert by_id["personal-001"]["proposed_action"] == "keep"
    assert by_id["personal-001"]["review_status"] == "skipped_protected"
