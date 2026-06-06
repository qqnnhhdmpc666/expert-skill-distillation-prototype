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
## 14. 最新进展：Skill-to-Agent Execution Protocol

新增 M5 方法探索支线：

```text
D:\solution\docs\SKILL_TO_AGENT_LOOP.md
D:\solution\scripts\verify_api_review_trace_json.py
D:\solution\scripts\run_skill_to_agent_loop.py
D:\solution\outputs\mvp_vertical_slice\skill_to_agent_loop_001
```

要解决的问题：

```text
compressed skill 不能只靠 rule_id coverage 证明正确。
需要让 agent 暴露 rule application trace，证明规则确实被应用到 case 证据上。
```

对比组：

```text
candidate_C_compressed_skill
rule_id_shortcut_skill
protocolized_compressed_skill
```

当前观察：

```text
mock:
  candidate_C / shortcut 可过简单覆盖，但 trace verifier 失败
  protocolized compressed skill 通过 trace verifier

RightCode gpt-5.5:
  candidate_C / shortcut 在 strict trace 下失败
  protocolized compressed skill 在 case001/case002 通过 trace verifier
```

结论：

```text
partially_supported
```

解释：

```text
structured skill-to-agent protocol 在当前 toy case 中能区分 rule-id shortcut 和带证据链的规则应用。
```

边界：

```text
这不是通用 agent protocol，也不证明真实复杂任务正确性。
它是 M5 的最小机制探针。
```
## 15. 最新进展：Traceable Compact Compiler Integration

新增 M2/M3/M5 integration 文档、脚本和输出：

```text
D:\solution\docs\TRACEABLE_COMPACT_COMPILER.md
D:\solution\scripts\run_traceable_compiler_integration.py
D:\solution\outputs\mvp_vertical_slice\traceable_compiler_integration_001
```

这一步不是新增机制候选，而是把已有三条线合并：

```text
M2 fixed-budget rule selection / compression
M3 validation gate / rollback
M5 skill-to-agent invocation protocol / trace verifier
```

统一后的部署产物是：

```text
compact skill rules
+ invocation protocol
+ trace verifier contract
```

四组对比结果：

```text
A plain compact skill:
  simple/semantic/trace 均失败，missing R005/R006

B compressed compact skill:
  simple/semantic 通过
  trace 失败

C compressed compact skill + protocol:
  simple/semantic/trace 通过
  但 token 总成本 300 / 237，超预算

D compressed compact skill + protocol + validation gate:
  trace 通过
  但被 gate 正确 reject_over_budget
```

当前结论：

```text
partially_supported_with_protocol_overhead
```

意义：

- trace verifier 可以阻止 shallow output / rule-id shortcut。
- protocol 让 agent 暴露 rule_application trace，有助于证明规则确实被应用。
- 但当前 protocol overhead 不可忽略，不能直接说已经得到低成本部署版本。
- validation gate 拒绝超预算 candidate 是成熟表现，而不是失败。

下一步如果继续该线，优先不是新增机制，而是压缩/外置/摊销 invocation protocol，让 traceability 变得更便宜。
## 16. 最新进展：Real Effect Evaluation Line

新增小型 controlled holdout：

```text
D:\solution\data\api_review_holdout_cases
D:\solution\scripts\run_real_effect_eval.py
D:\solution\outputs\mvp_vertical_slice\real_effect_eval_001
```

这一步回答：

```text
专家 skill 是否真的让 agent 在任务行为上做得更好？
```

当前 4-case controlled holdout 结果：

```text
no_skill:
  avg coverage 0.25
  pass@1 1/4
  critical misses 5

compact_v1:
  avg coverage 0.58
  pass@1 1/4
  critical misses 1

patched_compact:
  avg coverage 1.00
  pass@1 4/4
  critical misses 0

patched_compact_selective_trace:
  avg coverage 1.00
  pass@1 4/4
  critical misses 0
```

当前结论：

```text
partially_supported
```

意义：

