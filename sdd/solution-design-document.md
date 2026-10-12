# Solution Design Document (SDD)

## Enterprise Gmail Intelligence & Safe Inbox Cleaner

**Project:** Week 4 — Enterprise Boardroom Capstone  
**Status:** Prototype / Partial Implementation  
**Architecture style:** Containerized services with API gateway and agent-based planning

---

## 1. Executive Summary

The Enterprise Gmail Intelligence & Safe Inbox Cleaner is a prototype for reviewing Gmail inbox metadata and producing conservative cleanup recommendations.

The application uses a React frontend, FastAPI API gateway, Python agent service, and deterministic guardrail policies. Gmail access uses OAuth with the read-only `gmail.readonly` scope. The current workflow retrieves message metadata and produces a dry-run plan without modifying email.

Uncertain classifications default to `keep` and require manual review. Destructive Gmail operations are not implemented or enabled.

The intended broader solution includes email ingestion, Weaviate retrieval, grounded retrieval-augmented generation (RAG), persistent human-in-the-loop (HITL) approvals, and distributed observability. These components are not all implemented and must not be treated as production-ready.

### Current verified capabilities

- Read-only Gmail OAuth integration.
- Inbox metadata retrieval without fetching message bodies in the cleanup-plan endpoint.
- API gateway to agent-service planning workflow.
- Deterministic safety policy and unit tests.
- React review interface.
- Docker Compose deployment of the frontend, gateway, agent service, Weaviate, and Phoenix.

### Known limitations

- RAG ingestion, indexing, retrieval, and grounded answer generation are incomplete.
- Persistent HITL approvals are not implemented.
- Gmail write operations are disabled.
- The full service-level end-to-end test harness is missing.
- End-to-end Phoenix trace propagation has not been verified.

---

## 2. Scope and Requirements

### 2.1 Functional requirements

| ID | Requirement | Current status |
|---|---|---|
| FR-01 | Connect to Gmail using OAuth | Implemented and verified |
| FR-02 | Retrieve inbox metadata with read-only access | Implemented and verified |
| FR-03 | Generate a cleanup review plan through the agent service | Implemented and verified |
| FR-04 | Default uncertain classifications to keeping messages | Implemented and unit-tested |
| FR-05 | Protect sent, draft, work-related, and personally protected messages from destructive actions | Policy requirements implemented in guardrails; full action execution disabled |
| FR-06 | Present cleanup candidates in a frontend | Implemented |
| FR-07 | Ingest emails and index them in Weaviate | Not implemented |
| FR-08 | Retrieve relevant emails for a question | Not implemented |
| FR-09 | Generate grounded answers with source citations | Not implemented |
| FR-10 | Persist human approval decisions | Not implemented |
| FR-11 | Execute Gmail modifications after approval | Not implemented |
| FR-12 | Export and verify distributed traces in Phoenix | Not fully verified |

### 2.2 Non-functional requirements

- **Security:** use least-privilege OAuth scopes and keep credentials outside the repository.
- **Safety:** never modify Gmail during the current prototype workflow.
- **Privacy:** avoid retrieving email bodies unless a separately authorized feature requires them.
- **Reliability:** expose health/readiness checks and use deterministic policy decisions.
- **Maintainability:** separate gateway, agent logic, guardrails, frontend, and retrieval responsibilities.
- **Testability:** keep policy logic testable independently and document skipped integration tests.
- **Observability:** provide service logs and health checks; distributed trace verification remains outstanding.

### 2.3 Assumptions and exclusions

- Gmail access is explicitly authorized by the account owner.
- Local development uses Docker Compose.
- The current workflow is a read-only review prototype.
- Production email modification, automatic deletion, and unattended cleanup are outside the implemented scope.
- The design does not claim that RAG or production-grade observability is complete.

---

## 3. Five Production Layers

### Layer 1: Presentation and API Gateway

**Components**
- React frontend
- FastAPI API gateway

**Responsibilities**
- Display cleanup candidates and policy outcomes.
- Accept cleanup-planning requests.
- Retrieve Gmail metadata through the OAuth integration.
- Forward candidate data to the agent service.
- Expose health/readiness and API documentation endpoints.

**Verification**
- Frontend: `http://localhost:5173`
- API docs: `http://localhost:8000/docs`
- Readiness: `http://localhost:8000/ready`

### Layer 2: Security and Guardrails

**Components**
- Deterministic policy engine
- Cleanup planning/review policy
- Gmail read-only OAuth integration

**Responsibilities**
- Enforce conservative decisions.
- Default uncertain candidates to `keep`.
- Prevent destructive actions against protected categories.
- Keep Gmail write operations disabled.
- Treat email content as untrusted input.

**Verification**
- Run `pytest -q -rs`.
- Review `guardrails/` and the security tests under `tests/`.

### Layer 3: Agentic Intelligence

**Component**
- Python agent service

