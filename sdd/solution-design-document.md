# Solution Design Document

## Enterprise Gmail Intelligence & Safe Inbox Cleaner

**Capstone problem:** enterprise AI pilots fail review when teams submit demos instead of deployment-ready systems.
**Assessment target:** five-layer production-style system plus CISO-ready SDD, C4 diagrams, threat model, rollout plan, and evidence.

---

## 1. Executive Summary

Enterprise Gmail Intelligence & Safe Inbox Cleaner is a read-only Gmail intelligence system that connects four weekly artifacts into one deployable narrative:

- CI/CD and repository hygiene.
- Multi-agent cleanup planning with deterministic guardrails.
- RAG over indexed email content.
- Capstone deployment evidence through Docker Compose, C4 diagrams, telemetry, and security documentation.

The application uses a React frontend, FastAPI API gateway, Python agent service, deterministic policy engine, Weaviate vector database, local Ollama models, and Arize Phoenix telemetry. Gmail access uses the least-privilege `gmail.readonly` OAuth scope. Cleanup planning is dry-run only and does not modify Gmail.

Gmail write operations, automated deletion, persistent approvals, and production audit persistence are intentionally out of scope for the current capstone build.

---

## 2. Assessment Traceability

| Assessment category | Weight | Repository evidence |
|---|---:|---|
| Multi-container orchestration | 25 | `docker-compose.yml` orchestrates frontend, FastAPI gateway, agent service, Weaviate, and Phoenix |
| End-to-end flow verification | 25 | `evidence/verification-report.md` records the isolated synthetic request, RAG result, and Phoenix trace correlation |
| SDD - C4 diagrams | 15 | Mermaid C4-style diagrams in `diagrams/context.mmd`, `diagrams/container.mmd`, and `diagrams/component.mmd` |
| SDD - threat model | 15 | `sdd/threat-model.md` maps controls to supply-chain, rogue-agent, and injection/outage incidents |
| SDD - rollout plan | 10 | `sdd/rollout-rollback.md` defines staged rollout, gates, and rollback triggers |
| Overall coherence | 10 | README and this SDD connect CI/CD, multi-agent logic, RAG, and capstone deployment |

### Weekly artifact lineage

