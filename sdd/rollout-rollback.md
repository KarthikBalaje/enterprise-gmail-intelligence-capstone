# Rollout and Rollback Plan

**Project:** Enterprise Gmail Intelligence & Safe Inbox Cleaner  
**Status:** Local prototype — read-only Gmail workflow  
**Deployment:** Docker Compose

---

## 1. Rollout Strategy

The system will be rolled out in stages. Each stage must meet its acceptance criteria before proceeding to the next. Gmail write operations remain disabled until the security, authorization, and human-approval requirements are implemented and verified.

### Stage 1: Local Mock Mode

**Objective:** Validate the application using synthetic email candidates without connecting to Gmail.

**Configuration**
- Run the frontend, API gateway, and agent service locally through Docker Compose.
- Use synthetic candidate data.
- Keep Gmail OAuth and write access disabled for this stage.
- Validate deterministic guardrail behavior.

**Acceptance criteria**
- All applicable unit tests pass.
- Uncertain candidates default to `keep`.
- Protected-email policy tests pass.
- No Gmail modification endpoint is enabled.

**Current status:** The existing unit tests pass, but three tests are skipped. This stage should not be considered fully verified until the applicable skipped tests and configuration requirements are addressed.

### Stage 2: Read-Only Gmail Pilot

**Objective:** Validate Gmail metadata retrieval and conservative cleanup planning using an explicitly authorized test account.

**Configuration**
- Use OAuth with the `gmail.readonly` scope.
- Keep OAuth credentials and token files outside the repository.
- Retrieve message metadata only for the current cleanup-planning workflow.
- Keep Gmail write operations disabled.
- Route uncertain candidates to manual review.

**Acceptance criteria**
- OAuth authorization and metadata retrieval succeed.
- The granted scope is verified as read-only.
- A representative dry-run returns valid candidate records.
- `actions_executed` remains `0`.
- No email body is fetched by the cleanup-plan endpoint.
- Uncertain candidates default to `keep`.
- Personal data and credentials are excluded from submitted logs and screenshots.

**Current status:** The read-only Gmail metadata workflow has been demonstrated with five inbox candidates, zero actions executed, and approval required. RAG retrieval and grounded-answer validation are not complete.

### Stage 3: Human-Approved Writes

**Objective:** Introduce controlled Gmail modifications only after the required authorization and safety mechanisms have been implemented.

**Prerequisites**
- A separately reviewed Gmail write scope with the minimum required permissions.
- Server-side authorization independent of model or agent recommendations.
- Explicit human approval before applicable destructive actions.
- Fresh policy evaluation immediately before execution.
- Protected-email enforcement for sent, draft, work-related, and personally protected messages.
- Audit records for approval decisions and executed actions.
- Adversarial, regression, and integration tests.
- A documented emergency disable mechanism.

**Acceptance criteria**
- All mandatory security tests pass.
- Unapproved and protected actions are rejected.
- Approval cannot be reused for a different message or action.
- Failure of the authorization or policy service results in no action.
- Test evidence demonstrates that the emergency disable mechanism works.

**Current status:** Not implemented. Gmail write operations must remain disabled.

### Stage 4: Limited Cohort

**Objective:** Gradually introduce an approved write-enabled workflow to a limited, authorized user group after Stage 3 passes.

**Monitoring**
- Request error rate.
- Gateway and agent-service latency.
- Gmail API failures and quota errors.
- Policy rejections and uncertain classifications.
- Approval and execution outcomes.
- Trace-export failures.
- User-reported mistakes and incidents.

**Initial operational gates**

The following are proposed starting thresholds, not measured production baselines:

| Metric | Proposed gate |
|---|---|
| Unauthorized Gmail actions | Zero tolerated |
| Protected-email policy violations | Zero tolerated |
| Failed mandatory security tests | Zero |
| Unexpected destructive actions | Zero tolerated |
| API request error rate | Investigate sustained rates above 5% over a 5-minute window |
| Gateway/agent request latency | Investigate sustained p95 latency above 3 seconds over a 5-minute window |
| Trace-export failures | Investigate sustained failures; alerting requires implementation |