- 系统现在不只验证 artifact 闭环，也开始检查 skill-conditioned deployment 的任务效果。
- 结果支持 patched compact 在当前 controlled family 上改善 API-review 行为。
- 这不是 benchmark，也不能说成真实复杂任务泛化证明。

## 17. 最新进展：Selective / Risk-Budgeted Trace Line

新增 selective trace slice：

```text
D:\solution\scripts\run_selective_trace_compiler.py
D:\solution\outputs\mvp_vertical_slice\selective_trace_compiler_001
```

这一步回答：

```text
traceability 有成本时，trace 应该花在哪些规则上？
```

当前结果：

```text
no_trace:
  140 / 237 tokens
  shortcut_blocked=false
  accepted

full_trace:
  300 / 237 tokens
  shortcut_blocked=true
  reject_over_budget

selective_trace_failure_critical:
  trace R005/R006
  183 / 237 tokens
  shortcut_blocked=true
  accepted

selective_trace_high_risk_or_patched:
  trace R001/R003/R005/R006
  186 / 237 tokens
  shortcut_blocked=true
  accepted
```

当前结论：

```text
partially_supported
```

意义：

- full trace 有用但贵。
- no trace 便宜但不能阻止 shortcut。
- selective trace 在 toy slice 中能把可验证性成本集中到 failure-critical / high-risk 规则上。

当前更成熟的项目表述可以是：

```text
risk-budgeted traceable skill deployment prototype
```

或：

```text
correctness-constrained expert skill deployment optimization
```

## 18. 最新进展：主线收束与 Claim Audit

当前方法探索主线已经收束为：

```text
risk-budgeted traceable skill deployment prototype
```

也可以保守表述为：

```text
correctness-constrained expert skill deployment optimization
```

统一逻辑链：

```text
expert material
-> evidence-grounded full skill
-> compact deployment skill
-> verifier feedback
-> patch proposal
-> validation gate
-> agent output
-> selective trace for high-risk / failure-critical rules
-> trace verifier checks rule-application evidence
```

新增 claim audit：

```text
D:\solution\scripts\run_artifact_claim_audit.py
D:\solution\outputs\mvp_vertical_slice\artifact_claim_audit_001
```

审计覆盖核心 artifact：

```text
baseline_001
harbor_api_review_001 / 002
llm_agent_api_review_001
output_format_error_001
counterfactual_patch_utility_001
fixed_budget_compiler_001
rollback_gate_001
validation_aware_compiler_001
semantic_preservation_audit_001
skill_to_agent_loop_001
traceable_compiler_integration_001
real_effect_eval_001
selective_trace_compiler_001
```

当前审计结果：

```text
status: ok
missing_artifacts: []
```

安全主张：

```text
The prototype demonstrates a risk-budgeted traceable skill deployment loop in a controlled API-review family: expert materials become evidence-grounded skills, verifier feedback drives patch proposals, validation gates prevent regression or over-budget deployment, and selective trace focuses rule-application evidence on high-risk rules.
```

明确不能说：

- 不能说已经证明通用正确性。
- 不能说优于 related work。
- 不能把 4-case holdout 叫 benchmark。
- 不能把 selective trace 叫成熟 tracing strategy。
- 不能把当前系统叫 mature skill compiler。

## 19. 最新进展：Related-Work Delta 与仓库成熟度审计

新增：

```text
D:\solution\docs\RELATED_WORK_DELTA_AUDIT.md
D:\solution\docs\COMPONENT_BASELINE_PLAN.md
```

这一步不只比较机制，也比较仓库工程成熟度。

当前仓库体征对比：

```text
ours:
  122 source/doc/config files excluding outputs/external_repos
  28 Python files
  ~6.7k Python LOC
  no pyproject / no CI / script-first

SPARK-PDI:
  239 files
  29 Python files
  ~9.5k Python LOC
  pyproject + uv.lock + ruff/mypy config
  package-like research pipeline

COLLEAGUE.SKILL:
  108 files
  30 Python files
  ~8.1k Python LOC
  tests + install docs + contribution docs + host installers
  product-like skill artifact tooling
```

当前判断：

