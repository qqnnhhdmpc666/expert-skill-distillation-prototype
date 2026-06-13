Task: Review this upload endpoint defensively.

Snippet:
media_upload.py: upload_media checks filename.endswith('.png'), writes UPLOAD_ROOT / filename, and serves files from /public/uploads. config.ini: audit_log_retention_days is empty.

Requested output schema: capability_id, evidence_span, recommended_fix