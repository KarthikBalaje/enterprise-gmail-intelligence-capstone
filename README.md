# Enterprise Gmail Intelligence & Safe Inbox Cleaner

**Week 4 - Enterprise Boardroom Capstone**

A read-only Gmail intelligence prototype that retrieves inbox metadata, routes cleanup candidates through deterministic safety policy, and supports local email RAG with Weaviate, Ollama embeddings, and cited answers.

## 1. Current Implementation Status

### Implemented and verified

- FastAPI API gateway and agent service orchestrated with Docker Compose.
- Gmail OAuth integration using the read-only `gmail.readonly` scope.
- Inbox metadata retrieval without fetching message bodies in the cleanup-plan workflow.
- Cleanup planning through the gateway and agent service.
- Composite `POST /cleanup/assist` request that returns a guarded dry-run plan and a RAG result from one client request.
- Conservative policy decisions: uncertain messages default to `keep` and require manual review.
- React frontend for reviewing cleanup candidates and asking indexed email questions.
- Guardrail policy, cleanup workflow, and RAG citation tests.
- RAG ingestion helpers, Weaviate indexing, vector retrieval, Ollama embeddings, and Qwen-based answer generation.
- Source citation validation and insufficient-evidence fallback.
- Weaviate and Phoenix services included in the Docker Compose stack.
- Evidence capture for test results and the cleanup planner UI.

### Still incomplete or intentionally disabled

- Gmail write executor and destructive actions.
- Persistent human-in-the-loop approvals and audit persistence.
- Verified Phoenix end-to-end trace screenshots or exports.
- Production security hardening, dependency scanning, and CI/CD gates.
- Phoenix UI screenshot/export for the composite request (trace receipt and correlation are verified in the evidence report).
- Production security hardening, including dependency/container scanning, immutable image pins, and Weaviate authentication.
- Validation against the official ADaSci SDD template (the template itself is not present in this repository).

## 2. Architecture

Cleanup flow:

`React Frontend -> FastAPI Gateway -> Agent Service -> Guardrails / Review Policy`

RAG flow:

`React Frontend -> FastAPI Gateway -> Agent Service -> RAG Service -> Weaviate / Ollama`

The API-level integrated path is `POST /cleanup/assist`: the gateway sends one planning request through the guardrail workflow, then one related-context query through RAG. Gateway and agent HTTP calls are instrumented for Phoenix. The request sequence is unit-tested with mocks and was also verified live using an isolated synthetic-only stack; details are in `evidence/verification-report.md`.

For an authorized real-inbox check, `POST /cleanup/assist` accepts `use_gmail_metadata: true`, `index_gmail_for_rag: true`, and `gmail_max_results: 1` (maximum 3). This indexes a bounded Gmail batch locally using the read-only OAuth scope, plans from metadata only, and retrieves context. `python scripts/verify_readonly_gmail_e2e.py` exercises this path and prints counts/status only; email content and answers are not written to evidence.

Cleanup planning fetches Gmail metadata only. Optional RAG indexing is a separate, explicitly enabled read-only operation that fetches a bounded Inbox batch for local indexing; the indexing endpoint returns counts, not email bodies. The composite verifier suppresses subjects, senders, IDs, bodies, and generated answers from terminal output.

Architecture diagrams are available in `diagrams/`:

- `context.mmd`
- `container.mmd`
- `component.mmd`

## 3. Safety and Security

- Gmail OAuth access is restricted to `https://www.googleapis.com/auth/gmail.readonly`.
- The cleanup-plan workflow retrieves metadata only; message bodies are not fetched.
- No Gmail messages are archived, trashed, deleted, sent, or otherwise modified.
- Uncertain classifications default to `keep` and require manual review.
- Sent messages, drafts, work-related messages, and personally protected messages are protected from destructive cleanup policy.
- Any future destructive workflow must require explicit human approval, fresh server-side policy checks, appropriate authorization, and audit logging.
- Email content is treated as untrusted input in the RAG prompt.
- Weaviate anonymous access is enabled only for the localhost-bound development stack; do not expose this configuration to a shared or production network.
- Never commit `.env`, OAuth credentials, access tokens, personal email content, or unsanitized traces.

**Important:** This prototype is a read-only review and intelligence workflow, not an automated inbox cleaner.

