
"""Safe cleanup workflow for synthetic or real Gmail metadata."""
from app.classifier import synthetic_candidates
from app.planner import make_plan
from app.reviewer import apply_review_policy


def build_cleanup_plan(
    request_id: str,
    user_request: str,
    max_candidates: int = 20,
    candidates: list[dict] | None = None,
) -> dict:
    is_gmail_data = candidates is not None

    if candidates is None:
        selected = synthetic_candidates()[:max_candidates]
        mode = "synthetic-dry-run"
        message = (
            "Synthetic examples only. No Gmail messages were read or changed."
        )
    else:
        selected = candidates[:max_candidates]
        mode = "gmail-metadata-dry-run"
        message = (
            "Gmail metadata supplied for review. "
            "No Gmail messages were modified."
        )

    proposed = make_plan(user_request, selected)
    reviewed = apply_review_policy(proposed)

    return {
        "request_id": request_id,
        "mode": mode,
        "user_request": user_request,
        "message": message,
        "source": "gmail_metadata" if is_gmail_data else "synthetic",
        "candidates": reviewed,
        "actions_executed": 0,
        "approval_required": True,
    }
