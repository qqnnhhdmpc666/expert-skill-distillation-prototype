Task: Review input validation defensively. This task family is intentionally outside the current secure_code_review package.

Snippet:
search.py: query is interpolated into a filter string, but no database dialect, sanitizer contract, or patch-validation context is provided.

Requested output schema: capability_id, evidence_span, recommended_fix