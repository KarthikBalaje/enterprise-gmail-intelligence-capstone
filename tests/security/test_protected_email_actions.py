
"""Security tests for protected messages in bulk cleanup requests."""
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GUARDRAILS_DIR = PROJECT_ROOT / "guardrails"

if str(GUARDRAILS_DIR) not in sys.path:
    sys.path.insert(0, str(GUARDRAILS_DIR))

from policy_engine import Action, MessageFacts, authorize_action


def test_bulk_request_cannot_override_protected_message_policy():
    # A bulk request includes both an ordinary promotion and a protected email.
    messages = [
        MessageFacts(
            message_id="promo-001",
            classification_confident=True,
        ),
        MessageFacts(
            message_id="personal-001",
            is_personally_protected=True,
            classification_confident=True,
        ),
    ]

    # Even explicit approval must not override the protected-message rule.
    results = [
        authorize_action(
            message,
            Action.TRASH,
            user_approved=True,
        )
        for message in messages
    ]

    promo_allowed, _ = results[0]
    protected_allowed, protected_reason = results[1]

    assert promo_allowed is True
    assert protected_allowed is False
    assert "Personally protected" in protected_reason
