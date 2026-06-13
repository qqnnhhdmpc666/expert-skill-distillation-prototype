# upload_service 目标资产包

```python
@app.post("/upload")
def upload(filename, content_type, file_bytes):
    if filename.endswith((".png", ".jpg")):
        save("/public/uploads/" + filename, file_bytes)
    return {"ok": True, "debug_path": "/public/uploads/" + filename}

@app.get("/download")
def download(filename: str):
    return send_file("/public/uploads/" + filename)
```

```yaml
debug: true
audit_log_retention_days: null
```
