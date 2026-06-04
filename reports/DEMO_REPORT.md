# MVP Demo Report

日期：2026-06-04

## 1. 当前定位

本报告记录当前 deterministic MVP baseline。当前阶段不把 `rule_ledger.json` 夸成强创新方法，而是把它作为系统内部的统一决策表示。

本阶段目标是证明一个最小闭环可以跑通：

```text
专家材料
-> full_skill.md
-> evidence_map.json
-> rule_ledger.json
-> compact_skill_v1.md
-> execution_report_v1.json
-> repair_log.md
-> compact_skill_v2.md
-> cost/effect comparison
```

真正可能形成后续方法价值的是 ledger 上的 decision policy，例如 risk-cost policy、budgeted compact skill compiler、failure-to-patch taxonomy，而不是 ledger 文件本身。

## 2. Demo 场景

场景：

```text
API / 代码评审专家知识蒸馏
```

输入材料：

- `D:\solution\data\api_review_expert_materials\api_design_guidelines.md`
- `D:\solution\data\api_review_expert_materials\review_checklist.md`
- `D:\solution\data\api_review_expert_materials\historical_review_comments.md`

执行 case：

- `D:\solution\data\api_review_cases\case_001_openapi.md`

baseline 输出：

- `D:\solution\outputs\mvp_vertical_slice\baseline_001`

## 3. 四组对比

| Variant | Input Tokens | Passed | Checklist Pass | Missed Rules |
|---|---:|---|---:|---|
| no_skill | 0 | false | 0 / 6 | R001, R002, R003, R004, R005, R006 |
| full_skill | 1330 | true | 6 / 6 | none |
| compact_skill_v1 | 265 | false | 4 / 6 | R005, R006 |
| compact_skill_v2 | 339 | true | 6 / 6 | none |

## 4. 关键观察

`compact_skill_v1` 只保留高优先级且材料证据充分的规则，因此 token 约为 full skill 的 19.9%。它能检出 R001-R004，但漏掉 R005/R006。

执行反馈发现 R005/R006 是当前 case 的漏检规则后，`rule_ledger.json` 将它们标记为：

```text
execution_status = failure_critical
cost_status = compact_patch
decision_v2 = patch
```

随后 `compact_skill_v2` 将 R005/R006 补回，token 仍约为 full skill 的 25.5%，同时达到 6/6 checklist coverage。

## 5. 保守解释

这个 baseline 说明：

- 专家材料可以转成 full skill 和 evidence map。
- compact skill 可以由 rule-level 决策生成，而不是任意摘要。
- 执行失败可以回写到具体规则，并生成 repair log。
- v2 可以在仍明显小于 full skill 的情况下修复 v1 漏检。

它还不能说明：

- `rule_ledger` 本身是强新方法。
- 当前简单策略能在大规模任务上稳定优于已有工作。
- 当前 simulated execution 等价于真实 LLM/Harbor execution。

因此，当前最稳定位是：

```text
先完成可演示、可解释、可扩展的最小系统；
再在此基础上探索更强的 decision policy。
```

## 6. 下一步

优先级 1：

将 SPARK / Harbor 的 `attempts.json` 与 `trajectory.jsonl` 转换为统一 `execution_report.json`，替代或并联当前 simulated execution。

优先级 2：

实现更明确的 failure-to-patch taxonomy：

```text
missing_rule -> patch/add
weak_rule -> strengthen
output_format_error -> rewrite format
irrelevant_rule_interference -> prune
cost_heavy_unused_rule -> drop
```

优先级 3：

探索 risk-cost decision policy，让 compact skill 在 token budget 内保留 high-risk、execution-critical 和 verifier-critical rules。
