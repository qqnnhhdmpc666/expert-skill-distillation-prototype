# Skill Package Schema

日期：2026-06-04

## 1. 设计定位

本项目的最小方法核不是文件级 skill lifecycle，而是 rule-level evidence ledger。

区别在于：

```text
普通 lifecycle:
SKILL.md v1 -> SKILL.md v2 -> rollback

本项目:
rule atom -> material evidence / execution evidence / cost evidence
-> keep / compress / drop / patch / rollback
-> compact skill evolution
```

因此，`rule_ledger.json` 是 MVP 中最重要的结构化 artifact。它解释每条专家规则为什么被生成、保留、压缩、删除、补丁修正或回滚。

## 2. Artifact 列表

每次运行输出到：

```text
outputs/mvp_vertical_slice/<run_id>/
```

核心 artifact：

- `full_skill.md`：完整专家 skill，保留规则解释、证据、边界和审查语境。
- `evidence_map.json`：规则到材料证据的映射。
- `evidence_report.md`：面向人阅读的证据覆盖报告。
- `rule_ledger.json`：规则级证据账本和决策结果。
- `compact_skill_v1.md`：由初始 ledger 决策生成的轻量调用 skill。
- `execution_report_v1.json`：compact v1 执行结果和漏检规则。
- `repair_log.md`：执行反馈如何转成 rule-level patch。
- `compact_skill_v2.md`：由修正后 ledger 决策生成的轻量调用 skill。
- `execution_report_v2.json`：compact v2 执行结果。
- `cost_summary.json`：full / compact v1 / compact v2 的成本与效果对比。
- `manifest.json`：运行元数据和 artifact 清单。

## 3. Rule Ledger Schema

`rule_ledger.json` 是数组，每个元素对应一个 rule atom。

```json
{
  "rule_id": "R003",
  "rule_text": "APIs should provide stable error codes.",
  "category": "error_codes",
  "priority": "high",
  "source": "material_seed",
  "material_evidence": ["api_design_guidelines.md:Error Codes, line 13"],
  "material_status": "supported",
  "execution_status": "missed",
  "cost_status": "compact_keep",
  "decision_v1": "keep",
  "decision_v2": "keep",
  "decision_reason_v1": "High-priority supported rule retained in compact v1.",
  "decision_reason_v2": "Retained after execution because it remained task-critical.",
  "patches": []
}
```

字段含义：

- `rule_id`：稳定规则编号。
- `rule_text`：规则文本。
- `category`：规则类型。
- `priority`：`high | medium | low`。
- `source`：`material_seed | execution_patch | manual_seed`。
- `material_evidence`：材料证据引用。
- `material_status`：`supported | weak | unsupported | conflict`。
- `execution_status`：`not_observed | detected | missed | failure_critical | unused`。
- `cost_status`：`compact_keep | compact_drop | compact_patch | redundant | expensive`。
- `decision_v1`：`keep | compress | drop`。
- `decision_v2`：`keep | compress | drop | patch | rollback`。
- `decision_reason_v1`：v1 决策理由。
- `decision_reason_v2`：v2 决策理由。
- `patches`：执行反馈产生的 rule-level patch 记录。

## 4. 初始决策策略

MVP 的初始策略故意保守：

```text
if material_status == supported and priority == high:
    decision_v1 = keep
else:
    decision_v1 = drop
```

这会生成一个较轻的 `compact_skill_v1.md`。它不追求覆盖所有规则，而是先降低上下文成本。

## 5. 执行反馈修正规则

执行后，如果 compact v1 漏掉某条任务关键规则：

```text
if rule_id in execution_report_v1.missed_rules:
    execution_status = failure_critical
    cost_status = compact_patch
    decision_v2 = patch
```

如果 v1 已经检出某条规则：

```text
execution_status = detected
decision_v2 = keep
```

如果某条规则未触发：

```text
execution_status = unused
decision_v2 = decision_v1
```

## 6. 方法边界

当前 MVP 不声称完整自动优化，也不声称显著提升成功率。它只验证一个最小机制：

```text
材料证据决定初始 compact；
执行证据发现漏检；
成本证据约束 compact 大小；
rule ledger 解释每次 skill 改动。
```

这使系统区别于简单的“生成 skill + 执行验证 + token 统计”，因为每次变更都有 rule-level 证据理由。
