"""Placeholder for authorized Gmail ingestion and Weaviate indexing."""


def prepare_documents(messages: list[dict]) -> list[dict]:
    normalized = []
    for message in messages:
        normalized.append({
            "message_id": str(message.get("id", "")),
            "thread_id": str(message.get("threadId", "")),
            "subject": str(message.get("subject", ""))[:500],
            "sender": str(message.get("sender", ""))[:500],
            "date": str(message.get("date", ""))[:100],
            "body": str(message.get("body", "")),
            "labels": list(message.get("labels", [])),
        })
    return normalized
