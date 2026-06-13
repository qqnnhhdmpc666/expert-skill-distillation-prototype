app.py: upload() checks filename.endswith, writes UPLOAD_ROOT / filename, returns debug_path. config.yaml: audit_log_retention_days is empty.
