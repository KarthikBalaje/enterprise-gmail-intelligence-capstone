# Rollout and Rollback Plan

**Project:** Enterprise Gmail Intelligence & Safe Inbox Cleaner  
**Deployment target:** Local Docker Compose capstone environment
**Safety posture:** Read-only Gmail, no write execution

## 1. Rollout Strategy

The system rolls out in staged gates. Each gate must produce sanitized evidence before the next gate is considered complete.

### Stage 1: Local Synthetic Validation

**Objective:** Validate the service graph without Gmail credentials.

**Scope**

- Frontend
- API gateway
- Agent service
- Guardrail policy
- Synthetic cleanup candidates
- Synthetic RAG records

**Acceptance criteria**

- `pytest -q -rs` passes.
- `docker compose config` succeeds.
- `docker compose ps` shows required services.
- No Gmail write route exists.
- Cleanup plans return `actions_executed: 0`.

**Current status:** Implemented and passing locally.

### Stage 2: Read-Only Gmail Metadata Pilot

**Objective:** Validate OAuth and Gmail metadata cleanup planning.

**Scope**

- Gmail OAuth with `gmail.readonly`.
- Inbox metadata retrieval.
- Dry-run cleanup planning.

**Acceptance criteria**

- OAuth token is stored outside the repository.
- Granted scope is read-only.
- Cleanup plan uses metadata format and does not fetch bodies.
- Returned plan requires approval and executes zero actions.
- Evidence excludes personal subjects, body text, tokens, and credentials.

**Current status:** Implemented; evidence should be refreshed before final submission.

### Stage 3: Local RAG Validation

**Objective:** Verify the vector RAG layer for the capstone end-to-end flow.

**Scope**

- RAG indexing.
- Ollama embeddings.
- Weaviate vector storage and retrieval.
- Qwen answer generation.
- Source citations.
- Insufficient-evidence behavior.

**Acceptance criteria**

- Synthetic or explicitly authorized records are indexed.
- A question retrieves relevant chunks from Weaviate.
- The answer includes valid source citations.
- Unsupported questions return insufficient evidence.
- Sanitized request/response evidence is stored under `evidence/logs/`.

**Current status:** Code and automated tests are implemented; sanitized live evidence still needs to be captured.

### Stage 4: Observability Evidence Gate

**Objective:** Prove that the request path is observable.

**Scope**

- Gateway spans.
- Agent-service spans.
- Phoenix dashboard.
- Sanitized evidence artifact.

**Acceptance criteria**

- Phoenix is reachable at `http://localhost:6006`.
- A request produces visible spans for gateway and agent service.
- Trace evidence is saved under `evidence/traces/`.
- Trace evidence does not contain OAuth tokens or personal email body text.

**Current status:** Instrumented; trace evidence still required.

### Stage 5: Future Human-Approved Writes

**Objective:** Introduce Gmail modification only after a separate security review.

**Prerequisites**

- Separately approved minimum write scope.
- Persistent approval records bound to message ID and action.
- Fresh policy evaluation immediately before execution.
- Audit records for every attempted action.
- Emergency write-disable mechanism.
- Protected-message and adversarial tests.
- Rollback and user-notification playbook.

**Current status:** Not implemented. Do not enable write scopes or actions.

## 2. Rollback Triggers

Rollback or disable the affected capability when any of the following occurs:

1. Unauthorized Gmail action or suspected write route exposure.
2. OAuth credential or token exposure.
3. Protected-message policy regression.
4. RAG answer without valid evidence citation.
5. Trace/log artifact containing secrets or unnecessary personal content.
6. Critical dependency, container, or CI failure.
7. Weaviate, Ollama, gateway, or agent service instability that affects evidence quality.

## 3. Rollback Procedure

1. Stop the Compose stack:

```powershell
docker compose down
```

2. Preserve sanitized diagnostics:

```powershell
docker compose logs --tail=200
```

3. Remove or quarantine unsafe evidence artifacts.
4. Revoke or rotate OAuth credentials if exposure is suspected.
5. Return to the last verified commit or image.
6. Re-run `docker compose config`, `pytest -q -rs`, and readiness checks.
7. Re-enable only the validated read-only stages.

## 4. Recovery Limitations

- Rolling back application containers does not delete data already indexed in Weaviate.
- OAuth revocation prevents future access but does not remove previously captured evidence.
- If future write actions are ever enabled, application rollback cannot automatically reverse Gmail changes.
- Trace and log evidence may be incomplete if telemetry export fails.

## 5. Operational Verification Commands

```powershell
docker compose config
docker compose up --build -d
docker compose ps
Invoke-RestMethod http://localhost:8000/ready
pytest -q -rs
```

## 6. Rollout Decision Record

| Stage | Status | Decision |
|---|---|---|
| Local synthetic validation | Implemented | Keep as baseline gate |
| Read-only Gmail metadata pilot | Implemented | Refresh sanitized evidence |
| Local RAG validation | Implemented in code | Capture live sanitized evidence |
| Observability evidence gate | Instrumented | Capture Phoenix trace evidence |
| Human-approved writes | Not implemented | Blocked until separate review |

**Final decision:** proceed only with read-only capstone validation. Gmail write functionality remains outside the current release.
