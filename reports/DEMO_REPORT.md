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
| external LLM agent | RightCode GPT -> review.json -> verifier | 已完成 | 已用 `gpt-5.5` 跑通四组 matrix |

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

## 6. OpenAI-compatible LLM Agent Layer

新增 Harbor 外部 LLM agent：

```text
D:\solution\agents\api_review_llm_agent.py
```

新增四组 matrix runner：

```text
D:\solution\scripts\run_llm_agent_api_review_matrix.py
```

执行计划：

```text
case001 + compact_v1
case001 + compact_v2
case002 + compact_v1
case002 + compact_v2
```

输出目录：

```text
D:\solution\outputs\mvp_vertical_slice\llm_agent_api_review_001
```

当前配置：

```text
env_ready: true
OPENAI_BASE_URL: https://www.right.codes/codex/v1
MODEL: gpt-5.5
```

四组结果：

| Case | Variant | Model Output Rule IDs | Reward | Result |
|---|---|---|---:|---|
| case001 | compact_v1 | R001-R004 | 0.0 | missing R005 R006 |
| case001 | compact_v2 | R001-R006 | 1.0 | covers R001-R006 |
| case002 | compact_v1 | R001-R004 | 0.0 | missing R005 R006 |
| case002 | compact_v2 | R001-R006 | 1.0 | covers R001-R006 |

这一层证明：

- LLM agent 的 OpenAI-compatible 调用入口已经实现。
- prompt 会注入 compact skill 和 API case。
- 模型输出会经过 JSON fence 去除、首个 JSON object 提取和 findings 字段校验。
- 在 RightCode `gpt-5.5` 上，compact skill 的规则集合会影响真实模型输出。

边界：

```text
这一层是小样本增强证据，不是大规模稳定性结论。
它仍然不是两周 demo 的唯一成功路径。
```

## 7. 当前能对外说明什么

可以说明：

- 专家材料可以形成 full skill、evidence map 和 compact skill。
- compact skill 的生成由 rule-level decision 驱动，而不是随意摘要。
- Harbor verifier 的真实失败可以转换为统一 execution report。
- 执行失败可以回写到具体规则，并改变 compact skill v2。
- mock agent 已验证 `skill prompt -> review.json -> Harbor verifier` 的执行接口。
- OpenAI-compatible LLM agent 已使用 RightCode `gpt-5.5` 补跑，并复现 compact_v1 fail / compact_v2 pass。

不能过度说明：

- 不能说 `rule_ledger` 本身已经是强创新方法。
- 不能说当前策略已经在大规模任务上稳定优于 related work。
- 不能说 mock agent 等价于真实 LLM agent。
- 不能把四组小样本结果扩大成真实 LLM 大规模稳定性结论。

## 8. 下一步

## 8. Failure Taxonomy Expansion

新增第二个 failure-to-patch vertical slice：

```text
D:\solution\outputs\mvp_vertical_slice\output_format_error_001
```

该 case 构造了一个输出格式错误：`findings` 中缺少 `severity` / `evidence` 字段。verifier 返回：

```text
failure_type: output_format_error
affected_rule_ids: OUTPUT_CONTRACT
patch_action: rewrite_output_contract
```

这和已有的 missing_rule 路径不同：

| Failure Type | Example | Patch Target | Patch Action |
|---|---|---|---|
| missing_rule | compact v1 缺 R005/R006 | domain rule | patch_into_compact_v2 |
| output_format_error | findings 缺 severity/evidence | output contract | rewrite_output_contract |

边界：

```text
这是 taxonomy 的第二个 vertical slice，不是完整 failure taxonomy benchmark。
```

## 9. Policy Comparison

新增最小 compact decision policy 对比：

```text
D:\solution\outputs\mvp_vertical_slice\policy_comparison_001
```

当前三种策略：

| Policy | Selected Rules | Tokens | Within Budget | Checklist | Reward | Patch Needed |
|---|---|---:|---|---:|---:|---|
| priority-only | R001, R002, R003, R004 | 199 | true | 4 / 6 | 0.0 | true |
| risk-cost | R001, R002, R004, R005, R007 | 221 | true | 4 / 6 | 0.0 | true |
| execution-aware risk-cost | R001, R002, R003, R004, R005, R006 | 281 | false | 6 / 6 | 1.0 | false |

保守解释：

- `priority-only` 便宜，但漏掉 medium priority 的 execution-critical 规则。
- `risk-cost` 在预算内选择规则，但没有执行证据时仍可能漏掉 verifier 需要的规则。
- `execution-aware risk-cost` 加入历史失败证据后补齐 R005/R006，但代价是超过当前预算。
- 当前只是 exploratory comparison，case 数很少，不能说大规模优越。

