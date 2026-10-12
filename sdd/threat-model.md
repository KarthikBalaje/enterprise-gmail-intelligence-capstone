# Threat Model

**Project:** Enterprise Gmail Intelligence & Safe Inbox Cleaner  
**Status:** Read-only prototype with local RAG

## 1. Assets and Trust Boundaries

### Assets

- Gmail metadata and explicitly indexed email body text.
- OAuth client configuration and token files.
- Cleanup plans and policy decisions.
- Vector index contents.
- RAG answers and citations.
- Application logs, traces, screenshots, and evidence artifacts.
- Future approval and audit records.

### Trust boundaries

| Boundary | Threats | Controls |
|---|---|---|
| Browser to gateway | Malformed requests, unauthorized local access | Pydantic validation, localhost binding, bounded request sizes |
| Gateway to Gmail API | Token exposure, excessive permissions | `gmail.readonly`, external token storage, no write scopes |
| Gateway to agent service | Policy bypass, oversized payloads | Typed request schemas, service boundary |
| Agent to guardrails | Unsafe agent recommendations | Deterministic policy outside the model |
| RAG to Weaviate | Sensitive indexed data exposure | Local deployment, explicit indexing, minimal metadata |
| RAG to Ollama | Prompt injection, hallucination | Untrusted-content prompt, source citation validation |
| Services to telemetry | Sensitive logs/traces | Sanitized evidence, no token logging |

The current system is read-only and does not execute Gmail modifications.

---

## 2. Prior Incident Mapping 1: Supply-Chain Compromise

### Incident pattern

An enterprise AI pilot depends on compromised packages, container images, or unreviewed build steps. The system passes a demo but fails security review because dependency provenance, CI behavior, and secret handling are not documented.

### Project-specific impact

- Malicious dependency could read OAuth tokens or indexed email content.
- Compromised image could alter guardrail behavior.
- CI could leak secrets or produce unreviewed deployable artifacts.

### Implemented controls

- Service dependencies are declared in `requirements.txt` and `package-lock.json`.
- Dockerfiles isolate gateway, agent, and frontend builds.
- `.env`, OAuth tokens, credentials, logs, screenshots, and traces are ignored by default.
- GitHub Actions runs tests and frontend build checks.
- Docker Compose uses local services rather than unmanaged cloud dependencies.

### Remaining controls

- Pin all Python dependencies more tightly.
- Replace the floating Phoenix `latest` image with a reviewed immutable version or digest.
- Add dependency and container vulnerability scanning.
- Add secret scanning to CI.
- Preserve scan outputs as sanitized evidence.

### Verification evidence

- `git check-ignore .env`
- `.github/workflows/ci.yml`
- `docker compose config`
- `pytest -q -rs`

---

## 3. Prior Incident Mapping 2: Rogue Agent

### Incident pattern

An agent interprets a broad user goal as permission to take destructive action, bypass approval, or apply bulk modifications to protected records.

### Project-specific impact

- Important Gmail messages could be trashed or archived.
- Sent, draft, work-related, or personal messages could be modified.
- A future model-generated recommendation could be mistaken for authorization.

### Implemented controls

- Gmail OAuth scope is read-only.
- Gmail write executor raises at runtime and is not exposed as an API route.
- Cleanup planning returns `actions_executed: 0`.
- The planner keeps all current candidates and routes uncertain items to manual review.
- The guardrail policy blocks destructive actions for protected messages.
- Trash requires explicit human approval in policy, even though execution remains disabled.
- Tests cover protected, uncertain, and unapproved actions.

### Remaining controls before any write capability

- Add a separate write scope only after review.
- Persist approval records with message/action binding.
- Re-run policy at execution time.
- Add audit logs and idempotency controls.
- Add adversarial tests for bulk and prompt-manipulated requests.
- Add an emergency write-disable mechanism.

### Verification evidence

- `guardrails/policy_engine.py`
- `email-service/action_executor.py`
- `tests/unit/test_policy_engine.py`
- `tests/security/test_protected_email_actions.py`

---

## 4. Prior Incident Mapping 3: Prompt Injection / Outage

### Incident pattern

Email content or retrieved documents contain adversarial instructions, or a dependency outage causes unsafe fallback behavior. The model follows untrusted content, fabricates unsupported answers, or fails unclearly.

### Project-specific impact

- RAG could reveal sensitive content without grounding.
- Retrieved email could instruct the model to ignore policy.
- Weaviate or Ollama failures could produce misleading answers.
- Traces/logs could capture personal email content.

### Implemented controls

- Cleanup planning does not fetch message bodies.
- RAG indexing is an explicit read-only flow.
- Attachments are skipped.
- The answer prompt labels email text as untrusted data.
- The model is instructed to answer only from supplied evidence.
- Answers without valid source citations are rejected.
- Empty retrieval returns an insufficient-evidence response.
- Request sizes and retrieval limits are bounded.
- Weaviate is exposed only on localhost in the development Compose configuration; anonymous access remains enabled and is not acceptable for a shared or production deployment.

### Remaining controls

- Add live failure-mode evidence for unavailable Weaviate/Ollama.
- Add prompt-injection regression tests using synthetic malicious email content.
- Capture a sanitized Phoenix UI screenshot/export; the isolated synthetic run's trace metadata is recorded without email bodies or tokens.
- Add operational timeout and retry documentation.
- Require Weaviate authentication and transport protection before any non-local deployment.

### Verification evidence

- `rag-service/answer.py`
- `rag-service/ingestion.py`
- `tests/integration/test_rag_flow.py`
- `evidence/traces/` after final validation

---

## 5. Security Verification Summary

| Control | Current assessment |
|---|---|
| Gmail least-privilege OAuth | Implemented with `gmail.readonly` |
| No Gmail write execution | Implemented by omission and failing executor |
| Conservative cleanup policy | Implemented and tested |
| Source-grounded RAG answers | Implemented and tested with mocked model response |
| Insufficient-evidence fallback | Implemented and tested |
| Prompt-injection resilience | Partially implemented; more adversarial tests needed |
| Supply-chain hardening | Basic CI present; scanning still needed |
| Phoenix trace evidence | Instrumented and verified for an isolated synthetic flow; UI screenshot/export still required |
| Secret hygiene | `.env` ignored; do not inspect or commit secrets |

## 6. Acceptance Criteria Before Production

1. Complete dependency, container, and secret scanning.
2. Demonstrate sanitized end-to-end traces.
3. Demonstrate RAG indexing, retrieval, answer, and citations with sanitized records.
4. Confirm no Gmail write route is available in the read-only deployment.
5. Add approval persistence, audit logs, fresh policy checks, and emergency disable before any future write workflow.
6. Verify logs and traces do not include OAuth tokens or unnecessary personal email content.

**Final assessment:** the capstone system is ready to demonstrate read-only enterprise architecture patterns. It is not production-ready for Gmail modification workflows.
