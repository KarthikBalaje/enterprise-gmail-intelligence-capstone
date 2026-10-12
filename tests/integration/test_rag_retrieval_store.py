"""Deterministic tests for Weaviate/Ollama retrieval boundaries."""

import importlib.util
import sys
import types
from pathlib import Path
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[2]


def load_rag_modules():
    package = types.ModuleType("rag_service")
    package.__path__ = [str(ROOT / "rag-service")]
    sys.modules["rag_service"] = package

    ingestion_spec = importlib.util.spec_from_file_location(
        "rag_service.ingestion",
        ROOT / "rag-service" / "ingestion.py",
    )
    ingestion = importlib.util.module_from_spec(ingestion_spec)
    assert ingestion_spec and ingestion_spec.loader
    sys.modules["rag_service.ingestion"] = ingestion
    ingestion_spec.loader.exec_module(ingestion)

    retrieval_spec = importlib.util.spec_from_file_location(
        "rag_service.retrieval",
        ROOT / "rag-service" / "retrieval.py",
    )
    retrieval = importlib.util.module_from_spec(retrieval_spec)
    assert retrieval_spec and retrieval_spec.loader
    sys.modules["rag_service.retrieval"] = retrieval
    retrieval_spec.loader.exec_module(retrieval)
    return retrieval


retrieval = load_rag_modules()


def test_index_email_messages_creates_schema_and_object(monkeypatch):
    calls = []

    def response(payload=None, status_code=200):
        item = Mock()
        item.status_code = status_code
        item.is_success = 200 <= status_code < 300
        item.json.return_value = payload or {}
        item.raise_for_status.return_value = None
        return item

    fake_client = Mock()
    fake_client.__enter__ = Mock(return_value=fake_client)
    fake_client.__exit__ = Mock(return_value=False)

    def post(url, json):
        calls.append(("post", url, json))
        if url.endswith("/api/embed"):
            return response({"embeddings": [[0.1, 0.2, 0.3]]})
        return response()

    def get(url):
        calls.append(("get", url, None))
        if url.endswith("/v1/schema"):
            return response({"classes": []})
        return response(status_code=404)

    fake_client.post.side_effect = post
    fake_client.get.side_effect = get
    monkeypatch.setattr(retrieval.httpx, "Client", Mock(return_value=fake_client))

    chunks = retrieval.index_email_messages([
        {
            "id": "email-001",
            "subject": "Board review",
            "sender": "alex@example.test",
            "date": "2026-10-12",
            "labels": ["INBOX"],
            "body": "The board review is at 10 AM.",
        }
    ])

    assert chunks == 1
    assert any(call[1].endswith("/v1/schema") for call in calls)
    assert any(
        call[0] == "post"
        and call[1].endswith("/v1/objects")
        and call[2]["properties"]["messageId"] == "email-001"
        for call in calls
    )


def test_retrieve_email_context_returns_citable_rows(monkeypatch):
    def response(payload):
        item = Mock()
        item.json.return_value = payload
        item.raise_for_status.return_value = None
        return item

    fake_client = Mock()
    fake_client.__enter__ = Mock(return_value=fake_client)
    fake_client.__exit__ = Mock(return_value=False)

    def post(url, json):
        if url.endswith("/api/embed"):
            return response({"embeddings": [[0.3, 0.2, 0.1]]})
        return response({
            "data": {
                "Get": {
                    "EmailChunk": [
                        {
                            "messageId": "email-001",
                            "threadId": "thread-001",
                            "subject": "Board review",
                            "sender": "alex@example.test",
                            "date": "2026-10-12",
                            "chunkIndex": 0,
                            "text": "The board review is at 10 AM.",
                            "_additional": {"distance": 0.12},
                        }
                    ]
                }
            }
        })

    fake_client.post.side_effect = post
    monkeypatch.setattr(retrieval.httpx, "Client", Mock(return_value=fake_client))

    rows = retrieval.retrieve_email_context("When is the board review?", limit=1)

    assert rows == [
        {
            "message_id": "email-001",
            "thread_id": "thread-001",
            "subject": "Board review",
            "sender": "alex@example.test",
            "date": "2026-10-12",
            "chunk_index": 0,
            "text": "The board review is at 10 AM.",
            "distance": 0.12,
        }
    ]
