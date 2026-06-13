Task: Review environment-specific security config and avoid overbroad findings.

Snippet:
prod.audit has retention_days/export_sink empty. dev.api_token and dev.debug are present only in a dev-only profile.

Requested output schema: capability_id, evidence_span, recommended_fix