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

## 5.1 评估维度

当前 demo 使用五个轻量评估维度，不声称已经完成大规模 benchmark：

| Dimension | Current Proxy | Artifact |
|---|---|---|
| Completeness | checklist coverage / missed rules | `comparison_summary.json` |
| Executability | pass / reward / verifier result | `execution_report_*.json`, `execution_report_spark.json` |
| Maintainability | rule-level repair log and patched ledger | `repair_log.md`, `repair_log_spark.md`, `rule_ledger_patched.json` |
| Cost-awareness | input tokens, compact ratio, patch token increase | `cost_summary.json`, `validation_gate.json` |
| Auditability | material evidence, rule decisions, source execution report | `evidence_map.json`, `rule_ledger.json`, `execution_report_spark.json` |

这些维度用于让两周 demo 更可解释；它们不是对 SkillNet / SkillCraft 等大规模评测工作的替代。

## 6. Execution Feedback Layers

当前已补充一个 SPARK-compatible feedback 闭环：

```text
compact_skill_v1
-> execution_report_spark.json
-> rule_ledger_patched.json
-> repair_log_spark.md
-> compact_skill_v2.md
```

输出目录：

```text
D:\solution\outputs\mvp_vertical_slice\spark_feedback_001
```

该闭环使用的失败输入目前是 fixture，不是真实 Harbor API review task。因此它证明的是接口行为：

```text
SPARK-compatible failure report
-> affected_rule_ids: R005, R006
-> rule_ledger patch
-> compact_skill_v2 content change
```

它还不能证明真实任务效果提升。

当前结果：

| Item | Value |
|---|---|
| failure_type | verifier_failure |
| affected_rule_ids | R005, R006 |
| patch_ready | true |
| full_skill_tokens | 1330 |
| compact_skill_v1_tokens | 265 |
| compact_skill_v2_from_spark_tokens | 315 |
| compact_v2_from_spark_ratio | 0.237 |
| validation_gate_accepted | true |
| token_increase_ratio | 0.189 |

保守解释：

- SPARK/Harbor 执行反馈现在不是独立日志，已经可以进入 rule-level patch 流程。
- 失败报告中的 affected rules 会改变 `rule_ledger_patched.json`。
- patched ledger 会进一步改变 `compact_skill_v2.md`。
- validation gate 会检查 affected rules 是否进入 v2，以及 token 增量是否低于阈值。
- fixture 层用于测试接口行为；真实 Harbor 层用于提升反馈可信度。

## 6.1 Feedback Source Maturity

当前已经完成前三层反馈来源：

| 阶段 | 反馈来源 | 可信度 | 当前状态 |
|---|---|---|---|
| Simulated baseline | 本地 deterministic evaluator | 低到中 | 已完成 |
| SPARK fixture | SPARK-compatible attempts / trajectory fixture | 中 | 已完成 |
| Harbor task | Docker / Harbor verifier 实际执行 | 高 | 已完成 |
| Real LLM + Harbor | 真实模型执行 + Harbor verifier | 最高 | 后续增强 |

真实 Harbor verifier 结果：

```text
compact_v1: reward = 0.0, missing R005 R006
compact_v2: reward = 1.0, covers R001-R006
```

对应闭环输出：

```text
D:\solution\outputs\mvp_vertical_slice\harbor_api_review_001
```

这说明当前失败反馈已经不只来自手写 fixture，而是由 Harbor verifier 在 Docker 执行环境中实际产生。

## 6.2 Holdout Case

已新增第二个真实 Harbor holdout case：

```text
D:\solution\data\harbor_api_review_tasks\api-review-002-compact-v1
D:\solution\data\harbor_api_review_tasks\api-review-002-compact-v2
```

case_002 使用不同 API 文本：

```text
POST /api/v1/orders/{order_id}/refund
```

真实 Harbor verifier 结果：

| Case | Variant | Reward | Verifier Result | Closed-loop Output |
|---|---|---:|---|---|
| api-review-001 | compact_v1 | 0.0 | missing R005 R006 | `harbor_api_review_001` |
| api-review-001 | compact_v2 | 1.0 | covers R001-R006 | `harbor_api_review_001` |
| api-review-002 | compact_v1 | 0.0 | missing R005 R006 | `harbor_api_review_002` |
| api-review-002 | compact_v2 | 1.0 | covers R001-R006 | `harbor_api_review_002` |

当前解释：

- 这不是大规模 benchmark。
- 但它说明同一组 compact / patch 机制不只在单一 API 文本上成立。
- 下一步才适合继续增加 failure type 或接 mock / scripted LLM agent。

## 7. 下一步

优先级 1：

新增 `api-review-002` holdout case，验证同一个 compact / patch 机制是否能复用到不同 API 文本。

优先级 2：

尝试 mock / scripted LLM agent，把 compact skill 注入 prompt 或上下文，再交给 Harbor verifier。

```text
missing_rule -> patch/add
weak_rule -> strengthen
output_format_error -> rewrite format
irrelevant_rule_interference -> prune
cost_heavy_unused_rule -> drop
```

优先级 3：

探索 risk-cost decision policy，让 compact skill 在 token budget 内保留 high-risk、execution-critical 和 verifier-critical rules。
