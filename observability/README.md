# Observability

The gateway and agent service are instrumented with OpenTelemetry and configured to export traces to Phoenix at `http://phoenix:6006/v1/traces` inside Docker Compose.

Evidence requirements:

- Capture at least one request flowing through the API gateway and agent service.
- Prefer a RAG request for final assessment because it exercises gateway, agent logic, vector retrieval, model boundary, and telemetry.
- Save sanitized screenshots or exports under `evidence/traces/`.
- Do not capture OAuth tokens, credentials, full personal email bodies, or unsanitized message subjects in submitted evidence.

Useful local checks:

```powershell
docker compose ps
Invoke-RestMethod http://localhost:8000/ready
```

Phoenix is available at `http://localhost:6006` when the Compose stack is running.
