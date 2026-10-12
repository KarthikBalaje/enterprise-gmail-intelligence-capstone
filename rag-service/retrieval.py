"""Retrieval boundary. Implement Weaviate hybrid search and access filters here."""


def retrieve_email_context(question: str, limit: int = 5) -> list[dict]:
    if not question.strip():
        raise ValueError("Question must not be empty")
    # Safe placeholder: do not pretend to retrieve real email content.
    return []
