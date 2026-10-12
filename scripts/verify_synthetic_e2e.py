"""Exercise the composite API using synthetic email data only."""

import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


API_URL = os.getenv("CAPSTONE_API_URL", "http://127.0.0.1:18000").rstrip("/")


def post(path: str, payload: dict) -> dict:
    request = Request(
        f"{API_URL}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=210) as response:
            return json.load(response)
    except HTTPError as exc:
        raise RuntimeError(f"POST {path} failed with HTTP {exc.code}") from None
    except URLError:
        raise RuntimeError(f"Could not reach the local API at {API_URL}") from None


def main() -> int:
    indexed = post(
        "/rag/index",
        {
            "messages": [
                {
                    "id": "synthetic-message-001",
                    "subject": "Synthetic test meeting",
                    "sender": "qa@example.test",
                    "date": "2026-10-12",
                    "labels": ["INBOX"],
                    "body": (
                        "Synthetic test data only. The project review meeting "
                        "is Thursday at 2 PM."
                    ),
                }
            ]
        },
    )
    if indexed.get("chunks_indexed", 0) < 1:
        raise RuntimeError("Synthetic test record was not indexed")

    result = post(
        "/cleanup/assist",
        {
            "request": "Review synthetic newsletter metadata for cleanup recommendations",
            "question": "When is the synthetic project review meeting?",
            "max_candidates": 5,
        },
    )
    plan = result["cleanup_plan"]
    rag = result["related_context"]
    if plan.get("actions_executed") != 0:
        raise RuntimeError("Safety check failed: a cleanup action was executed")
    if not rag.get("sources"):
        raise RuntimeError("RAG did not return a cited synthetic source")

    print(
        json.dumps(
            {
                "request_id": result["request_id"],
                "chunks_indexed": indexed["chunks_indexed"],
                "planned_candidates": len(plan.get("candidates", [])),
                "actions_executed": plan["actions_executed"],
                "grounded": rag.get("grounded"),
                "source_count": len(rag.get("sources", [])),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, RuntimeError) as exc:
        print(f"Synthetic E2E verification failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
