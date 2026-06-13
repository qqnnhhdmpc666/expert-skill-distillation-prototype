Task: Review this upload path defensively and return JSON findings only.

Snippet:
upload_service.py: save_upload() accepts report.pdf.jpg when filename.endswith('.jpg'), then writes UPLOAD_ROOT / filename. settings.toml: audit_log_retention_days is empty.

Requested output schema: capability_id, evidence_span, recommended_fix