# custom_external_security_review_skill v2

- domain: 外部安全审查 / 自定义任务
- status: 验证通过
- token_cost: 321

## Rules
- R002 用户输入校验: 检查用户可控参数是否有类型、长度、范围和 allowlist。
- R004 敏感信息泄露: 检查错误响应和日志是否暴露邮箱、token、密钥或内部错误。
- R005 文件上传安全: 检查上传是否同时校验扩展名、MIME、内容魔数和隔离存储路径。
- R006 审计日志保留: 检查关键安全事件是否有审计日志和保留策略。
- R007 弱密钥与调试配置: 检查 debug=true、默认密钥、弱 JWT secret 和过宽 CORS。
- R008 路径穿越: 检查 filename/path 参数是否可写入非预期目录。

## Output Contract
- finding_id
- rule_id
- evidence_span
- risk_level
- recommended_fix

## Trace Policy
- R005: rule_application -> evidence_span -> finding_id
- R006: rule_application -> evidence_span -> finding_id
- R008: rule_application -> evidence_span -> finding_id

## Capability Track
- 将 外部安全审查 / 自定义任务 的专家经验转成可执行、可验证、可修正的 Skill Package。
- Keep findings grounded in target evidence.
- Repair only failure-critical gaps observed by the verifier.

## Behavior Boundary
- 仅用于受控 toy code / config / API 片段审查。
- 不连接真实目标，不执行漏洞利用，不宣称通用漏洞扫描能力。
- 当前外部输入会映射到受控规则库，用于演示蒸馏闭环。
