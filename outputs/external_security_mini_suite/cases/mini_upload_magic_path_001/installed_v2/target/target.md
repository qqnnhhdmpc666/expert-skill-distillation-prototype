Task: Review this upload handler defensively and return JSON findings only.

Snippet:
app.py: upload() checks filename.endswith, writes UPLOAD_ROOT / filename, and returns debug_path. config.yaml: audit_log_retention_days is empty.

Requested output schema: capability_id, evidence_span, recommended_fix