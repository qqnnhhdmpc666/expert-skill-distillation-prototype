# 当前进度对齐摘要

记录时间：2026-06-05 12:55（Asia/Shanghai）

## 1. 当前定位

当前项目主线是：

```text
基于专家材料的可验证 Skill 部署原型
```

最小闭环是：

```text
专家材料
-> full skill package
-> evidence map / rule ledger
-> compact skill v1
-> task execution / verifier feedback
-> rule-level patch
-> compact skill v2
-> cost/effect comparison
```

边界保持清楚：

- 不把 `rule_ledger.json` 过度包装成强创新方法。
- 不声称已经完成通用 skill lifecycle 或 self-evolution。
- 当前重点是让专家材料、执行反馈和成本约束进入同一套可复现 artifact 流。

## 2. 已完成内容

已完成第一层复现审查：

- `COLLEAGUE.SKILL` 和 `SPARK-PDI` 已下载到 `D:\solution\external_repos`。
- `COLLEAGUE.SKILL` 本地测试通过。
- SPARK / Harbor / Docker / uv 在 WSL2 中完成可运行验证。
- 已写入 `D:\solution\reports\REPRO_AUDIT.md` 和 `D:\solution\reports\ENV_SETUP_LOG.md`。

已完成 MVP vertical slice：

- `D:\solution\scripts\run_mvp_vertical_slice.py`
- `D:\solution\outputs\mvp_vertical_slice\baseline_001`

baseline 结果：

```text
no_skill: 0 / 6
full_skill: 6 / 6
compact_v1: 4 / 6
compact_v2: 6 / 6
```

已完成 SPARK / Harbor adapter：

- `D:\solution\integrations\spark\convert_spark_artifacts.py`
- `D:\solution\integrations\spark\convert_harbor_result.py`
- `D:\solution\integrations\spark\apply_spark_feedback.py`

已完成真实 Harbor verifier case：

- `D:\solution\outputs\mvp_vertical_slice\harbor_api_review_001`
- `D:\solution\outputs\mvp_vertical_slice\harbor_api_review_002`

case001 和 case002 均显示：

```text
compact_v1: reward = 0.0, missing R005 R006
compact_v2: reward = 1.0, covers R001-R006
```

## 3. 最新进展：Mock Agent Execution Layer

新增 mock/scripted API review agent：

```text
D:\solution\agents\api_review_mock_agent.py
```

它验证的执行接口是：

```text
compact_skill.md + case_openapi.md
-> review.json
-> Harbor verifier
-> execution_report_spark.json
-> rule_ledger patch
-> compact_skill_v2.md
```

新增 Harbor agent-mock task：

```text
D:\solution\data\harbor_api_review_tasks\api-review-agent-mock-001-compact-v1
D:\solution\data\harbor_api_review_tasks\api-review-agent-mock-001-compact-v2
```

运行结果：

```text
compact_v1 mock agent output: R001-R004
compact_v1 Harbor reward: 0.0
compact_v1 verifier: FAIL, missing R005 R006

compact_v2 mock agent output: R001-R006
compact_v2 Harbor reward: 1.0
compact_v2 verifier: PASS, covers R001-R006
```

闭环输出：

```text
D:\solution\outputs\mvp_vertical_slice\agent_mock_api_review_001
```

关键 artifact：

- `review_v1.json`
- `review_v2.json`
- `execution_report_spark.json`
- `execution_report_comparison.json`
- `rule_ledger_patched.json`
- `compact_skill_v2.md`
- `validation_gate.json`

## 4. 当前意义

现在系统已经从：

```text
预设 oracle review -> Harbor verifier
```

推进到：

```text
compact skill -> mock agent -> review.json -> Harbor verifier
```

这说明 compact skill 的内容会真实影响 agent 输出，并进一步影响 Harbor verifier 结果。这个阶段仍然不证明真实 LLM 的稳定性，但已经证明执行接口可以接入非预设答案的 agent 层。

## 5. 下一步

## 5. 最新进展：OpenAI-compatible LLM Agent 入口

新增 Harbor 外部 LLM agent：

```text
D:\solution\agents\api_review_llm_agent.py
```

新增四组 matrix runner：

```text
D:\solution\scripts\run_llm_agent_api_review_matrix.py
```

目标链路：

```text
compact_skill.md + case_openapi.md
-> OpenAI-compatible chat/completions
-> review.json
-> local verifier / Harbor verifier
```

当前 RightCode GPT 配置：

