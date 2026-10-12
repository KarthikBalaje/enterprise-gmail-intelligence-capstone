
"""Deterministic tests for email RAG ingestion and cited answers."""

import importlib.util
from pathlib import Path
from unittest.mock import Mock

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


ingestion = load_module(
    "rag_ingestion_test",
    ROOT / "rag-service" / "ingestion.py",
)
answer_module = load_module(
    "rag_answer_test",
    ROOT / "rag-service" / "answer.py",
)


def test_email_is_normalized_into_a_citable_chunk():
    documents = ingestion.prepare_documents([
        {
            "id": "email-test-001",
            "threadId": "thread-test-001",
            "subject": "Project review",
            "sender": "alex@example.test",
            "date": "2026-10-12",
            "labels": ["INBOX"],
            "body": "The project review is Friday at 10 AM.",
        }
    ])

    assert len(documents) == 1
    assert documents[0]["message_id"] == "email-test-001"
    assert documents[0]["subject"] == "Project review"
    assert "Friday at 10 AM" in documents[0]["text"]


def test_metadata_only_email_is_not_indexed():
    documents = ingestion.prepare_documents([
        {
            "id": "email-test-002",
            "subject": "Metadata only",
            "body": "",
        }
    ])

    assert documents == []


def test_answer_returns_only_valid_source_citations(monkeypatch):
    fake_response = Mock()
    fake_response.raise_for_status.return_value = None
    fake_response.json.return_value = {
        "message": {
            "content": "The project review is Friday at 10 AM [S1]."
        }
    }

    fake_client = Mock()
    fake_client.__enter__ = Mock(return_value=fake_client)
    fake_client.__exit__ = Mock(return_value=False)
    fake_client.post.return_value = fake_response

    monkeypatch.setattr(answer_module.httpx, "Client", Mock(return_value=fake_client))

    result = answer_module.build_answer(
        "When is the project review?",
        [
            {
                "message_id": "email-test-001",
                "subject": "Project review",
                "date": "2026-10-12",
                "chunk_index": 0,
                "text": "The project review is Friday at 10 AM.",
            }
        ],
    )

    assert result["grounded"] is True
    assert result["sources"] == [
        {
            "source_id": "S1",
            "message_id": "email-test-001",
            "subject": "Project review",
            "date": "2026-10-12",
            "chunk_index": 0,
        }
    ]


def test_answer_without_retrieved_evidence_is_not_grounded():
    result = answer_module.build_answer(
        "When is the project review?",
        [],
    )

    assert result["grounded"] is False
    assert result["sources"] == []
