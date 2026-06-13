Task: Review dependency/version risk defensively. This task family is intentionally outside the current secure_code_review package.

Snippet:
requirements.txt: legacy-lib==0.9.1 is pinned, but no advisory database or patch validation context is available.

Requested output schema: capability_id, evidence_span, recommended_fix