```text
OPENAI_BASE_URL: https://www.right.codes/codex/v1
MODEL: gpt-5.5
```

已生成真实 LLM 输出：

```text
D:\solution\outputs\mvp_vertical_slice\llm_agent_api_review_001
```

四组结果：

```text
case001 + compact_v1: R001-R004, reward 0.0, missing R005 R006
case001 + compact_v2: R001-R006, reward 1.0
case002 + compact_v1: R001-R004, reward 0.0, missing R005 R006
case002 + compact_v2: R001-R006, reward 1.0
```

当前意义：

- LLM agent 调用入口已完成。
- JSON 提取与基本校验已完成。
- 四组 case/skill matrix 已固定。
- RightCode `gpt-5.5` 已验证 compact skill 会影响真实模型输出。

边界：

```text
这一层还不能证明真实 LLM 在大规模任务中稳定完成任务。
它是增强层，不是当前 demo 主线的阻塞项。
```

## 6. 下一步

## 6. 最新进展：Demo Stability 与探索线

新增 demo 健康检查脚本：

```text
D:\solution\scripts\run_demo_pipeline.py
```

当前 `--check-existing` 输出：

```text
D:\solution\outputs\demo_pipeline_check\summary.json
D:\solution\outputs\demo_pipeline_check\summary.md
```

结果：

```text
overall_status: ok
baseline_001: ok
harbor_api_review_001: ok
harbor_api_review_002: ok
agent_mock_api_review_001: ok
llm_agent_api_review_001: ok
```

新增第二个 failure-to-patch vertical slice：

```text
D:\solution\outputs\mvp_vertical_slice\output_format_error_001
```

该 slice 展示：

```text
output_format_error
-> affected target: OUTPUT_CONTRACT
-> patch action: rewrite_output_contract
-> compact_skill_v2 adds JSON schema / required fields
```

新增 policy comparison：

```text
D:\solution\outputs\mvp_vertical_slice\policy_comparison_001
```

当前结果：

```text
priority-only: 199 tokens, 4/6, reward 0.0
risk-cost: 221 tokens, 4/6, reward 0.0
execution-aware-risk-cost: 281 tokens, 6/6, reward 1.0, exceeds budget
```

边界：

- output_format_error 是第二个 vertical slice，不是完整 taxonomy benchmark。
- policy comparison 是探索性对比，不是大规模实验结论。
- `execution-aware-risk-cost` 当前展示的是覆盖和成本之间的 tradeoff，不是免费改进。

## 7. 下一步

## 7. 最新进展：Counterfactual Patch Utility

新增方法探索支线：

```text
D:\solution\docs\METHOD_HYPOTHESIS.md
D:\solution\docs\METRIC_EXPLORATION.md
D:\solution\scripts\run_counterfactual_patch_utility.py
D:\solution\outputs\mvp_vertical_slice\counterfactual_patch_utility_001
```

核心问题：

```text
正确 failure attribution + 正确 patch action
是否比 no_patch / random_patch / wrong_type_patch 更能解释 compact skill 修正有效？
```

当前结果：

```text
missing_rule:
  no_patch / random_patch / wrong_type_patch 均失败
  compiler_patch 补 R005/R006 后通过

output_format_error:
  random_rule_patch / wrong_missing_rule_patch 仍保留 output_format_error
  output_contract_patch 解决格式错误，但仍可能存在业务规则缺失
  full_contract_patch 作为 upper bound 通过
```

当前结论标注：

```text
partially_supported
```

解释：

- 对 `missing_rule`，toy counterfactual 支持“正确归因 + 正确 patch action”有解释价值。
- 对 `output_format_error`，实验提醒我们要区分 `failure_resolved` 和 `verifier_passed`：格式问题可被解决，但完整任务仍可能因为缺规则失败。
- 这不是通用 patch compiler 证明，也不是 benchmark。

## 8. 下一步

优先级 1：保留 RightCode `gpt-5.5` 作为真实 LLM 增强证据；如果后续需要 DeepSeek 等其他模型，再接入新的 key 和 endpoint。

优先级 2：增加不同 failure type 的 case，例如 `output_format_error`、`irrelevant_rule_interference`。

优先级 3：比较 decision policy：

```text
priority-only
risk-cost
execution-aware risk-cost
```

优先级 4：整理 demo 脚本和架构图，为导师演示做准备。
## 9. 最新进展：Method Discovery Plan

新增方法探索计划文档：