```text
我们不是空壳草稿；代码和 artifact 已经有一定规模。
但工程成熟度还不是 SPARK/COLLEAGUE 级别。
```

我们的当前优势：

- artifact discipline 强；
- vertical slices 多且可复现；
- demo loop 覆盖 material -> skill -> compact -> agent -> verifier -> patch -> gate -> trace；
- claim audit 已经明确每个 artifact 能支撑什么。

我们的当前短板：

- script-first，缺少 package/API；
- `src/` 尚未形成核心库；
- 缺少 formal unit tests；
- 缺少 typed schemas；
- 缺少 pyproject/dependency lock/CI；
- 一些标准在文档里写清楚了，但还没有被代码强制执行。

安全表述：

```text
The repository is currently a reproducible research/demo prototype, not yet a mature open-source platform.
```

后续如果要提升成熟度，优先方向是：

```text
move reusable logic into src/
define schemas
add CLI
add tests
add pyproject/ruff/CI
turn component baseline plan into runnable ablation
```

## 20. 最新进展：Repository Maturity Patch

新增最小工程骨架：

```text
D:\solution\pyproject.toml
D:\solution\src\skill_deployment
D:\solution\tests
D:\solution\scripts\validate_task_cases.py
D:\solution\scripts\skill_deploy.py
D:\solution\docs\REPOSITORY_MATURITY_PATCH_PLAN.md
```

抽取的稳定逻辑：

- `TaskCase` schema 和 loader；
- token budget check；
- artifact manifest check；
- validation gate result helper；
- partial trace verifier helper；
- lightweight CLI wrapper。

新增快速测试：

```text
test_task_case_schema.py
test_validation_gate.py
test_trace_verifier.py
test_token_budget.py
test_artifact_manifest.py
```

验证结果：

```text
python -m pytest: 11 passed
python scripts\validate_task_cases.py: status ok
python scripts\skill_deploy.py check-existing: overall_status ok
```

当前成熟度判断更新：

```text
仓库已经从 pure script-first demo 往 minimal package/schema/test skeleton 推进了一步。
但仍不是 mature open-source platform。
```

## 21. 最新进展：Component Baseline Direct Summary

新增 component attribution slice：

```text
D:\solution\scripts\run_component_baseline_eval.py
D:\solution\outputs\mvp_vertical_slice\component_baseline_direct_summary_001
```

目标：

```text
检查普通 direct-summary skill 是否已经足够覆盖受控 API-review family。
这用于解释结构化 rule / patch / gate / trace 各组件的实际增量，而不是做 benchmark。
```

当前结果：

```text
direct_summary_skill: avg coverage 0.92, pass@1 3/4, avg total tokens 263.0
full_skill: avg coverage 1.00, pass@1 4/4, avg total tokens 1429.8
compact_v1: avg coverage 0.58, pass@1 1/4, avg total tokens 323.5
patched_compact: avg coverage 1.00, pass@1 4/4, avg total tokens 438.8
patched_compact_selective_trace: avg coverage 1.00, pass@1 4/4, avg total tokens 335.0
```

当前解释：

```text
direct summary 在这个小型受控场景里并不弱，它能覆盖大部分高显著规则。
因此我们的价值不能说成“普通总结不会生成 checklist”。
更稳的价值是：verifier feedback 找到 direct summary / compact skill 容易遗漏的长尾或 failure-critical 规则，再通过 patch、validation gate 和 selective trace 控制部署风险。
```

边界：

```text
这是 deterministic component attribution slice，不是 benchmark，也不证明我们已经普遍优于 direct-summary skill generation。
```

## 22. 最新进展：Core Method Spec 与 Risk Trace Policy Baseline

新增核心方法规格文档：

```text
D:\solution\docs\CORE_METHOD_SPEC.md
```

当前主张收束为：

```text
Skill deployment needs risk-budgeted verification, not just better summarization.
```

中文表述：

```text
专家 skill 部署需要按风险分配验证成本，而不是只追求生成阶段的总结质量。
```

新增 risk-vs-random selective trace baseline：

```text
D:\solution\scripts\run_risk_trace_policy_baseline.py
D:\solution\outputs\mvp_vertical_slice\risk_trace_policy_baseline_001
```

