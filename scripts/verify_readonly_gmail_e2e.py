"""Run a one-message Gmail read-only flow and print only redacted counts."""

import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


API_URL = os.getenv("CAPSTONE_API_URL", "http://127.0.0.1:8000").rstrip("/")
MAX_RESULTS = int(os.getenv("GMAIL_MAX_RESULTS", "1"))

if not 1 <= MAX_RESULTS <= 3:
    raise SystemExit("GMAIL_MAX_RESULTS must be between 1 and 3")


def main() -> int:
    payload = {
        "request": "Review one inbox message conservatively; keep uncertain items",
        "question": "Summarize the indexed inbox item using cited evidence.",
        "max_candidates": 1,
        "use_gmail_metadata": True,
        "index_gmail_for_rag": True,
        "gmail_max_results": MAX_RESULTS,
    }
    request = Request(
        f"{API_URL}/cleanup/assist",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=240) as response:
            result = json.load(response)
    except HTTPError as exc:
        print(f"Read-only Gmail request failed with HTTP {exc.code}", file=sys.stderr)
        return 1
    except URLError:
        print(f"Could not reach the local API at {API_URL}", file=sys.stderr)
        return 1

    plan = result.get("cleanup_plan", {})
    indexing = result.get("gmail_indexing", {})
    related_context = result.get("related_context", {})
    summary = {
        "index_status": indexing.get("status", "unknown"),
        "gmail_read_only": indexing.get("gmail_read_only", False),
        "messages_fetched": indexing.get("messages_fetched", 0),
        "messages_indexed": indexing.get("messages_indexed", 0),
        "chunks_indexed": indexing.get("chunks_indexed", 0),
        "messages_skipped_empty": indexing.get("skipped_empty", 0),
        "planned_candidates": len(plan.get("candidates", [])),
        "actions_executed": plan.get("actions_executed", -1),
        "rag_grounded": related_context.get("grounded", False),
        "source_count": len(related_context.get("sources", [])),
    }
    if not summary["gmail_read_only"] or summary["actions_executed"] != 0:
        print("Safety check failed; inspect local service status.", file=sys.stderr)
        return 1

    # Deliberately omit subjects, senders, message IDs, bodies, answers, and tokens.
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
