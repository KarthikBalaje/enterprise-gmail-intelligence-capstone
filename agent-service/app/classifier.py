"""Synthetic candidates for local tests; replace with a reviewed Gmail ingestion flow."""


def synthetic_candidates() -> list[dict]:
    return [
        {
            "message_id": "demo-promo-001",
            "sender": "offers@example.test",
            "subject": "Weekly store offers",
            "category": "promotion",
            "is_sent": False,
            "is_draft": False,
            "is_work_related": False,
            "is_personally_protected": False,
            "classification_confident": True,
            "proposed_action": "trash",
        },
        {
            "message_id": "demo-work-001",
            "sender": "colleague@example.test",
            "subject": "Project delivery decisions",
            "category": "work",
            "is_sent": False,
            "is_draft": False,
            "is_work_related": True,
            "is_personally_protected": True,
            "classification_confident": True,
            "proposed_action": "trash",
        },
        {
            "message_id": "demo-sent-001",
            "sender": "me@example.test",
            "subject": "Sent: project update",
            "category": "sent",
            "is_sent": True,
            "is_draft": False,
            "is_work_related": False,
            "is_personally_protected": True,
            "classification_confident": True,
            "proposed_action": "trash",
        },
        {
            "message_id": "demo-unknown-001",
            "sender": "unknown@example.test",
            "subject": "Please review",
            "category": "uncertain",
            "is_sent": False,
            "is_draft": False,
            "is_work_related": False,
            "is_personally_protected": False,
            "classification_confident": False,
            "proposed_action": "trash",
        },
    ]
