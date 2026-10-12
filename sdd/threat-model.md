# Threat Model

**Project:** Enterprise Gmail Intelligence & Safe Inbox Cleaner  
**Status:** Prototype / Partial Implementation

## 1. Trust Boundaries and Assets

### Assets

- Gmail message metadata and email content.
- OAuth client configuration and access tokens.
- Human approval records.
- Vector index and indexed email data.
- Audit records, application logs, and distributed traces.
- Cleanup plans and policy decisions.

### Trust boundaries

| Boundary | Threats | Required controls |
|---|---|---|
| User browser to API gateway | Unauthorized requests, malformed input | Input validation, local service binding |
| API gateway to Gmail API | Token exposure, excessive permissions | Read-only OAuth scope, protected token storage |
| Gateway to agent service | Malformed or manipulated candidate data | Schema validation, bounded input |
| Agent to policy layer | Unsafe proposals, protected-email handling errors | Deterministic policy, fail-closed behavior |
| Email content to future LLM/RAG pipeline | Prompt injection, data leakage | Treat email as untrusted data, enforce policy outside the LLM |
| Application to vector store | Unauthorized retrieval, sensitive-data exposure | Access control, retention policy, data minimization |
| Application to logs and traces | Exposure of personal information or credentials | Redaction, restricted access, retention controls |

The current prototype uses read-only Gmail access and does not execute Gmail modifications. The RAG, persistent approval, and write-execution controls remain subject to implementation and verification.

---

## 2. Incident 1: Supply-Chain Compromise

### Threat and impact

A compromised package, malicious dependency update, or vulnerable container image could execute unauthorized code, expose OAuth tokens, access email metadata, or compromise the local development environment.

Potential impacts include credential theft, unauthorized data access, altered cleanup decisions, and compromise of application services.

### Preventive controls

**Implemented or observed**
- Dependencies are declared in service-specific requirements files.
- `.env` is excluded through `.gitignore`.
- OAuth configuration and token files are intended to remain outside the repository.
- Services run in Docker containers.

**Planned or requiring verification**
- Pin dependencies to reviewed versions and maintain reproducible lock files.
- Scan Python and frontend dependencies for known vulnerabilities.
- Scan container images and review base-image updates.
- Apply least privilege to container processes and mounted files.
- Verify that CI prevents secret leakage and blocks unacceptable vulnerabilities.

### Detection and verification

- Inspect dependency and container vulnerability scan reports.
- Review Git status and verify that secrets are not staged.
- Confirm that OAuth credentials and tokens are not present in logs or evidence.
- Verify that CI runs dependency and security checks.

Example repository checks:

```powershell
git status --short
git check-ignore .env
```

These commands verify repository state and ignore behavior; they do not prove the absence of every secret or vulnerability.

### Residual risk

Dependencies or container images may contain undiscovered vulnerabilities. The current project evidence does not establish that comprehensive supply-chain scanning, locked dependencies, or security gates are enforced.

### Link to the actual prior-week incident artifact

**Pending:** Add the path or URL of the actual Week 1/previous-week incident report supplied by the course. Do not invent an incident reference.

---

## 3. Incident 2: Rogue Agent

### Threat and impact

An agent may propose or attempt an unauthorized action because of a faulty classification, manipulated input, compromised model output, or missing authorization checks.

Potential impacts include deletion or modification of important email, exposure of sensitive information, and bulk actions outside the user's intent.

### Preventive controls

**Implemented or observed**
- Gmail OAuth access uses the read-only `gmail.readonly` scope.
- The current cleanup-plan workflow retrieves metadata without fetching message bodies.
- The tested workflow returns `actions_executed: 0`.
- Uncertain candidates default to `keep` and require manual review.
- The real Gmail action executor is intentionally disabled.
- Guardrail policy unit tests are passing.

**Required before enabling write operations**
- Enforce server-side authorization independently of agent recommendations.
- Protect sent messages, drafts, work-related email, and personally protected email.
- Require explicit human approval before every applicable destructive action.
- Re-evaluate policy immediately before execution.
- Limit bulk-action size and enforce idempotency.
- Maintain an auditable record of approvals and executed actions.
- Fail closed if policy evaluation or authorization fails.

### Verification

The latest recorded test run reports:

```text
12 passed, 3 skipped
```

The protected-email-action test is skipped because the real action executor is intentionally disabled.

