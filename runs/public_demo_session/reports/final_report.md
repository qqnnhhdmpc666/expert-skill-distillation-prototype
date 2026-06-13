# 安全审查 Skill 运行报告

任务：文件上传服务安全审查
## 最终发现

### 输入校验
- 证据：filename, user_id, q 等用户可控字段直接进入处理流程。
- 风险：medium
- 修复：补充类型、长度、白名单与拒绝策略。

### 敏感信息泄露
- 证据：debug_path, stacktrace, token, api_key 暴露在返回或日志中。
- 风险：medium
- 修复：统一错误响应，并对路径、邮箱、token 和内部错误脱敏。

### 上传类型与存储隔离
- 证据：filename.endswith(...) 且写入 /public/uploads/。
- 风险：high
- 修复：联合检查 MIME、magic number、大小并使用非公开存储目录。

### 审计日志保留
- 证据：audit_log_retention_days: null。
- 风险：medium
- 修复：记录 actor/object/action/result/timestamp 并配置保留周期。

### 路径穿越
- 证据：save("/public/uploads/" + filename, file_bytes)
- 风险：high
- 修复：使用安全文件名、路径归一化和随机化存储名。

### 弱密钥与调试配置
- 证据：debug: true, SECRET_KEY: changeme。
- 风险：high
- 修复：关闭生产 debug，替换强密钥，并限制敏感配置暴露。