对比组：

```text
no_trace
full_trace
random_selective_trace
risk_based_selective_trace
```

当前结果：

```text
no_trace:
  140 / 237 tokens
  failure-critical trace coverage 0.00
  shortcut_blocked false
  gate accept

full_trace:
  300 / 237 tokens
  failure-critical trace coverage 1.00
  shortcut_blocked true
  gate reject_over_budget

random_selective_trace:
  traced R002/R003
  183 / 237 tokens
  failure-critical trace coverage 0.00
  shortcut_blocked true
  gate accept

risk_based_selective_trace:
  traced R005/R006
  183 / 237 tokens
  failure-critical trace coverage 1.00
  shortcut_blocked true
  gate accept
```

当前解释：

```text
partially_supported
```

含义：

```text
在同样 trace 2 条规则、同样 183/237 token 成本下，risk-based trace 把可验证性预算分配到 failure-critical rules，而 fixed-seed random trace 没有做到。
```

边界：

```text
这是 toy baseline，只有一个 random seed 和很小的 rule pool。random trace 可能偶然命中关键规则，所以不能说已经统计验证 risk policy。
```

## 23. 最新进展：Risk Trace Robustness 与 Direct Summary Miss Analysis

新增 risk trace robustness 枚举：

```text
D:\solution\scripts\run_risk_trace_policy_robustness.py
D:\solution\outputs\mvp_vertical_slice\risk_trace_policy_robustness_001
```

目标：

```text
不只依赖一个 random seed，而是在当前 R001-R006 规则池内枚举所有 size=2 trace 组合。
```

当前结果：

```text
total_combinations: 15
full_failure_critical_coverage_count: 1
partial_failure_critical_coverage_count: 8
zero_failure_critical_coverage_count: 6
risk_based_selective_trace: R005/R006, coverage 1.00, 183/237 tokens
previous_random_seed_4: R002/R003, coverage 0.00, 183/237 tokens
```

当前解释：

```text
partially_supported
```

含义：

```text
在当前 toy rule pool 中，R005/R006 是唯一能完整覆盖 failure-critical rules 的 size=2 trace allocation。
这比单个 random seed 对照更稳，但仍不是统计显著性验证。
```

新增 direct summary miss analysis：

```text
D:\solution\scripts\run_direct_summary_miss_analysis.py
D:\solution\outputs\mvp_vertical_slice\direct_summary_miss_analysis_001
```

当前结果：

```text
failed_case_id: case004_validation_sensitive_idempotency
missed_rule_ids: R006
missed rule: idempotency / duplicate submission behavior
patched_compact: recovers R006 and passes
```

当前解释：

```text
direct summary 并不弱，它只漏了一个 medium-priority 但 deployment-critical 的 R006。
这支持“deployment-time residual failure recovery”的主线，而不是“direct summary 不会生成 checklist”的主线。
```

边界：

```text
这是解释性 evidence，不是 general long-tail failure proof。
```

新增 falsification 文档：

```text
D:\solution\docs\FALSIFICATION_AND_NEXT_EVIDENCE.md
```

作用：

```text
明确当前核心 claim 在什么条件下会变弱或被推翻，以及下一步优先收集什么证据。
```

## 24. 最新进展：Risk Signal Taxonomy 与 Adversarial Trace Verifier

新增 risk signal taxonomy：

```text
D:\solution\docs\RISK_SIGNAL_TAXONOMY.md
```

核心边界：

```text
当前系统主要支持 post-execution risk-budgeted verification。
也就是 verifier feedback 暴露 residual failure 后，系统把 patch / gate / trace 预算集中到 failure-critical 或 newly patched rules。
当前还不能声称已经证明 pre-execution risk prediction。
```

新增 adversarial trace verifier sanity check：

```text
D:\solution\scripts\run_adversarial_trace_verifier.py
D:\solution\outputs\mvp_vertical_slice\adversarial_trace_verifier_001
```

当前结果：

```text
valid control: pass
fake_evidence_span: reject
generic_trigger: reject
mismatched_finding_id: reject
rule_id_only_trace: reject
```

