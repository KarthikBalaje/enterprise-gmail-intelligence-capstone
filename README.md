# Enterprise Gmail Intelligence & Safe Inbox Cleaner

**Week 4 — Enterprise Boardroom Capstone**

A read-only Gmail intelligence prototype that retrieves inbox metadata, routes candidate messages through an agent-based safety policy, and presents conservative cleanup recommendations through a React review interface.

## 1. Current Implementation Status

### Implemented and verified

- FastAPI API gateway and agent service orchestrated with Docker Compose.
- Gmail OAuth integration using the read-only `gmail.readonly` scope.
- Inbox metadata retrieval without fetching message bodies in the cleanup-plan workflow.
- Cleanup planning through the gateway and agent service.
- Conservative policy decisions: uncertain messages default to `keep` and require manual review.
- React frontend for reviewing cleanup candidates.
- Guardrail policy unit tests.
- Weaviate and Phoenix services included in the Docker Compose stack.
- Evidence capture for test results and the cleanup planner UI.

### In progress / not implemented

- Weaviate email ingestion, indexing, and retrieval.
- Grounded RAG answer generation and source citations.
- Persistent human-in-the-loop approvals.
- Gmail write executor and destructive actions.
- Fully automated end-to-end service tests.
- Verified end-to-end Phoenix trace export.
- Production CI/CD hardening.

## 2. Architecture

The intended request flow is:

`React Frontend → FastAPI Gateway → Agent Service → Guardrails / Review Policy`

Gmail metadata is retrieved through the gateway using read-only OAuth access. Weaviate is available as a service, but email RAG ingestion and retrieval are not yet complete. Phoenix is included for observability; end-to-end trace export remains unverified.

Architecture diagrams are available in `diagrams/`:

- `context.mmd`
- `container.mmd`
- `component.mmd`

## 3. Safety and Security

- Gmail OAuth access is restricted to `https://www.googleapis.com/auth/gmail.readonly`.
- The cleanup-plan workflow retrieves metadata only; message bodies are not fetched.
- No Gmail messages are archived, trashed, deleted, sent, or otherwise modified.
- Uncertain classifications default to `keep` and require manual review.
- Sent messages, drafts, work-related messages, and personally protected messages must be excluded from destructive actions.
- Any future destructive workflow must require explicit human approval, appropriate authorization, and audit logging.
- Email content must be treated as untrusted input, including possible prompt-injection attempts.
- Never commit `.env`, OAuth credentials, access tokens, personal email content, or unsanitized traces.

**Important:** This prototype is a read-only review workflow, not an automated inbox cleaner.

## 4. Run with Docker Compose

### Prerequisites

- Docker Desktop with Docker Compose.
- Node.js/npm if running frontend tooling locally.
- Python if running tests locally.
- Google OAuth client configuration for Gmail integration.

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

Keep OAuth credentials and token files outside the repository. Configure local secret and token paths according to `docker-compose.yml` and your local environment.

## 5. Test Results

Latest recorded test run:

```text
12 passed, 3 skipped
```

The skipped tests are:

- **End-to-end cleanup workflow:** the full service test harness is missing.
- **RAG integration:** retrieval and answer-generation integration is not implemented.
- **Protected-email actions:** the real action executor is intentionally disabled.

Evidence:

- `evidence/logs/pytest-results.txt`
- `evidence/screenshots/gmail-cleanup-planner.png`

These results establish that the current unit tests pass. They do not establish complete end-to-end or RAG functionality.

## 6. Evidence and Design Artifacts

- Solution design: `sdd/solution-design-document.md`
- Threat model: `sdd/threat-model.md`
- Rollout and rollback: `sdd/rollout-rollback.md`
- Architecture diagrams: `diagrams/`
- Test report: `evidence/logs/pytest-results.txt`
- UI screenshot: `evidence/screenshots/gmail-cleanup-planner.png`

Additional sanitized service logs and trace evidence can be added under `evidence/logs/` and `evidence/traces/` as the relevant workflows are verified.

## 7. Known Limitations and Next Steps

1. Implement authorized email ingestion and Weaviate indexing.
2. Implement retrieval with source-grounded answers and verify citations.
3. Add integration tests for the retrieval and answer pipeline.
4. Add a full service-level end-to-end test harness.
5. Verify Phoenix trace propagation across the gateway and agent service.
6. Complete the official capstone SDD requirements and document the required incident mappings.
7. Keep Gmail write operations disabled until approval, policy, audit, and adversarial security tests are complete.

## 8. Repository Hygiene

Check staged files before committing:

```powershell
git status --short
git check-ignore .env
```

Do not commit secrets, OAuth tokens, credentials, personal email content, or unsanitized diagnostic output.