**Responsibilities**
- Receive cleanup-plan requests.
- Process candidate metadata.
- Apply the planning and review policy.
- Return candidate decisions and review statuses.

The current implementation is a deterministic planning workflow. It should not be described as a fully autonomous multi-agent system or as an LLM-based classifier unless those features are implemented and verified.

### Layer 4: Email Knowledge and Retrieval

**Planned components**
- Email ingestion and normalization
- Embedding generation
- Weaviate indexing and retrieval
- Grounded answer generation
- Source citations

Weaviate is available in Docker Compose, but the complete email RAG workflow is not implemented. No claim of successful retrieval, grounded answers, or source citations should be made yet.

**Completion criteria**
1. Authorized documents can be ingested safely.
2. Email records are indexed in Weaviate.
3. Queries retrieve relevant records.
4. Answers cite retrieved sources.
5. Tests verify that answers are grounded and insufficient evidence is handled safely.

### Layer 5: DevOps and Observability

**Components**
- Docker Compose
- Health/readiness endpoints
- Phoenix service
- Evidence and test-report directories

The frontend, API gateway, agent service, Weaviate, and Phoenix are included in the local Compose deployment.

End-to-end trace propagation and Phoenix trace export remain unverified. Production alerting, retention controls, and CI/CD hardening are not yet complete.

---

## 4. C4 Architecture

The project includes the following Mermaid diagrams:

- Context: `../diagrams/context.mmd`
- Container: `../diagrams/container.mmd`
- Component: `../diagrams/component.mmd`

The diagrams should distinguish implemented components from planned components. In particular, the presence of Weaviate and Phoenix containers does not establish that email retrieval or distributed tracing is operational.

### Logical request flow

```text
User
 |
 v
React Frontend
 |
 v
FastAPI API Gateway
 |                 \
 |                  \--> Gmail API
 |                       (read-only metadata)
 v
Agent Service
 |
 v
Guardrails / Review Policy
 |
 v
Cleanup Plan Response
 |
 v
React Review Interface
```

The planned RAG flow adds ingestion, indexing, retrieval, and grounded answer generation. That path is not yet complete.

---

## 5. Data Flow and Trust Boundaries

### 5.1 Current cleanup-planning flow

1. The user authorizes Gmail access using OAuth.
2. The gateway retrieves inbox metadata using the read-only Gmail scope.
3. The gateway constructs candidate records without fetching message bodies.
4. The candidate records are sent to the agent service.
5. The planner and guardrails produce conservative decisions.
6. The API returns the plan and review statuses to the frontend.
7. No Gmail modification is executed.

### 5.2 Trust boundaries

| Boundary | Data crossing the boundary | Required controls |
|---|---|---|
| Browser to gateway | User requests and plan responses | Local binding, request validation |
| Gateway to Gmail API | OAuth token and metadata requests | Read-only scope, protected token storage |
| Gateway to agent service | Candidate metadata and planning request | Schema validation, bounded input |
| Agent service to policy layer | Candidate attributes and proposed decisions | Deterministic policy, safe defaults |
| Application to Weaviate | Future indexed email records and queries | Authorization, access filtering, retention controls |
| Application to Phoenix | Operational telemetry | Redaction and sensitive-data filtering |

### 5.3 Future approval and write boundary

Any future Gmail write workflow must be isolated from the current read-only path. It must require explicit human approval, enforce policy again at execution time, and generate an auditable decision record. No such executor is currently enabled.

---

## 6. Security and Privacy

### 6.1 OAuth and credentials

- Use `https://www.googleapis.com/auth/gmail.readonly`.
- Store OAuth client configuration and token files outside the repository.
- Exclude `.env`, credentials, and tokens from Git.
- Never log access tokens or OAuth secrets.
- Do not request Gmail modification scopes for the current prototype.

### 6.2 Email protection

- Sent messages and drafts must be protected.
- Work-related and personally protected messages must be excluded from destructive actions.
- Uncertain classifications must default to `keep` and manual review.
- Do not fetch email bodies in the current cleanup-plan workflow.

### 6.3 Prompt injection

If RAG or LLM processing is introduced, email content must be treated as untrusted data, not as instructions that override system policy. Retrieved content must not authorize tool use or bypass approval controls.

### 6.4 Logging and retention

- Keep test evidence sanitized.
- Do not store unnecessary personal email content in logs or traces.
- Define explicit retention and deletion policies before introducing persistent email indexing.
- Configure access controls and encryption appropriate to the deployment before production use.

Encryption, formal retention enforcement, and production access-control hardening require additional verification.

---

## 7. Observability and Operations

### 7.1 Health and readiness

Use the API readiness endpoint:

```powershell
Invoke-RestMethod http://localhost:8000/ready
```

Inspect service status:

```powershell
docker compose ps
```

Inspect service logs when troubleshooting:

```powershell
docker compose logs --tail=100
```

### 7.2 Phoenix

Phoenix is available at `http://localhost:6006`.

The presence of the Phoenix container does not prove that traces propagate across the gateway and agent service. Trace export, correlation, redaction, and end-to-end visualization must be verified before observability is marked complete.

### 7.3 Error handling and runbooks

Operational follow-up work includes:
- OAuth expiration and reauthorization handling.
- Gmail API rate limits and transient failures.
- Agent-service timeout and unavailable-service handling.
- Weaviate ingestion and retrieval failures.
- Trace export failures.
- Sanitized diagnostic collection and recovery procedures.

Production alerting and operational service-level objectives are not yet defined.

---

## 8. Testing and Evidence

### 8.1 Latest recorded tests

```text
12 passed, 3 skipped
```

The skipped tests are:

- `tests/e2e/test_cleanup_workflow.py`: full service test harness is missing.
- `tests/integration/test_rag_flow.py`: RAG integration is not implemented.
- `tests/security/test_protected_email_actions.py`: the real action executor is intentionally disabled.

### 8.2 Reproduce the test run

```powershell
pytest -q -rs
```

### 8.3 Recorded evidence

- Test report: `../evidence/logs/pytest-results.txt`
- Cleanup planner screenshot: `../evidence/screenshots/gmail-cleanup-planner.png`

### 8.4 Additional evidence required

- Sanitized `docker compose ps` output.
- Sanitized service logs.
- A documented request/response demonstrating gateway-to-agent processing.
- Verified Phoenix trace evidence after trace propagation is implemented.
- RAG retrieval and citation evidence after the RAG pipeline is implemented.
- Automated service-level end-to-end test results.

Do not include personal email subjects, message bodies, OAuth tokens, or other secrets in submitted evidence.

---

## 9. Threat Model

See `threat-model.md`.

The threat model should cover, at minimum:

- Unauthorized access and OAuth token exposure.
- Destructive action against protected or misclassified email.
- Prompt injection through email content.
- Sensitive data leakage through logs, traces, or indexed content.
- Unauthorized execution without human approval.

The course requires explicit mapping of three prior weekly incidents. Their exact descriptions are not included in this document, so those mappings must be completed using the official course materials rather than invented.

---

## 10. Rollout and Rollback

See `rollout-rollback.md`.

### Current rollout stage

The current stage is a local, read-only prototype. Gmail write operations are disabled.

### Minimum rollout gates

1. Unit and policy tests pass.
2. OAuth scope and secret handling are verified.
3. No destructive action is reachable through the read-only workflow.
4. The end-to-end service test harness passes.
5. RAG ingestion, retrieval, and grounding tests pass before RAG is advertised as operational.
6. Phoenix trace propagation is demonstrated before observability is marked complete.
7. Security review and human-approval controls pass before any future write executor is enabled.

### Rollback

For local failures, stop the Compose stack and return to the last verified code/configuration state. Preserve sanitized diagnostic evidence and keep Gmail write operations disabled.

Specific measurable recovery-time objectives, recovery-point objectives, and production rollback procedures remain to be defined.

---

## 11. Assessment Traceability

| Assessment area | Artifact | Verification |
|---|---|---|
| API gateway and service orchestration | `docker-compose.yml`, `api-gateway/`, `agent-service/` | `docker compose ps`; `Invoke-RestMethod http://localhost:8000/ready` |
| Gmail integration | `api-gateway/app/gmail_oauth.py` | Read-only status and metadata dry-run |
| Guardrails | `guardrails/`, `tests/` | `pytest -q -rs` |
| Frontend | `frontend/` | Open `http://localhost:5173` |
| C4 architecture | `diagrams/` | Review the three `.mmd` files |
| Security and privacy | `threat-model.md` | Review scope, token handling, protected-email rules |
| Rollout and rollback | `rollout-rollback.md` | Review documented gates and recovery procedures |
| Test evidence | `../evidence/logs/pytest-results.txt` | Inspect the saved report |
| UI evidence | `../evidence/screenshots/gmail-cleanup-planner.png` | Inspect the screenshot |
| RAG integration | `rag-service/` | Incomplete; integration test is skipped |
| End-to-end workflow | `tests/e2e/` | Incomplete; service test harness is missing |
| Distributed tracing | `observability/` | Incomplete; end-to-end trace export is unverified |

---

## Final Status

This project demonstrates a working read-only Gmail metadata review workflow, agent-service planning, conservative guardrails, a React review interface, and a containerized local deployment.

It does not yet demonstrate a complete RAG pipeline, persistent HITL approvals, a Gmail write executor, a full automated end-to-end test harness, or verified distributed trace propagation.

These limitations must remain explicit in the capstone submission until the corresponding implementation and evidence are complete.

**Template note:** Adapt this document to the official ADaSci Enterprise SDD template if one is provided by the course.