## 10. 下一步

## 10. Counterfactual Patch Utility

新增方法探索支线：

```text
D:\solution\outputs\mvp_vertical_slice\counterfactual_patch_utility_001
```

目标不是再命名一个指标，而是验证一个机制假设：

```text
correct failure attribution + correct patch action
是否比 no patch / random patch / wrong type patch 更能解释 compact skill 修正有效？
```

当前 toy counterfactual 结果：

| Failure | Correct Patch | Result | Counterfactual Observation |
|---|---|---|---|
| missing_rule | `patch_into_compact_v2` | pass | no/random/wrong-type patch 均未恢复 R005/R006 |
| output_format_error | `rewrite_output_contract` | format failure resolved, full verifier still fails | wrong missing-rule patch 补了规则但没有解决输出格式错误 |

保守解释：

```text
当前 toy counterfactual 部分支持 failure-to-patch mapping 有解释价值。
它不能证明通用 patch compiler，也不是统计 benchmark。
```

## 11. 下一步

优先级 1：把 `run_demo_pipeline.py --check-existing` 作为演示前健康检查。

优先级 2：继续扩展 failure type，例如 `irrelevant_rule_interference`。

优先级 3：细化 policy comparison，让 budgeted policy 能在固定预算内更合理地权衡高风险规则和历史失败规则。
## 12. Method Discovery Loop: Fixed-Budget Compiler

新增方法探索支线：

```text
D:\solution\docs\METHOD_DISCOVERY_PLAN.md
D:\solution\scripts\run_fixed_budget_compiler.py
D:\solution\outputs\mvp_vertical_slice\fixed_budget_compiler_001
```

这个实验专门回答一个质疑：

```text
compact v2 是不是只是 prompt 变长了所以变好？
```

因此所有 policy 共用同一个 rule-token budget：

```text
token_budget: 237
compact_v1_rule_cost: 199
all_expected_rule_cost: 281
```

对比结果：

| Policy | Selected Rules | Tokens | Over Budget | Checklist | Failure-Critical Recovered | Missed Rules |
|---|---|---:|---|---:|---|---|
| priority-only | R001, R002, R003, R004 | 199 | false | 4 / 6 | none | R005, R006 |
| risk-cost | R001, R002, R004, R005, R007 | 221 | false | 4 / 6 | R005 | R003, R006 |
| execution-aware-fixed-budget | R001, R002, R004, R005, R006 | 223 | false | 5 / 6 | R005, R006 | R003 |

保守解释：

```text
fixed-budget execution-aware policy 部分支持 compiler 机制：
它没有超预算，并且确实把 R005/R006 换进 compact skill。
但它为了预算牺牲了 R003，因此没有完整通过 verifier。
```

这说明当前机制不是简单 append，但也还不是成熟的最优 compact compiler。

## 13. Method Discovery Loop: Rollback Gate

新增验证门控支线：

```text
D:\solution\scripts\run_rollback_gate.py
D:\solution\outputs\mvp_vertical_slice\rollback_gate_001
```

该 slice 构造了一个 toy patch：

```text
selected rules: R001, R002, R004, R005, R006
```

它的特点是：

```text
解决原始 affected rules: R005/R006
仍在预算内: 223 / 237
但丢掉 compact v1 已覆盖的 R003
```

validation gate 结果：

```text
resolves_original_failure: true
regression_detected: true
lost_previously_covered_rules: R003
over_budget: false
accepted: false
decision: reject_and_rollback
```

保守解释：

```text
这个 toy gate 说明 patch 不能因为解决局部失败就自动进入部署版本。
系统需要检查 regression、budget 和 failure-critical preservation。
但这仍然只是小型机制探针，不是成熟 rollback 系统。
```
## 14. Method Discovery Loop: Validation-Aware Compiler

新增 M2.1 支线：

```text
D:\solution\docs\VALIDATION_AWARE_COMPILER.md
D:\solution\scripts\run_validation_aware_compiler.py
D:\solution\outputs\mvp_vertical_slice\validation_aware_compiler_001
```

这个 slice 把 fixed-budget compiler 和 rollback gate 联动起来：

```text
failure feedback
-> fixed-budget recompilation
-> validation constraints
-> candidate compact skill
-> validation gate
-> accept / reject / rollback / infeasible
```

硬约束：

```text
must include R005/R006
must preserve R001/R002/R003/R004
must not exceed budget 237
```

