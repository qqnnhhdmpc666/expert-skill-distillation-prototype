# Expert Skill v1

## Objective
Solve the user's task using the supplied expert knowledge and target asset. Do not treat the task as a generic summary request.

## Operating Protocol
1. Identify the concrete user goal, expert constraints, target asset, and expected output.
2. Produce findings or decisions with direct evidence from the target asset.
3. For every issue, include why it matters, how to fix it, and what assumption may change the conclusion.
4. Return a structured JSON object with `answer`, `evidence`, `improvements`, and `limits`.
5. Prefer specific, checkable statements over broad advice.

## Source Task Preview
任务目标：
根据专家知识，生成一个可执行的安全审查 Skill，并展示它在执行后如何被反馈修正。

专家材料：
- 高风险文件上传不能只看扩展名，要联合检查 MIME、内容魔数、大小和隔离存储。
- 用户可控文件名不能直接拼接到公开路径。
- 上传、下载、删除等高风险动作必须进入审计日志并设置保留周期。
- 错误响应不能暴露内部路径、token、api_key 或 stacktrace。

目标资产：
```python
@app.post("/upload")
def upload(filename, content_type, file_bytes):
    if filename.endswith((".png", ".jpg")):
        save("/public/uploads/" + filename, file_bytes)
    return {"ok": True, "debug_path": "/public/uploads/" + filename}
```

```yaml
debug: true
audit_log_retention_days: null
SECRET_KEY: changeme
```


