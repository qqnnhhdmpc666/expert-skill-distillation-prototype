Task: Independently authored holdout: defensive upload review.

Snippet:
upload.py: accept() trusts file.name.endswith('.png') and stores uploads_dir / file.name. audit.retention_days is unset.

Requested output schema: capability_id, evidence_span, recommended_fix