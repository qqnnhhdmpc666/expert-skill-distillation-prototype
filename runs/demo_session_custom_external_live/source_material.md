任务目标：
让 agent 检查一个文件上传服务，识别扩展名/MIME/内容魔数校验不足、路径穿越、敏感调试路径泄露和审计日志缺失。

专家材料：
文件上传安全审查专家材料：
1. 上传接口不能只依赖 filename.endswith；必须同时校验扩展名、MIME 类型和内容魔数。
2. 文件名和存储路径必须做规范化，拒绝 ../ 等路径穿越输入。
3. 上传目录不能直接暴露为可执行或可公开枚举目录。
4. 错误响应不能泄露内部路径、邮箱、token、api_key 或 stacktrace。
5. 上传、下载等高风险文件操作必须写入审计日志，并定义保留策略。
6. 每个 finding 必须给出 affected endpoint、evidence_span、risk_level 和 recommended_fix。

输出要求：
输出 findings 数组；每个 finding 包含 finding_id、rule_id、evidence_span、risk_level、recommended_fix。

验证标准：
验证器检查是否覆盖上传校验、路径穿越、敏感信息泄露、审计日志保留；检查输出 schema 和 evidence_span；要求 Skill v2 能通过。
