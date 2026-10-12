import os
import uuid
from typing import Any

import httpx
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

AGENT_SERVICE_URL = os.getenv("AGENT_SERVICE_URL", "http://localhost:8001").rstrip("/")
APP_ENV = os.getenv("APP_ENV", "development")

app = FastAPI(
    title="Enterprise Gmail Intelligence API",
    version="0.1.0",
    description="Capstone API scaffold. Gmail write actions are deliberately not implemented.",
)


from app.telemetry import configure_tracing
configure_tracing(app, "api-gateway", instrument_httpx=True)

class CleanupRequest(BaseModel):
    request: str = Field(min_length=3, max_length=2000)
    max_candidates: int = Field(default=20, ge=1, le=100)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "api-gateway",
        "status": "ok",
        "mode": "scaffold",
        "warning": "This version uses synthetic email candidates and does not modify Gmail.",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "api-gateway"}


@app.post("/cleanup/plan")
async def create_cleanup_plan(
    body: CleanupRequest,
    x_request_id: str | None = Header(default=None),
) -> dict[str, Any]:
    request_id = x_request_id or str(uuid.uuid4())
    payload = {
        "request_id": request_id,
        "request": body.request,
        "max_candidates": body.max_candidates,
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(f"{AGENT_SERVICE_URL}/plan", json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Agent service unavailable or returned an error: {type(exc).__name__}",
        ) from exc


@app.get("/ready")
async def ready() -> dict[str, str]:
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{AGENT_SERVICE_URL}/health")
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail="Agent service is not ready") from exc
    return {"status": "ready"}




from app.gmail_oauth import (
    router as gmail_oauth_router,
    gmail_messages,
)

app.include_router(gmail_oauth_router)


@app.post("/cleanup/plan/gmail")
def create_gmail_cleanup_plan(
    body: CleanupRequest,
    x_request_id: str | None = Header(default=None),
) -> dict[str, Any]:
    """Create a read-only dry-run plan from Inbox metadata."""

    request_id = x_request_id or str(uuid.uuid4())

    # Gmail metadata endpoint supports at most 50 messages per request.
    limit = min(body.max_candidates, 50)

    # Fetch Inbox metadata only. No email bodies or write operations.
    gmail_result = gmail_messages(
        max_results=limit,
        label_ids=["INBOX"],
    )

    candidates = []

    for message in gmail_result["messages"]:
        labels = set(message.get("label_ids", []))

        # Until a real classifier is implemented, treat every message
        # as uncertain. Never infer promotion status from its subject.
        candidates.append({
            "message_id": message["message_id"],
            "sender": message.get("sender", ""),
            "recipient": message.get("recipient", ""),
            "subject": message.get("subject", ""),
            "date": message.get("date", ""),
            "label_ids": list(labels),
            "category": "uncertain",
            "is_sent": "SENT" in labels,
            "is_draft": "DRAFT" in labels,
            "is_work_related": False,
            "is_personally_protected": False,
            "classification_confident": False,
            "proposed_action": "keep",
        })

    payload = {
        "request_id": request_id,
        "request": body.request,
        "max_candidates": limit,
        "candidates": candidates,
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.post(
                f"{AGENT_SERVICE_URL}/plan",
                json=payload,
            )
            response.raise_for_status()
            result = response.json()

        result["source"] = "gmail_inbox_metadata"
        result["actions_executed"] = 0
        result["approval_required"] = True
        result["gmail_read_only"] = True
        result["message_bodies_fetched"] = False
        result["messages_retrieved"] = len(candidates)
        return result

    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "Agent service unavailable or returned an error: "
                f"{type(exc).__name__}"
            ),
        ) from exc



class RagIndexRequest(BaseModel):
    messages: list[dict[str, Any]] = Field(min_length=1, max_length=500)


class RagAskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    limit: int = Field(default=5, ge=1, le=20)


@app.post("/rag/index")
async def rag_index(body: RagIndexRequest) -> dict[str, Any]:
    """Forward explicitly supplied test or approved email records to the agent."""
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{AGENT_SERVICE_URL}/rag/index",
                json=body.model_dump(),
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail="Agent rejected the RAG indexing request",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail="Agent service unavailable during RAG indexing",
        ) from exc


@app.post("/rag/ask")
async def rag_ask(body: RagAskRequest) -> dict[str, Any]:
    """Forward a question to the agent's retrieval and answer pipeline."""
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{AGENT_SERVICE_URL}/rag/ask",
                json=body.model_dump(),
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail="Agent rejected the RAG question",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail="Agent service unavailable during RAG retrieval",
        ) from exc


