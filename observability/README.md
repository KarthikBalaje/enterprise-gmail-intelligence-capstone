# Observability

Instrument gateway requests, policy decisions, agent steps, retrieval and executor outcomes.

- Propagate a request/correlation ID.
- Export spans to Arize Phoenix when instrumentation is configured.
- Use structured, sanitized logs.
- Do not log OAuth tokens or full email bodies by default.
- Capture a complete end-to-end trace and correlated logs for assessment evidence.

Phoenix integration is a follow-up implementation task; the current scaffold does not yet export traces.
