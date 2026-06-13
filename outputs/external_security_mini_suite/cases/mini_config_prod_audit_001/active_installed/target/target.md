Task: Review this config defensively and separate production findings from dev-only settings.

Snippet:
prod.yaml: audit.enabled=true but retention_days/export_sink empty. dev.yaml: dev.api_token is set and dev.debug=true; these are marked dev-only.

Requested output schema: capability_id, evidence_span, recommended_fix