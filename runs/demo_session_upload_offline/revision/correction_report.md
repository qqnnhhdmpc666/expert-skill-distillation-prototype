# Skill 后验纠错报告

## 场景

文件上传漏洞检查

## 问题摘要

- A0 无 Skill：FAIL
- Skill v1：FAIL，缺失能力：文件上传安全、审计日志保留
- Skill v2：PASS，Gate：accept

## 后验反馈

Verifier 基于 A1 输出和验证契约发现报告缺少关键审查能力，因此触发后验修正。

## 修正动作

- missing_rule:R005 -> patch_rule: 补入 R005 文件上传安全
- missing_rule:R006 -> patch_rule: 补入 R006 审计日志保留
- output_contract_error -> rewrite_output_contract: 补齐 risk_level / recommended_fix / evidence_span
- failure_critical_rule -> add_trace_requirement: 对 R005, R006 要求 rule_application trace

## Skill v2 新增报告内容

- 文件上传安全: evidence=`# upload_service 目标资产包`; fix=同时校验扩展名、MIME、内容魔数，并隔离上传路径。
- 审计日志保留: evidence=`audit_log_retention_days: null`; fix=设置安全事件审计日志和保留策略。

## 目录级变化

```diff
~ SKILL.md -- 内容或契约发生变化
~ changelog.md -- 内容或契约发生变化
~ contracts/output_schema.json -- 内容或契约发生变化
~ manifest.yaml -- 内容或契约发生变化
~ meta.json -- 内容或契约发生变化
+ rules/R005_upload_type_and_storage.yaml -- v2 新增文件
+ rules/R006_audit_logging_retention.yaml -- v2 新增文件
~ trace_policy.yaml -- 内容或契约发生变化
```
