"""Normalize messages for indexing while minimizing stored personal data."""


def normalize_message(message: dict) -> dict:
    return {
        "message_id": str(message.get("id", "")),
        "thread_id": str(message.get("threadId", "")),
        "subject": str(message.get("subject", ""))[:500],
        "sender": str(message.get("sender", ""))[:500],
        "date": str(message.get("date", ""))[:100],
        "body": str(message.get("body", "")),
        "labels": list(message.get("labels", [])),
    }