```text
D:\solution\docs\METHOD_DISCOVERY_PLAN.md
```

当前不把已有系统包装成成熟方法，而是进入 method discovery loop。四个候选机制分别是：

```text
M1 failure-to-patch mapping
M2 fixed-budget compact skill compiler
M3 rollback / validation-gated revision
M4 evidence-grounded expert distillation
```

本轮优先推进 M2 和 M3，因为它们直接回应两个核心质疑：

```text
1. compact v2 是不是只是加长 prompt？
2. patch 会不会修好一个问题又破坏另一个问题？
```

## 10. 最新进展：Fixed-Budget Compiler 001

新增脚本和输出：

```text
D:\solution\scripts\run_fixed_budget_compiler.py
D:\solution\outputs\mvp_vertical_slice\fixed_budget_compiler_001
```

核心结果：

```text
token_budget: 237
priority-only: 199 tokens, 4/6, misses R005/R006
risk-cost: 221 tokens, 4/6, misses R003/R006
execution-aware-fixed-budget: 223 tokens, 5/6, recovers R005/R006, misses R003
```

当前解释：

```text
partially_supported
```

execution-aware policy 在固定预算内确实把 failure-critical 的 R005/R006 换了进来，不再是简单 append；但它为了预算牺牲 R003，所以还不能说已经形成成熟 compact compiler。

## 11. 最新进展：Rollback Gate 001

新增脚本和输出：

```text
D:\solution\scripts\run_rollback_gate.py
D:\solution\outputs\mvp_vertical_slice\rollback_gate_001
```

toy patch：

```text
R001, R002, R004, R005, R006
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

意义：

```text
这说明 repair loop 不应该自动接受所有 patch。
即使 patch 解决了 R005/R006，也可能因为丢失 R003 而被 gate 拒绝并回滚。
```

边界：

```text
这是 toy validation-gated revision slice，不是成熟 rollback 系统。
```
## 12. 最新进展：Validation-Aware Compiler 001

新增文档、脚本和输出：

```text
D:\solution\docs\VALIDATION_AWARE_COMPILER.md
D:\solution\scripts\run_validation_aware_compiler.py
D:\solution\outputs\mvp_vertical_slice\validation_aware_compiler_001
```

目标：

```text
把 fixed-budget compiler 和 rollback gate 联动起来。
compiler 不仅要补 R005/R006，还要避免破坏已覆盖的 R001-R004。
如果预算不够，要明确报告 infeasible。
```

候选结果：

```text
candidate_A_naive_execution_aware:
  223 / 237 tokens
  reject_regression
  misses R003

candidate_B_preserve_covered_first:
  281 / 237 tokens
  reject_over_budget

candidate_C_compressed_required_rules:
  93 / 237 tokens
  accept
  covers R001-R006

candidate_D_infeasible_original_wording:
  infeasible_under_budget
  required original rule cost 281 > budget 237
```

当前结论：

```text
partially_supported
```

解释：

```text
validation-aware recompilation 能避免 naive fixed-budget 的 R003 regression。
但当前成功依赖 compressed wording，不是原始 selector 自然成功。
```

边界：

```text
这是 toy case，不是通用 compact compiler 证明。
```
## 13. 最新进展：Semantic-Preserving Compression Audit

新增脚本和输出：

```text
D:\solution\scripts\run_semantic_preservation_audit.py
D:\solution\scripts\verify_api_review_semantic_json.py
D:\solution\scripts\run_compressed_candidate_execution.py
D:\solution\outputs\mvp_vertical_slice\semantic_preservation_audit_001
D:\solution\outputs\mvp_vertical_slice\compressed_candidate_execution_001
D:\solution\outputs\mvp_vertical_slice\semantic_verifier_001
```

核心问题：

```text
candidate_C 是 semantic compression，还是 rule-id shortcut？
```

审计结果：

```text
semantic_preservation_status: preserved
```

执行结果：

```text
mock + semantic verifier:
  case001 pass
  case002 pass

RightCode gpt-5.5 + semantic verifier:
  case001 pass
  case002 pass
```

当前结论：

```text
partially_supported
```

解释：

```text
candidate_C 在 toy case 中不只是保留 R001-R006 rule IDs。
它保留了简短但可执行的触发/检查语义，并且能驱动可用 agent 生成通过 semantic verifier 的 review.json。
```

边界：

```text
semantic verifier 仍然是轻量关键词/字段检查，不是深层语义 judge。
不能据此证明通用 fixed-budget compiler。
```
