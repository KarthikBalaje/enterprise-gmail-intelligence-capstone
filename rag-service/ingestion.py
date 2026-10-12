
"""Normalize permitted email records and split them into RAG chunks."""

from typing import Any


def prepare_documents(
    messages: list[dict[str, Any]],
    *,
    chunk_size: int = 1200,
    overlap: int = 150,
) -> list[dict[str, Any]]:
    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("Require chunk_size > overlap >= 0")

    documents: list[dict[str, Any]] = []

    for message in messages:
        message_id = str(message.get("id") or message.get("message_id") or "").strip()
        if not message_id:
            raise ValueError("Every email must have a message ID")

        body = str(message.get("body") or "")[:100_000]
        subject = str(message.get("subject") or "")[:500]
        sender = str(message.get("sender") or "")[:500]
        date = str(message.get("date") or "")[:100]
        thread_id = str(message.get("threadId") or message.get("thread_id") or "")
        labels = [str(label)[:100] for label in message.get("labels", [])[:50]]

        # Do not index metadata-only messages as if they contained email text.
        content = f"Subject: {subject}\nFrom: {sender}\nDate: {date}\n\n{body}"
        if not body.strip():
            continue

        start = 0
        chunk_index = 0

        while start < len(content):
            chunk = content[start : start + chunk_size]
            if chunk.strip():
                documents.append({
                    "message_id": message_id,
                    "thread_id": thread_id[:500],
                    "subject": subject,
                    "sender": sender,
                    "date": date,
                    "labels": labels,
                    "chunk_index": chunk_index,
                    "text": chunk,
                })

            if start + chunk_size >= len(content):
                break

            start += chunk_size - overlap
            chunk_index += 1

    return documents