候选结果：

| Candidate | Tokens | Validation | Covered | Missed | Interpretation |
|---|---:|---|---|---|---|
| candidate_A_naive_execution_aware | 223 / 237 | reject_regression | R001, R002, R004, R005, R006 | R003 | 补了 R005/R006，但丢掉 R003 |
| candidate_B_preserve_covered_first | 281 / 237 | reject_over_budget | R001-R006 | none | 原始规则全保留会超预算 |
| candidate_C_compressed_required_rules | 93 / 237 | accept | R001-R006 | none | 通过压缩表述满足约束 |
| candidate_D_infeasible_original_wording | 0 / 237 | infeasible | none | R001-R006 | 明确报告原始表述预算内不可行 |

保守结论：

```text
partially_supported
```

validation-aware fixed-budget recompilation 在 toy case 中可以避免上一轮的 R003 regression，但成功依赖 compressed wording。不能说已经证明通用 compact compiler。
## 15. Method Discovery Loop: Semantic-Preserving Compression Audit

新增 M2.2 支线：

```text
D:\solution\scripts\run_semantic_preservation_audit.py
D:\solution\scripts\verify_api_review_semantic_json.py
D:\solution\scripts\run_compressed_candidate_execution.py
D:\solution\outputs\mvp_vertical_slice\semantic_preservation_audit_001
D:\solution\outputs\mvp_vertical_slice\compressed_candidate_execution_001
D:\solution\outputs\mvp_vertical_slice\semantic_verifier_001
```

目标：

```text
验证 candidate_C_compressed_required_rules 不是 rule-id shortcut。
```

semantic audit 结果：

```text
overall_status: preserved
R001-R006 均包含 rule_id、触发短语、可执行检查动作和输出行为约束。
```

execution validation 结果：

| Agent | Case | Local Verifier | Semantic Verifier | Result |
|---|---|---|---|---|
| mock | case001 | pass | pass | semantic pass |
| mock | case002 | pass | pass | semantic pass |
| RightCode gpt-5.5 | case001 | pass | pass | semantic pass |
| RightCode gpt-5.5 | case002 | pass | pass | semantic pass |

当前结论：

```text
partially_supported
```

candidate_C 在当前 toy slice 中不是只靠 rule_id 过关；它的压缩文本保留了足够的检查语义，并能驱动 mock 和 RightCode GPT 输出通过轻量 semantic verifier。

边界：

```text
semantic verifier 只是字段 + 关键词触发检查，不是深层 NLP judge。
Compressed wording success 只有在 semantic-preservation 和 execution validation 都通过时才有意义。
否则它可能只是 verifier-contract weakness。
```
## 16. Method Discovery Loop: Skill-to-Agent Execution Protocol

新增 M5 支线：

```text
D:\solution\docs\SKILL_TO_AGENT_LOOP.md
D:\solution\scripts\verify_api_review_trace_json.py
D:\solution\scripts\run_skill_to_agent_loop.py
D:\solution\outputs\mvp_vertical_slice\skill_to_agent_loop_001
```

核心问题：

```text
compressed skill 进入 agent 后，agent 是否真的把规则应用到输入证据上？
```

对比三种输入：

```text
A. candidate_C_compressed_skill
B. rule_id_shortcut_skill
C. protocolized_compressed_skill
```

trace verifier 检查：

```text
findings 合法
rule_applications 合法
每个 finding 有对应 rule_application
rule_application 有 trigger_condition_found / evidence_span / finding_id / confidence
evidence_span 或 trigger_condition_found 与 case 相关
不能只是模板或 rule-id-only
```

当前结果：

| Agent | Variant | Simple/Semantic Coverage | Trace Verifier |
|---|---|---|---|
| mock | candidate_C_compressed_skill | pass | fail |
| mock | rule_id_shortcut_skill | pass | fail |
| mock | protocolized_compressed_skill | pass | pass |
| RightCode gpt-5.5 | candidate_C_compressed_skill | weak/fail under strict trace | fail |
| RightCode gpt-5.5 | rule_id_shortcut_skill | fail | fail |
| RightCode gpt-5.5 | protocolized_compressed_skill | pass | pass |

当前结论：

```text
partially_supported
```

structured skill-to-agent protocol 在 toy case 中能帮助区分“机械输出 rule_id”和“带有规则应用轨迹的输出”。

边界：

```text
这不是通用 agent protocol 证明，也不证明真实复杂任务正确性。
它只是说明：比起只看 rule_id coverage，rule_application trace 更接近我们想要的执行证据。
```