| Prior artifact | Reference repository and demonstrated pattern | Capstone carry-forward and current gap |
|---|---|---|
| Case Study 1 — Zero-Trust CI/CD | [ai-model-explorer](https://github.com/KarthikBalaje/ai-model-explorer): Jenkins stages for tests, Docker build, Trivy image scanning, and image publishing. | `.github/workflows/ci.yml` runs tests and frontend build; Docker Compose builds local services. Container scanning, provenance, and image publishing are not yet implemented here. |
| Case Study 2 — Guardrailed multi-agent system | [fintech-market-intelligence-agent](https://github.com/KarthikBalaje/fintech-market-intelligence-agent): Researcher → Analyst → Reviewer workflow, execution-budget guardrail, and reviewer decision gate. | The Gmail planner uses deterministic classification/planning/review and a fail-closed policy; it does not run an autonomous loop, and cleanup actions remain disabled. |
| Case Study 3 — Monitored RAG | [knowledge-base-monitored-rag](https://github.com/KarthikBalaje/knowledge-base-monitored-rag): Weaviate retrieval, input sanitization, Phoenix traces, and retrieval-quality evaluation. | The capstone uses Weaviate/Ollama, untrusted-email handling, citation checks, and Phoenix instrumentation. Hybrid retrieval/evaluation and a portfolio-ready Phoenix screenshot remain gaps. |

The ADaSci template file was not present among the tracked repository files when this SDD was reviewed; this document follows the supplied assessment criteria and should be transferred into the official template if one is provided.

---

## 3. Five Production Layers

### Layer 1: DevOps and Runtime Orchestration

**Components**

- Master `docker-compose.yml`
- Service Dockerfiles
- GitHub Actions workflow
- Evidence directories

**Responsibilities**

- Run local microservices together.
- Keep external ports bound to localhost.
- Preserve repeatable test/build commands.
- Keep secrets and tokens outside Git.

**Current evidence**

- `docker compose config` renders successfully.
- Compose includes frontend, API gateway, agent service, Weaviate, and Phoenix.
- `.env`, token, credential, build, and cache files are ignored.

### Layer 2: API Gateway and Presentation

**Components**

- React frontend
- FastAPI API gateway
- Nginx frontend proxy

**Responsibilities**

- Provide the user-facing cleanup and RAG interface.
- Validate request shape and size.
- Forward cleanup planning and RAG requests to the agent service.
- Optionally fetch up to three Gmail metadata records using the read-only OAuth scope; body indexing is a separate explicit option.
- Terminate local browser requests through a single frontend origin.

**Key endpoints**

- `POST /cleanup/plan`
- `POST /cleanup/assist` (single-client-request cleanup plan plus RAG lookup)
- `POST /cleanup/plan/gmail`
- `POST /rag/index`
- `POST /rag/ask`
- `POST /gmail/rag/index`
- `GET /ready`

The current local verification results and the safe synthetic live-check procedure are recorded in `evidence/verification-report.md`. Live request/trace evidence remains outstanding.

### Layer 3: Guardrails and Agentic Logic

**Components**

- Agent service
- Cleanup planner
- Reviewer
- Deterministic guardrail policy

**Responsibilities**

- Build a cleanup review plan.
- Fail closed for protected or uncertain messages.
- Ensure planning is never authorization.
- Return `actions_executed: 0` for the current system.

**Implemented safety controls**

- Sent and draft messages are protected from cleanup modification.
- Work-related and personally protected messages cannot be trashed.
- Uncertain messages are kept for manual review.
- Trash requires explicit human approval in policy, but no write executor is enabled.

### Layer 4: Vector RAG

**Components**

- RAG ingestion and chunking.
- Ollama embedding endpoint.
- Weaviate vector database.
- Retrieval and grounded answer generation.
- Citation validation.

**Responsibilities**

- Normalize explicitly supplied or read-only Gmail-indexed records.
- Skip metadata-only records.
- Index chunks in Weaviate with caller-provided vectors.
- Retrieve relevant chunks by vector similarity.
- Generate answers using retrieved evidence only.
- Reject answers that do not cite valid provided source IDs.
- Return an insufficient-evidence response when no evidence exists.

**Current evidence**

- Automated tests cover chunk preparation, metadata-only skip, citation validation, and insufficient-evidence fallback.
- Live RAG evidence must be captured with sanitized input/output before final submission.

### Layer 5: Telemetry and Evidence

**Components**

- OpenTelemetry instrumentation in gateway and agent service.
- Phoenix dashboard.
- Evidence folders for logs, screenshots, and traces.

**Responsibilities**

- Show a request path through gateway and agent service.
- Support trace inspection in Phoenix.
- Preserve sanitized proof of service status, API readiness, tests, and UI.

**Current status**

- Instrumentation and Phoenix service are present.
- The isolated synthetic flow exported spans to Phoenix and the shared trace ID was verified; a sanitized Phoenix UI screenshot/export artifact is still outstanding.

---

## 4. End-to-End Flow

The composite `POST /cleanup/assist` request is designed to traverse (Gmail metadata/body indexing are opt-in and bounded to at most three Inbox messages):

```text
Client
  -> FastAPI gateway (/cleanup/assist)
  -> Gmail API (gmail.readonly; optional metadata and local indexing)
  -> Agent service /plan
  -> Planner and deterministic guardrails
  -> Agent service /rag/ask
  -> Ollama embedding request and Weaviate retrieval
  -> Ollama answer request (only when evidence exists)
  -> OpenTelemetry gateway/agent HTTP spans
  -> Phoenix dashboard
```

The composite endpoint makes two internal agent-service requests under one external client request. The plan remains dry-run only (`actions_executed: 0`); the related-context question defaults to the cleanup request unless a separate question is supplied. The agent service instruments its outgoing HTTP calls so vector-store and local model spans can join the request trace.

### Verification checklist

1. `docker compose config`
2. `docker compose up --build -d`
3. `docker compose ps`
4. `Invoke-RestMethod http://localhost:8000/ready`
5. `pytest -q -rs`
6. In an isolated test vector store containing synthetic records only, index synthetic data through `/rag/index`.
7. Send one synthetic request to `/cleanup/assist` and verify the dry-run plan plus RAG fallback/answer. Do not run this against a vector store that may contain private email unless you intend to review the resulting answer.
8. Capture a sanitized Phoenix UI screenshot/export showing the verified gateway, agent, vector-store, and Ollama HTTP spans.

---

## 5. C4 Architecture

The C4 diagrams are maintained as Mermaid files:

- `../diagrams/context.mmd`
- `../diagrams/container.mmd`
- `../diagrams/component.mmd`

They document:

- Users and external systems.
- Containers in the local deployment.
- Implemented request components for cleanup and RAG.
- Future write execution as out of scope.

---

## 6. Data and Trust Boundaries

| Boundary | Data crossing | Primary risks | Controls |
|---|---|---|---|
| Browser to gateway | User prompts, cleanup requests, RAG questions | Malformed input, unauthorized local access | Pydantic validation, localhost binding |
| Gateway to Gmail | OAuth token, metadata/body reads | Token exposure, excessive scope | `gmail.readonly`, external token path |
| Gateway to agent | Candidate metadata, RAG payloads | Policy bypass, oversized payloads | Request schemas and size limits |
| Agent to guardrails | Candidate facts and proposed action | Unsafe autonomous action | Deterministic policy outside LLM |
| Agent to Weaviate | Email chunks and vectors | Sensitive indexed data exposure | Local deployment, minimal metadata, evidence sanitation |
| Agent to Ollama | Retrieved snippets and question | Prompt injection, hallucination | Untrusted-content prompt, citation validation |
| Services to Phoenix | Traces and attributes | Sensitive telemetry leakage | Sanitized evidence and no token logging |

---

## 7. Security and Privacy Controls

- Gmail OAuth is read-only.
- Gmail write actions are not implemented.
- Cleanup planning does not fetch email bodies.
- RAG indexing is explicit and bounded.
- Attachments are not indexed.
- Retrieved email content is labeled untrusted in the answer prompt.
- Answers without valid source citations are rejected.
- `.env`, credentials, token files, traces, screenshots, and logs are excluded by default unless deliberately sanitized.

---

## 8. Testing and Evidence

Latest verified local result:

```text
18 passed
```

Test coverage includes:

- Guardrail policy behavior.
- Dry-run cleanup workflow.
- Protected-message bulk policy behavior.
- RAG chunk normalization.
- Insufficient-evidence fallback.
- Citation validation.

Evidence locations:

- `evidence/logs/pytest-results.txt`
- `evidence/logs/runtime-validation.txt`
- `evidence/screenshots/gmail-cleanup-planner.png`
- `evidence/traces/`

Required final evidence still to capture:

- Sanitized synthetic RAG live request/response summary and trace correlation: `evidence/verification-report.md`.
- Phoenix UI screenshot/export showing gateway, agent, vector-store, and Ollama spans (still outstanding).

---

## 9. Rollout Summary

The rollout plan is staged:

1. Local mock mode.
2. Read-only Gmail pilot.
3. Local RAG validation with sanitized data.
4. Observability evidence gate.
5. Future human-approved writes, only after new scopes, approval binding, audit persistence, and adversarial tests.

Rollback is documented in `rollout-rollback.md`. Any suspected unauthorized Gmail action or credential exposure triggers immediate disablement and credential containment.

---

## 10. Final Position

This repository is no longer a notebook demo. It is a local enterprise-style system with container orchestration, service boundaries, guardrails, RAG, telemetry instrumentation, architecture diagrams, and security documentation.

The system remains a read-only prototype. Its synthetic end-to-end RAG flow and Phoenix trace correlation have been verified and recorded; a UI screenshot/export and the remaining production-hardening controls are still outstanding.
