# account_admin 目标资产包

```python
@app.get("/admin/users")
def list_users(tenant_id: str):
    require_login()
    return db.query("select * from users where tenant_id=" + tenant_id)

@app.get("/users/{user_id}/profile")
def profile(user_id: str):
    return db.query("select email, phone from users where id=" + user_id)

def error_handler(exc):
    return {"message": "SQL syntax error near user_email=alice@example.com"}
```

```yaml
audit_log_retention_days: null
```
