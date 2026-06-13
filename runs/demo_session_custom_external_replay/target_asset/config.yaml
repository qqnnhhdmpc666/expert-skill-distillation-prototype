# 用户提供的外部问题

```python
@app.post("/upload")
def upload(filename, content_type, file_bytes):
    if filename.endswith((".png", ".jpg")):
        save("/public/uploads/" + filename, file_bytes)
    return {"ok": True, "debug_path": "/public/uploads/" + filename}

@app.get("/download")
def download(filename):
    return send_file("/public/uploads/" + filename)
```

```yaml
audit_log_retention_days: null
```