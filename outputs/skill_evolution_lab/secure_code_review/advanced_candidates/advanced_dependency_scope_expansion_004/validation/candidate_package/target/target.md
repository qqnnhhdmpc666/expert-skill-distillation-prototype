Task: Review dependency/version risk defensively. This task family is intentionally outside the current secure_code_review package.

Snippet:
requirements.txt: old-json-parser==1.2.0 is pinned, but no advisory database, exploitability context, or patch validation evidence is provided.

Requested output schema: capability_id, evidence_span, recommended_fix