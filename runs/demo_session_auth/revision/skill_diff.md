--- Skill Package v1
+++ Skill Package v2
@@ -1,15 +1,23 @@
-# auth_security_review_skill v1
+# auth_security_review_skill v2
 
 - domain: 漏洞挖掘 / 鉴权与访问控制
-- status: 部署失败
-- token_cost: 127
+- status: 验证通过
+- token_cost: 259
 
 ## Rules
+- R001 权限与租户边界: 检查登录态、角色权限、租户隔离是否同时成立。
 - R002 用户输入校验: 检查用户可控参数是否有类型、长度、范围和 allowlist。
 - R003 SQL 注入: 检查用户输入是否拼接进入 SQL 查询。
 - R004 敏感信息泄露: 检查错误响应和日志是否暴露邮箱、token、密钥或内部错误。
+- R006 审计日志保留: 检查关键安全事件是否有审计日志和保留策略。
 
 ## Output Contract
 - finding_id
 - rule_id
 - evidence_span
+- risk_level
+- recommended_fix
+
+## Trace Policy
+- R001: rule_application -> evidence_span -> finding_id
+- R006: rule_application -> evidence_span -> finding_id