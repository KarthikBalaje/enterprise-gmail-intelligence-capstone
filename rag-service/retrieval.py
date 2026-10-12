
"""Ollama embeddings and Weaviate vector indexing/retrieval."""

import os
import uuid
from typing import Any

import httpx

from .ingestion import prepare_documents

WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8081").rstrip("/")
OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL", "http://localhost:11434"
).rstrip("/")
EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
COLLECTION = "EmailChunk"
TIMEOUT = 30.0


def _embed(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    with httpx.Client(timeout=TIMEOUT) as client:
        response = client.post(
            f"{OLLAMA_BASE_URL}/api/embed",
            json={"model": EMBEDDING_MODEL, "input": texts},
        )
        response.raise_for_status()
        vectors = response.json().get("embeddings", [])

    if len(vectors) != len(texts) or any(not vector for vector in vectors):
        raise RuntimeError("Embedding service returned invalid vectors")

    return vectors


def _ensure_schema(client: httpx.Client) -> None:
    response = client.get(f"{WEAVIATE_URL}/v1/schema")
    response.raise_for_status()

    classes = response.json().get("classes", [])
    if any(item.get("class") == COLLECTION for item in classes):
        return

    schema = {
        "class": COLLECTION,
        "vectorizer": "none",
        "properties": [
            {"name": "messageId", "dataType": ["text"]},
            {"name": "threadId", "dataType": ["text"]},
            {"name": "subject", "dataType": ["text"]},
            {"name": "sender", "dataType": ["text"]},
            {"name": "date", "dataType": ["text"]},
            {"name": "chunkIndex", "dataType": ["int"]},
            {"name": "text", "dataType": ["text"]},
            {"name": "labels", "dataType": ["text[]"]},
        ],
    }
    response = client.post(f"{WEAVIATE_URL}/v1/schema", json=schema)
    response.raise_for_status()


def index_email_messages(messages: list[dict[str, Any]]) -> int:
    """Index explicitly supplied email records. Returns the number of chunks."""
    documents = prepare_documents(messages)
    if not documents:
        return 0

    vectors = _embed([doc["text"] for doc in documents])

    with httpx.Client(timeout=TIMEOUT) as client:
        _ensure_schema(client)

        for doc, vector in zip(documents, vectors, strict=True):
            # Stable ID makes re-indexing the same message chunk idempotent.
            object_id = str(uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"gmail-rag:{doc['message_id']}:{doc['chunk_index']}",
            ))
            payload = {
                "class": COLLECTION,
                "id": object_id,
                "properties": {
                    "messageId": doc["message_id"],
                    "threadId": doc["thread_id"],
                    "subject": doc["subject"],
                    "sender": doc["sender"],
                    "date": doc["date"],
                    "chunkIndex": doc["chunk_index"],
                    "text": doc["text"],
                    "labels": doc["labels"],
                },
                "vector": vector,
            }
            object_url = f"{WEAVIATE_URL}/v1/objects/{COLLECTION}/{object_id}"

            existing = client.get(object_url)

            if existing.status_code == 404:
                response = client.post(
                    f"{WEAVIATE_URL}/v1/objects",
                    json=payload,
                )
                response.raise_for_status()
            elif existing.is_success:
                response = client.patch(
                    object_url,
                    json={"properties": payload["properties"], "vector": vector},
                )
                response.raise_for_status()
            else:
                existing.raise_for_status()
            response.raise_for_status()

    return len(documents)


def retrieve_email_context(question: str, limit: int = 5) -> list[dict]:
    if not question or not question.strip():
        raise ValueError("Question must not be empty")
    if not 1 <= limit <= 20:
        raise ValueError("limit must be between 1 and 20")

    vector = _embed([question.strip()])[0]

    # The vector is generated locally by the configured embedding model.
    import json

    query = f"""
    {{
      Get {{
        {COLLECTION}(
          nearVector: {{vector: {json.dumps(vector)}}},
          limit: {limit}
        ) {{
          messageId threadId subject sender date chunkIndex text
          _additional {{ distance }}
        }}
      }}
    }}
    """

    with httpx.Client(timeout=TIMEOUT) as client:
        response = client.post(
            f"{WEAVIATE_URL}/v1/graphql",
            json={"query": query},
        )
        response.raise_for_status()
        result = response.json()

    if result.get("errors"):
        raise RuntimeError("Weaviate retrieval query failed")

    rows = result.get("data", {}).get("Get", {}).get(COLLECTION, [])
    return [
        {
            "message_id": row["messageId"],
            "thread_id": row.get("threadId", ""),
            "subject": row.get("subject", ""),
            "sender": row.get("sender", ""),
            "date": row.get("date", ""),
            "chunk_index": row.get("chunkIndex", 0),
            "text": row.get("text", ""),
            "distance": row.get("_additional", {}).get("distance"),
        }
        for row in rows
    ]
