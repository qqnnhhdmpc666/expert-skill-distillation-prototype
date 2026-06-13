Task: Review this upload endpoint for defensive file-handling risks.

Snippet:
handler.py: validate_upload() allows filename.endswith('.jpg'), then writes UPLOAD_ROOT / filename into /public/uploads. settings.py: audit_log_retention_days is empty.

Requested output schema: capability_id, evidence_span, recommended_fix