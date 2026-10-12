"""Grounded answer boundary."""


def build_answer(question: str, retrieved_messages: list[dict]) -> dict:
    if not retrieved_messages:
        return {
            "answer": "I could not find sufficient indexed email evidence to answer this question.",
            "sources": [],
            "grounded": False,
        }
    # TODO: call the configured model with retrieved context and require citations.
    return {
        "answer": "Answer generation is not implemented yet.",
        "sources": [
            {
                "message_id": item.get("message_id"),
                "subject": item.get("subject"),
                "date": item.get("date"),
            }
            for item in retrieved_messages
        ],
        "grounded": False,
    }