## 4. Run with Docker Compose

### Prerequisites

- Docker Desktop with Docker Compose.
- Node.js/npm if running frontend tooling locally.
- Python if running tests locally.
- Ollama running locally with the configured embedding and chat models.
- Optional Gmail integration: place the OAuth client JSON at `secrets/gmail/oauth-client.json` (or configure `GMAIL_SECRETS_DIR` in `.env`). The OAuth token is persisted under `data/gmail/` (or `GMAIL_DATA_DIR`). Both paths are local-only and ignored by Git.

Review the configuration before starting:

```powershell
docker compose config
docker compose up --build -d
docker compose ps
```

Inspect service logs when troubleshooting:

```powershell
docker compose logs --tail=100
```

### Local endpoints

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| API documentation | http://localhost:8000/docs |
| API readiness | http://localhost:8000/ready |
| Phoenix UI | http://localhost:6006 |
| Weaviate HTTP endpoint | http://localhost:8081 |

The default Compose mounts keep OAuth client credentials read-only and persist the token in an ignored local data directory. Override `GMAIL_SECRETS_DIR` and `GMAIL_DATA_DIR` in `.env` if you prefer locations outside the repository. Never commit the OAuth client JSON, token, or `.env` file.

### Isolated synthetic end-to-end verification

This separate stack uses a fresh Weaviate volume, dummy OAuth paths, and loopback-only ports; it does not mount Gmail credentials or touch the default Compose vector volume. The verification script prints counts/status only, not email text or the generated answer.

```powershell
docker compose -p capstone-synthetic -f docker-compose.synthetic.yml up -d --build --wait --wait-timeout 120
python scripts/verify_synthetic_e2e.py
# Review the trace at http://localhost:16006 before teardown.
docker compose -p capstone-synthetic -f docker-compose.synthetic.yml down --volumes
```

The separate real-Gmail verifier uses the already configured local OAuth token and stores at most one message in the default local Weaviate volume. Run it only when you intend to index that inbox content locally; the Gmail API remains read-only and no messages are changed:

```powershell
python scripts/verify_readonly_gmail_e2e.py
```

## 5. Test Results

Latest verified local test run:

```text
22 passed
```

The test suite covers:

- Guardrail policy decisions.
- Dry-run cleanup planning.
- Protected-email bulk policy behavior.
- RAG document preparation.
- Insufficient-evidence fallback.
- Citation validation for grounded answers.
- Composite gateway planning-plus-RAG request orchestration.

The tests use deterministic synthetic records and mocks for model calls where appropriate. They do not prove production-grade Gmail, Weaviate, Ollama, or Phoenix availability by themselves.

Evidence:

- `evidence/logs/pytest-results.txt`
- `evidence/screenshots/gmail-cleanup-planner.png`
- `evidence/verification-report.md` (latest local checks and safe synthetic live-check procedure)

## 6. Evidence and Design Artifacts

- Solution design: `sdd/solution-design-document.md`
- Threat model: `sdd/threat-model.md`
- Rollout and rollback: `sdd/rollout-rollback.md`
- Architecture diagrams: `diagrams/`
- Test report: `evidence/logs/pytest-results.txt`
- UI screenshot: `evidence/screenshots/gmail-cleanup-planner.png`
- Verification report: `evidence/verification-report.md`

Additional sanitized service logs and trace evidence can be added under `evidence/logs/` and `evidence/traces/` as the relevant workflows are verified.

## 7. Known Limitations and Next Steps

1. Capture a Phoenix UI screenshot/export for the already verified isolated synthetic flow. Do not query a local index that may contain private email unless its output is intentionally reviewed.
2. Preserve sanitized trace evidence when repeating the synthetic flow; `evidence/verification-report.md` records the current correlation check.
3. Compare this SDD against the official ADaSci template when it is available.
4. Add dependency/container scanning evidence, immutable image pins, and Weaviate authentication before any shared deployment.
5. Keep Gmail write operations disabled; the current OAuth scope is read-only.

## 8. Repository Hygiene

Check staged files before committing:

```powershell
git status --short
git check-ignore .env
```

Do not commit secrets, OAuth tokens, credentials, personal email content, or unsanitized diagnostic output.
