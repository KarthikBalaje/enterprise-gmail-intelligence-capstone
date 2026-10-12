# Capstone Verification Report

**Run date:** 2026-10-12  
**Scope:** Local, synthetic/mocked verification only. No Gmail API calls were made and no existing Weaviate records were queried.

## Results

| Check | Command/action | Result |
|---|---|---|
| Automated tests | `python -m pytest -q` | **22 passed** |
| Compose syntax | `docker compose config --quiet` | Passed |
| Python syntax | `python -m compileall -q api-gateway/app agent-service/app tests/integration` | Passed |
| Service image builds | `docker compose build api-gateway agent-service` | Both images built successfully |
| Gateway image import/route registration | Load app OpenAPI in the built gateway image | `/cleanup/assist` registered |
| Agent image import/route registration | Load app OpenAPI in the built agent image | `/plan` and `/rag/ask` registered |
| Composite workflow test | `tests/integration/test_gateway_assist_flow.py` with mocked downstream calls | Verified plan then RAG ordering, request ID, and dry-run result |

The project `.venv` does not have pytest installed; the passing suite was run with the available system `python` and pytest. The container smoke tests use dummy OAuth file paths and do not open those files.

## Synthetic live-check procedure

Run this separate Compose project. It has a new Weaviate volume, dummy OAuth paths, and loopback-only ports; it does not mount or query the default Compose vector store. The script prints counts and status fields, not the answer or source contents:

```powershell
docker compose -p capstone-synthetic -f docker-compose.synthetic.yml up -d --build --wait --wait-timeout 120
python scripts/verify_synthetic_e2e.py
# Review Phoenix at http://localhost:16006, then remove only the synthetic stack/data:
docker compose -p capstone-synthetic -f docker-compose.synthetic.yml down --volumes
```

## Live synthetic end-to-end run

The live run used a separate temporary Compose project with a fresh Weaviate volume and the locally built gateway/agent images. It did not mount Gmail credentials or access the existing development vector store.

| Result | Value |
|---|---|
| Synthetic RAG chunks indexed | 1 |
| Composite endpoint | `POST /cleanup/assist` |
| Request ID | `f628a512-7ebc-42b1-9810-5a83682bd98e` |
| Planned candidates | 4 |
| Gmail actions executed | 0 |
| RAG grounded | `true` |
| Cited sources | 1 |
| Phoenix trace ID | `3b1e9bff5fd33e71a83c8911790510e2` |
| Trace continuity | Gateway `/cleanup/assist`, agent `/plan`, and agent `/rag/ask` spans shared the trace ID |
| Downstream spans | Phoenix recorded HTTP spans to the agent service, Ollama `/api/embed` and `/api/chat`, and Weaviate schema/object/query endpoints |

Only counts, identifiers, and endpoint names are retained here; no synthetic email text or model answer is recorded. The temporary Compose stack and synthetic volume were removed after verification.

## Remaining evidence

A sanitized Phoenix UI screenshot/export is still recommended for the portfolio. The existing development Weaviate volume may contain private email data; do not query it for evidence unless its output is intentionally reviewed. Do not place email bodies, personal data, credentials, or tokens in public evidence.
