"""Verify the gateway's single-request cleanup-plus-RAG orchestration."""

import asyncio
import importlib.util
from pathlib import Path
from unittest.mock import Mock


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = ROOT / "api-gateway" / "app" / "assist_workflow.py"
SPEC = importlib.util.spec_from_file_location("gateway_assist_workflow", WORKFLOW_PATH)
assert SPEC and SPEC.loader
workflow = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(workflow)


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeAsyncClient:
    def __init__(self, calls, **kwargs):
        self.calls = calls
        self.kwargs = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def post(self, url, json):
        self.calls.append((url, json))
        if url.endswith("/plan"):
            return FakeResponse({"actions_executed": 0, "candidates": []})
        return FakeResponse({"grounded": False, "sources": []})


def test_single_assist_request_runs_plan_then_rag(monkeypatch):
    calls = []
    clients = []

    def client_factory(**kwargs):
        client = FakeAsyncClient(calls, **kwargs)
        clients.append(client)
        return client

    monkeypatch.setattr(workflow.httpx, "AsyncClient", client_factory)

    result = asyncio.run(
        workflow.run_assisted_plan(
            agent_service_url="http://agent-service:8001/",
            request_id="synthetic-flow-001",
            request="Review synthetic newsletters",
            question="Summarize the synthetic newsletter context",
            max_candidates=7,
        )
    )

    assert [url for url, _ in calls] == [
        "http://agent-service:8001/plan",
        "http://agent-service:8001/rag/ask",
    ]
    assert calls[0][1] == {
        "request_id": "synthetic-flow-001",
        "request": "Review synthetic newsletters",
        "max_candidates": 7,
    }
    assert calls[1][1] == {
        "question": "Summarize the synthetic newsletter context",
        "limit": 5,
    }
    assert clients[0].kwargs["timeout"] == 210.0
    assert result["request_id"] == "synthetic-flow-001"
    assert result["cleanup_plan"]["actions_executed"] == 0
    assert result["related_context"]["grounded"] is False


def test_real_gmail_metadata_is_forwarded_without_body(monkeypatch):
    calls = []

    def client_factory(**kwargs):
        return FakeAsyncClient(calls, **kwargs)

    monkeypatch.setattr(workflow.httpx, "AsyncClient", client_factory)
    candidates = [{
        "message_id": "gmail-id-redacted",
        "subject": "metadata only",
        "category": "uncertain",
        "classification_confident": False,
        "proposed_action": "keep",
    }]

    result = asyncio.run(
        workflow.run_assisted_plan(
            agent_service_url="http://agent-service:8001",
            request_id="readonly-gmail-flow",
            request="Review inbox messages conservatively",
            question="Summarize the indexed message",
            max_candidates=1,
            candidates=candidates,
        )
    )

    forwarded = calls[0][1]["candidates"]
    assert forwarded == candidates
    assert all("body" not in item for item in forwarded)
    assert result["cleanup_plan"]["actions_executed"] == 0