The Gmail metadata dry-run was also verified with five candidates, zero actions executed, and approval required.

These results support the read-only workflow and current safety defaults. They do **not** demonstrate that a future write executor would safely reject every protected or unapproved action.

### Residual risk

A future implementation could introduce authorization bypasses, policy regressions, or unsafe behavior in bulk operations. Persistent approvals, a real action executor, and the associated security tests remain unimplemented.

### Link to the actual prior-week incident artifact

**Pending:** Add the path or URL of the actual incident report associated with the rogue-agent scenario.

---

## 4. Incident 3: Prompt Injection / Outage

### Threat and impact

An attacker may embed instructions in email content that attempt to override application rules, influence an LLM, expose sensitive data, or trigger unauthorized tool use.

Service outages or dependency failures may also cause requests to hang, fail unpredictably, or produce incomplete results.

Potential impacts include unsafe recommendations, sensitive-data leakage, denial of service, and misleading answers unsupported by retrieved evidence.

### Preventive controls

**Implemented or observed**
- The current cleanup-plan endpoint does not fetch message bodies.
- Uncertain classifications default to `keep`.
- The current workflow does not execute Gmail modifications.
- The application uses bounded input fields in the agent-service request schema.

**Required for future LLM/RAG functionality**
- Treat email content and retrieved documents as untrusted data, never as privileged instructions.
- Enforce authorization and cleanup policy outside the LLM.
- Prevent retrieved content from granting tool permissions or overriding system rules.
- Apply request timeouts, bounded retries, and concurrency limits.
- Fail safely when the model, vector store, or upstream API is unavailable.
- Return an explicit insufficient-evidence response when retrieval cannot support an answer.
- Redact sensitive email content from logs and traces.

### Verification

- The current metadata dry-run verified that message bodies are not fetched by the cleanup-plan endpoint.
- The current unit tests pass, but the RAG integration test is skipped because RAG is not implemented.
- Prompt-injection resistance, bounded retry behavior, timeout recovery, and grounded-answer quality have not been demonstrated by the current evidence.

Required future tests should include malicious instructions embedded in synthetic email content, model and vector-store failures, timeout behavior, and attempts to obtain answers unsupported by retrieved sources.

### Residual risk

Prompt injection remains a material risk for any future LLM/RAG integration. Resilience and recovery behavior also remain incompletely verified. The current prototype should not be represented as having proven prompt-injection resistance or production-grade outage handling.

### Link to the actual prior-week incident artifact

**Pending:** Add the path or URL of the actual prompt-injection or outage incident report supplied by the course.

---

## 5. Security Verification Summary

| Control or capability | Current evidence | Assessment |
|---|---|---|
| Gmail read-only scope | OAuth configuration and successful metadata workflow | Verified in current workflow |
| No Gmail modification in dry-run | `actions_executed: 0` | Verified in tested request |
| Uncertain candidates default to keep | Policy implementation and unit tests | Verified by current tests |
| Protected-email action execution | Action executor disabled; security test skipped | Not fully verified |
| RAG prompt-injection resistance | RAG integration not implemented | Not verified |
| Supply-chain vulnerability controls | Comprehensive scan evidence not provided here | Not verified |
| Secret exclusion from Git | `.env` ignore check passed | Partial verification only |
| Phoenix trace redaction and end-to-end propagation | End-to-end trace evidence not verified | Not verified |

## 6. Security Acceptance Criteria

Before considering this system for production use:

1. Verify the least-privilege OAuth configuration and secret-storage practices.
2. Demonstrate that no Gmail write operation is reachable in the read-only deployment.
3. Implement and test server-side authorization and human approval before enabling destructive actions.
4. Pass protected-email and unauthorized-action security tests.
5. Complete prompt-injection tests before enabling email content in an LLM/RAG pipeline.
6. Demonstrate safe behavior during Gmail API, model, vector-store, and telemetry failures.
7. Scan dependencies and container images and retain sanitized evidence.
8. Verify that logs and traces contain no OAuth tokens or unnecessary personal email content.
9. Link the three actual prior-week incident artifacts required by the course.

**Final assessment:** The current evidence supports a read-only Gmail metadata review prototype with conservative cleanup decisions. It does not establish production readiness, comprehensive supply-chain security, a safe write executor, or verified prompt-injection resistance.
