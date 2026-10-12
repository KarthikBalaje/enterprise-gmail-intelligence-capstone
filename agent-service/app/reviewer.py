"""Policy review boundary. Fails closed for protected or uncertain candidates."""
from pathlib import Path
import sys

# The guardrails directory is copied into the agent image by the build context
# in the recommended Compose configuration.
_GUARDRAILS_DIR = Path(__file__).resolve().parents[1] / "guardrails"
if str(_GUARDRAILS_DIR) not in sys.path:
    sys.path.insert(0, str(_GUARDRAILS_DIR))

from policy_engine import Action, MessageFacts, authorize_action  # noqa: E402


def apply_review_policy(candidates: list[dict]) -> list[dict]:
    reviewed = []

    for candidate in candidates:
        facts = MessageFacts(
            message_id=candidate["message_id"],
            is_sent=candidate.get("is_sent", False),
            is_draft=candidate.get("is_draft", False),
            is_work_related=candidate.get("is_work_related", False),
            is_personally_protected=candidate.get("is_personally_protected", False),
            classification_confident=candidate.get("classification_confident", False),
        )

        # Planning is never authorization to perform a write action.
        proposed = candidate.get("proposed_action", "keep")
        try:
            action = Action(proposed)
        except ValueError:
            action = Action.KEEP

        allowed, reason = authorize_action(
            facts, action, user_approved=False
        )

        protected = any((
            facts.is_sent,
            facts.is_draft,
            facts.is_work_related,
            facts.is_personally_protected,
        ))

        if protected:
            status = "skipped_protected"
        elif not facts.classification_confident:
            status = "manual_review_required"
        elif candidate.get("category") == "promotion":
            status = "eligible_for_human_review"
        else:
            status = candidate.get("review_status", "manual_review_required")

        reviewed.append({
            **candidate,
            "proposed_action": action.value,
            "policy_allowed_without_approval": allowed,
            "policy_reason": reason,
            "review_status": status,
            "final_status": status,
        })

    return reviewed

