# Skill 后验纠错报告

## 场景

配置安全检查

## 问题摘要

- A0 无 Skill：FAIL
- Skill v1：FAIL，缺失能力：-
- Skill v2：PASS，Gate：accept

## 后验反馈

Verifier 基于 A1 输出和验证契约发现报告缺少关键审查能力，因此触发后验修正。

## 修正动作

- output_contract_error -> rewrite_output_contract: 补齐 risk_level / recommended_fix / evidence_span

## Skill v2 新增报告内容

- 无新增 finding

## 目录级变化

```diff
~ SKILL.md -- 内容或契约发生变化
~ changelog.md -- 内容或契约发生变化
~ contracts/output_schema.json -- 内容或契约发生变化
~ manifest.yaml -- 内容或契约发生变化
~ meta.json -- 内容或契约发生变化
```
