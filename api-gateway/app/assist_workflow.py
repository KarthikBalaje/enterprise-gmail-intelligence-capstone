"""Orchestrate the composite cleanup-plan and RAG request to the agent service."""

import httpx


async def run_assisted_plan(
    *,
    agent_service_url: str,
    request_id: str,
    request: str,
    question: str,
    max_candidates: int,
    candidates: list[dict] | None = None,
) -> dict:
    """Run planning and retrieval under the gateway's single client request."""
    base_url = agent_service_url.rstrip("/")
    async with httpx.AsyncClient(timeout=210.0) as client:
        plan_payload = {
            "request_id": request_id,
            "request": request,
            "max_candidates": max_candidates,
        }
        if candidates is not None:
            plan_payload["candidates"] = candidates

        plan_response = await client.post(f"{base_url}/plan", json=plan_payload)
        plan_response.raise_for_status()

        rag_response = await client.post(
            f"{base_url}/rag/ask",
            json={"question": question, "limit": 5},
        )
        rag_response.raise_for_status()

    return {
        "request_id": request_id,
        "cleanup_plan": plan_response.json(),
        "related_context": rag_response.json(),
    }