Tune performance thresholds after collecting a representative baseline. Any confirmed unauthorized action triggers immediate disablement of writes and incident review.

**Current status:** Not started.

---

## 2. Rollback Triggers

Initiate rollback or disable the affected capability when any of the following occurs:

1. A confirmed unauthorized Gmail action.
2. A protected message is modified unexpectedly.
3. An approval is bypassed, reused improperly, or cannot be verified.
4. A policy or authorization failure permits an unsafe action.
5. OAuth credentials or tokens are suspected to be exposed.
6. A deployed version causes a critical regression.
7. The application repeatedly produces unsafe or unverifiable decisions.
8. Required audit records cannot be generated or preserved.

For a confirmed unauthorized action, disable writes immediately. Preserve relevant evidence and investigate before re-enabling the capability.

---

## 3. Rollback Procedure

1. **Disable writes:** activate the emergency write-disable mechanism and prevent further Gmail modifications.
2. **Contain credentials:** revoke or reduce OAuth permissions when warranted. Rotate compromised credentials where appropriate.
3. **Restore the last known-good release:** roll back the application image and configuration to a verified version.
4. **Preserve evidence:** retain sanitized application logs, audit records, timestamps, request identifiers, and relevant trace data.
5. **Inspect Gmail state:** identify affected messages and determine which actions actually occurred.
6. **Reconcile changes:** restore or correct message state where possible and authorized. Do not assume that every Gmail change can be reversed.
7. **Investigate root cause:** review policy behavior, authorization, approval records, dependency changes, and deployment configuration.
8. **Verify recovery:** run regression, policy, integration, and applicable security tests.
9. **Re-enable cautiously:** require security review and documented approval before restoring write capability.

The emergency disable mechanism and the complete write rollback workflow must be implemented and tested before Stage 3 is approved.

---

## 4. Recovery Limitations

- Rolling back a container image does not undo changes already made in Gmail.
- Moving messages to Trash is not a guarantee of permanent recovery.
- OAuth revocation prevents future authorized access but does not reverse completed operations.
- Logs and traces may not contain enough information to reconstruct every change.
- Recovery may require manual reconciliation with Gmail state.
- Restoring the application does not restore an external vector index unless an appropriate backup exists.

A production rollout must define recovery-time objectives (RTO), recovery-point objectives (RPO), backup policies, and retention requirements.

---

## 5. Operational Verification

### Service status

```powershell
docker compose ps
```

### API readiness

```powershell
Invoke-RestMethod http://localhost:8000/ready
```

### Test suite

```powershell
pytest -q -rs
```

The current recorded result is **12 passed, 3 skipped**. The end-to-end cleanup workflow, RAG integration, and protected-email-action tests remain skipped; these are not passing acceptance evidence.

### Evidence locations

- Test results: `../evidence/logs/pytest-results.txt`
- UI screenshot: `../evidence/screenshots/gmail-cleanup-planner.png`
- Sanitized service logs: `../evidence/logs/`
- Verified traces: `../evidence/traces/`

Only add trace evidence after end-to-end trace propagation has been demonstrated.

---

## 6. Rollout Decision Record

| Stage | Status | Decision |
|---|---|---|
| Stage 1: Local mock mode | Partially verified | Address skipped tests and confirm mock-mode configuration |
| Stage 2: Read-only Gmail pilot | Demonstrated | Continue read-only validation; RAG remains incomplete |
| Stage 3: Human-approved writes | Not implemented | Do not enable write scopes or actions |
| Stage 4: Limited cohort | Not started | Block until Stage 3 security gates pass |

**Final decision:** Continue operating the current prototype in read-only mode. Do not enable Gmail write operations until the approval workflow, server-side authorization, audit trail, rollback controls, and mandatory security tests are implemented and verified.
