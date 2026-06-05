# MVP Demo Report

日期：2026-06-05

## 1. 当前定位

当前原型不声称已经提出通用 skill lifecycle、自演化框架或完整 cost-aware framework。更稳的定位是：

```text
基于专家材料的可验证 Skill 部署原型。
```

当前阶段的核心目标是跑通并展示一个最小闭环：

```text
专家材料
-> full_skill.md
-> evidence_map.json
-> rule_ledger.json
-> compact_skill_v1.md
-> 执行反馈
-> rule_ledger patch
-> compact_skill_v2.md
-> cost/effect comparison
```

`rule_ledger.json` 不是强创新本身，而是 MVP 的内部统一决策表示。真正值得后续探索的是 ledger 上的 decision policy，例如 risk-cost policy、budgeted compact skill compiler、failure-to-patch taxonomy。

## 2. Deterministic Baseline

输出目录：

```text
D:\solution\outputs\mvp_vertical_slice\baseline_001
```

四组对比：

| Variant | Input Tokens | Passed | Checklist Pass | Missed Rules |
|---|---:|---|---:|---|
| no_skill | 0 | false | 0 / 6 | R001, R002, R003, R004, R005, R006 |
| full_skill | 1330 | true | 6 / 6 | none |
| compact_skill_v1 | 265 | false | 4 / 6 | R005, R006 |
| compact_skill_v2 | 339 | true | 6 / 6 | none |

解释：

- `compact_skill_v1` 因成本约束只保留 R001-R004，因此 token 明显低于 full skill。
- 执行反馈发现 R005/R006 是漏检规则后，ledger 将二者标记为 `failure_critical` 和 `compact_patch`。
- `compact_skill_v2` 补回 R005/R006，在仍明显小于 full skill 的情况下恢复 6/6 checklist coverage。

## 3. Feedback Source Maturity

当前已经完成四层反馈来源：

| Layer | Feedback Source | Status | Meaning |
|---|---|---|---|
| deterministic baseline | 本地确定性 evaluator | 已完成 | 证明 artifact 闭环存在 |
| SPARK fixture | SPARK-compatible attempts / trajectory fixture | 已完成 | 证明 adapter 接口可用 |
| real Harbor verifier | Docker / Harbor verifier 实际执行 | 已完成 | 失败不再只是手写 fixture |
| mock agent + Harbor | compact skill -> mock review.json -> Harbor verifier | 已完成 | 证明执行接口不依赖预设 oracle review |

边界：

```text
mock agent 只验证执行接口，不证明真实 LLM 能稳定完成任务。
```

## 4. Real Harbor Verifier Cases

当前已经完成两个真实 Harbor verifier case：

| Case | Variant | Reward | Verifier Result | Closed-loop Output |
|---|---|---:|---|---|
| api-review-001 | compact_v1 | 0.0 | missing R005 R006 | `harbor_api_review_001` |
| api-review-001 | compact_v2 | 1.0 | covers R001-R006 | `harbor_api_review_001` |
| api-review-002 | compact_v1 | 0.0 | missing R005 R006 | `harbor_api_review_002` |
| api-review-002 | compact_v2 | 1.0 | covers R001-R006 | `harbor_api_review_002` |

这不是大规模 benchmark，但说明同一套 compact / patch 机制不只在单个 API 文本上成立。

## 5. Mock Agent Execution Layer

新增 mock/scripted API review agent：

```text
D:\solution\agents\api_review_mock_agent.py
```

执行接口：

```text
compact_skill.md + case_openapi.md
-> review.json
-> Harbor verifier
-> execution_report_spark.json
-> rule_ledger patch
-> compact_skill_v2.md
```

输出目录：

```text
D:\solution\outputs\mvp_vertical_slice\agent_mock_api_review_001
```

关键结果：

| Variant | Agent Output | Harbor Reward | Verifier Result |
|---|---|---:|---|
| compact_v1 | R001-R004 | 0.0 | missing R005 R006 |
| compact_v2 | R001-R006 | 1.0 | covers R001-R006 |

对应 artifact：

```text
D:\solution\outputs\mvp_vertical_slice\agent_mock_api_review_001\review_v1.json
D:\solution\outputs\mvp_vertical_slice\agent_mock_api_review_001\review_v2.json
D:\solution\outputs\mvp_vertical_slice\agent_mock_api_review_001\execution_report_spark.json
D:\solution\outputs\mvp_vertical_slice\agent_mock_api_review_001\execution_report_comparison.json
D:\solution\outputs\mvp_vertical_slice\agent_mock_api_review_001\validation_gate.json
```

当前 `validation_gate.json` 结果：

```text
accepted: true
affected_rule_ids: R005, R006
token_increase_ratio: 0.189
within_budget: true
```

## 6. 当前能对外说明什么

可以说明：

- 专家材料可以形成 full skill、evidence map 和 compact skill。
- compact skill 的生成由 rule-level decision 驱动，而不是随意摘要。
- Harbor verifier 的真实失败可以转换为统一 execution report。
- 执行失败可以回写到具体规则，并改变 compact skill v2。
- mock agent 已验证 `skill prompt -> review.json -> Harbor verifier` 的执行接口。

不能过度说明：

- 不能说 `rule_ledger` 本身已经是强创新方法。
- 不能说当前策略已经在大规模任务上稳定优于 related work。
- 不能说 mock agent 等价于真实 LLM agent。

## 7. 下一步

优先级 1：接一个真实或 OpenAI-compatible LLM agent，小心控制不稳定性。

优先级 2：新增不同 failure type 的 case，例如 `output_format_error` 或 `irrelevant_rule_interference`。

优先级 3：开始比较 decision policy，例如 priority-only、risk-cost、execution-aware risk-cost。
