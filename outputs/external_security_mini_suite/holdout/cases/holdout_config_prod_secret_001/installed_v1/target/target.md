Task: Review this configuration defensively and keep production and dev-only findings separate.

Snippet:
prod.yaml: audit.enabled=true with retention_days/export_sink empty. dev.yaml: dev.api_token and dev.debug are present under a dev-only profile.

Requested output schema: capability_id, evidence_span, recommended_fix