本轮还补强了：

```text
D:\solution\scripts\verify_api_review_trace_json.py
```

新增检查：

```text
evidence_span 本身也必须和 case / rule 相关，不能只靠 trigger_condition_found 里的关键词过关。
```

当前解释：

```text
partially_supported
```

边界：

```text
这是 basic adversarial sanity check，不是 deep semantic verifier，也不能证明能抵御复杂伪 evidence。
```

## 25. 最新进展：Constrained Post-Execution Skill Revision

新增方法定位文档：

```text
D:\solution\docs\CONSTRAINED_POST_EXECUTION_REVISION.md
```

核心修正：

```text
弱表述：加一个 token budget，预算够就接受，不够就拒绝。
强表述：核心不是检查预算，而是在执行反馈之后，对 skill 进行受约束修正。
```

新增 revision decision matrix：

```text
D:\solution\scripts\run_revision_decision_matrix.py
D:\solution\outputs\mvp_vertical_slice\revision_decision_matrix_001
```

当前矩阵：

```text
missing_rule -> patch affected rules
output_format_error -> rewrite output contract
regression_observed -> reject and rollback
semantic_compressed -> semantic preservation audit
rule_id_shortcut -> require rule_application trace
fake_trace_evidence -> strengthen trace verifier
trace_budget_pressure -> risk-based selective trace
```

当前解释：

```text
partially_supported
```

含义：

```text
目前创新潜力不在“预算限制”本身，而在 post-execution feedback 之后如何归因、定向修正、检查回归、验证语义和分配 trace 证据。
```

边界：

```text
这是 existing toy artifacts 上的机制矩阵，不是成熟 revision algorithm，也不是 benchmark。
```

## 26. Method Exploration Update: Posterior Skill Revision

New method hypothesis:

```text
Posterior skill revision treats a generated skill as a deployable hypothesis.
After execution, verifier or trajectory feedback should determine what to patch,
what to reject, what to trace, and when to roll back.
```

New artifact:

```text
D:\solution\outputs\mvp_vertical_slice\posterior_revision_signal_audit_001
```

Key diagnostic results:

```text
posterior_recovery_gain_over_compact_v1: 0.4166
posterior_recovery_gain_over_direct_summary: 0.0833
missing_rule_type_specificity_margin: 1
output_format_type_specificity_margin: 1
```

Current interpretation:

```text
The stronger story is not "we added token budget" or "we beat summary generation".
The stronger story is that posterior execution/verifier evidence can guide
type-specific repair, regression gating, and selective trace allocation.
```

Boundary:

```text
This is still controlled API-review evidence. It is a method hypothesis and audit,
not a broad PDI-like metric or cross-domain proof.
```

## 27. Novelty Pressure Test And Naive Revision Ablation

New related-work pressure document:

```text
D:\solution\docs\RELATED_WORK_NOVELTY_PRESSURE_TEST.md
```

Main correction:

```text
Posterior feedback itself is not novel.
The narrower possible delta is typed posterior revision over deployable expert-skill packages.
```

New ablation artifact:

```text
D:\solution\outputs\mvp_vertical_slice\naive_revision_ablation_001
```

Key diagnostic results:

```text
always_append_domain_rules: fixes missing_rule, fails output_format_error
always_rewrite_output_contract: fixes output_format_error, fails missing_rule
always_regenerate_full_skill: fixes tested failures but costs 1429.75 avg tokens
accept_if_current_failure_fixed: unsafe under rollback_gate_001
always_full_trace: blocks shortcut but is 300/237 over budget
type_specific_operator_plus_gate_and_selective_trace: resolves tested axes in toy slice
```

Current interpretation:

```text
The strongest current formulation is not "we have feedback revision".
It is: expert skill deployment feedback is attributed to typed revision operators
over rule/output-contract/trace-contract/gate records, then promoted through
deployment-level constraints.
```

Boundary:

```text
This remains narrow method evidence. Related work may still cover parts of the combination,
and full regeneration remains a strong high-cost upper bound.
```
