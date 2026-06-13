任务目标：
让 agent 检查一个文件上传接口中的上传类型、路径、敏感泄露和审计日志问题。

专家材料：
专家规则：
1. 上传接口必须校验扩展名、MIME 类型和内容魔数。
2. 文件名和存储路径必须防止路径穿越。
3. 错误响应不能泄露内部路径、邮箱、token 或 api_key。
4. 高风险上传、下载事件必须写入审计日志。

输出要求：
输出 finding_id、rule_id、evidence_span、risk_level、recommended_fix。

验证标准：
验证器检查规则覆盖率、输出 schema 完整性、evidence_span 是否来自目标资产。
