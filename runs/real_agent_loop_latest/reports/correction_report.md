# 真实 Agent 闭环纠错报告

## 任务摘要

任务：审查一个文件上传服务，找出会影响真实用户安全的问题。

专家知识：
- 文件上传不能只检查扩展名，还要检查 MIME、内容魔数、大小、存储目录和执行权限。
- 用户可控文件名不能直接拼接到公开目录，必须做路径归一化和随机化存储名。
- 上传、下载、删除等高风险操作要有审计日志，并配置保留周期。
- 错误响应不能泄露内部路径、邮箱、token、api_key 或 stacktrace。

目标资产：
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
SECRET_KEY: changeme
```

期望输出：给出可执行的审查 Skill，并用它生成带证据和修复建议的审查报告。

## A1 verifier 反馈


## 修正策略

- 将缺失项写入 Skill v2 的 Evidence Protocol 和 Output Contract。
- 要求 agent 输出更具体的 evidence、improvements、limits。
- 重跑 A2，并保留完整 trajectory 和 model_calls 证据。

## A2 结果

- passed: True
- score: 1.0
- remaining missing: none