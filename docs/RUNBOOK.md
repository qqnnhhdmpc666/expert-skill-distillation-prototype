# Runbook

日期：2026-06-05

## 1. 前置条件

工作目录：

```powershell
cd D:\solution
```

Windows 侧需要：

- Python 可用
- Git 可用

WSL 侧需要：

- WSL distro：`spark-ubuntu`
- Docker Engine 可用
- SPARK repo：`/opt/spark/spark-skills`
- uv：`/root/.local/bin/uv`

ARIS 科研工作流位置：

```text
C:\Users\老板\Desktop\new\aris_repo
```

当前项目不依赖 `aris` 命令入口，只吸收其工作习惯：claim -> evidence -> run order、manifest/artifact discipline、结果分析后再确定下一步。

## 2. 复现 deterministic MVP baseline

```powershell
python scripts\run_mvp_vertical_slice.py `
  --run-id baseline_001 `
  --created-at 2026-06-03T18:06:09.686982+00:00
```

检查：

```powershell
Get-Content outputs\mvp_vertical_slice\baseline_001\comparison_summary.json
Get-Content outputs\mvp_vertical_slice\baseline_001\cost_summary.json
```

预期：

```text
no_skill: 0 / 6
full_skill: 6 / 6
compact_v1: 4 / 6
compact_v2: 6 / 6
```

## 3. 复现 SPARK fixture feedback

```powershell
python integrations\spark\convert_spark_artifacts.py `
  --task-dir data\spark_failed_fixture `
  --output-dir outputs\spark-adapter-failure-fixture\baseline_001

python integrations\spark\apply_spark_feedback.py `
  --source-run-dir outputs\mvp_vertical_slice\baseline_001 `
  --spark-report outputs\spark-adapter-failure-fixture\baseline_001\execution_report_spark.json `
  --output-dir outputs\mvp_vertical_slice\spark_feedback_001 `
  --created-at 2026-06-04T00:00:00+00:00
```

## 4. 复现真实 Harbor verifier case001

运行 v1，预期失败：

```powershell
wsl -d spark-ubuntu -- bash -lc "chmod +x /mnt/d/solution/data/harbor_api_review_tasks/api-review-001-compact-v1/solution/solve.sh /mnt/d/solution/data/harbor_api_review_tasks/api-review-001-compact-v1/tests/test.sh /mnt/d/solution/data/harbor_api_review_tasks/api-review-001-compact-v2/solution/solve.sh /mnt/d/solution/data/harbor_api_review_tasks/api-review-001-compact-v2/tests/test.sh && cd /opt/spark/spark-skills && /root/.local/bin/uv run harbor run --path /mnt/d/solution/data/harbor_api_review_tasks/api-review-001-compact-v1 --agent oracle --jobs-dir /opt/spark/harbor-api-review-v1-jobs --n-concurrent 1 --n-attempts 1 --debug"
```

运行 v2，预期通过：

```powershell
wsl -d spark-ubuntu -- bash -lc "cd /opt/spark/spark-skills && /root/.local/bin/uv run harbor run --path /mnt/d/solution/data/harbor_api_review_tasks/api-review-001-compact-v2 --agent oracle --jobs-dir /opt/spark/harbor-api-review-v2-jobs --n-concurrent 1 --n-attempts 1 --debug"
```

转换和闭环：

```powershell
python integrations\spark\convert_harbor_result.py `
  --job-dir outputs\harbor-api-review-real\compact_v1 `
  --output-dir outputs\harbor-api-review-real\compact_v1_converted

python integrations\spark\convert_harbor_result.py `
  --job-dir outputs\harbor-api-review-real\compact_v2 `
  --output-dir outputs\harbor-api-review-real\compact_v2_converted

python integrations\spark\apply_spark_feedback.py `
  --source-run-dir outputs\mvp_vertical_slice\baseline_001 `
  --spark-report outputs\harbor-api-review-real\compact_v1_converted\execution_report_spark.json `
  --comparison-report outputs\harbor-api-review-real\compact_v2_converted\execution_report_spark.json `
  --output-dir outputs\mvp_vertical_slice\harbor_api_review_001 `
  --created-at 2026-06-04T00:30:00+00:00
```

## 5. 复现真实 Harbor holdout case002

运行 v1，预期失败：

```powershell
wsl -d spark-ubuntu -- bash -lc "chmod +x /mnt/d/solution/data/harbor_api_review_tasks/api-review-002-compact-v1/solution/solve.sh /mnt/d/solution/data/harbor_api_review_tasks/api-review-002-compact-v1/tests/test.sh /mnt/d/solution/data/harbor_api_review_tasks/api-review-002-compact-v2/solution/solve.sh /mnt/d/solution/data/harbor_api_review_tasks/api-review-002-compact-v2/tests/test.sh && cd /opt/spark/spark-skills && /root/.local/bin/uv run harbor run --path /mnt/d/solution/data/harbor_api_review_tasks/api-review-002-compact-v1 --agent oracle --jobs-dir /opt/spark/harbor-api-review-002-v1-jobs --n-concurrent 1 --n-attempts 1 --debug"
```

运行 v2，预期通过：

```powershell
wsl -d spark-ubuntu -- bash -lc "cd /opt/spark/spark-skills && /root/.local/bin/uv run harbor run --path /mnt/d/solution/data/harbor_api_review_tasks/api-review-002-compact-v2 --agent oracle --jobs-dir /opt/spark/harbor-api-review-002-v2-jobs --n-concurrent 1 --n-attempts 1 --debug"
```

闭环输出：

```text
D:\solution\outputs\mvp_vertical_slice\harbor_api_review_002
```

## 6. 复现 Mock Agent Execution Layer

本地 smoke：

```powershell
python agents\api_review_mock_agent.py `
  --compact-skill outputs\mvp_vertical_slice\baseline_001\compact_skill_v1.md `
  --case data\harbor_api_review_tasks\api-review-002-compact-v1\case_002_openapi.md `
  --output outputs\agent-mock-smoke\review_v1.json

python agents\api_review_mock_agent.py `
  --compact-skill outputs\mvp_vertical_slice\harbor_api_review_002\compact_skill_v2.md `
  --case data\harbor_api_review_tasks\api-review-002-compact-v1\case_002_openapi.md `
  --output outputs\agent-mock-smoke\review_v2.json
```

运行 Harbor v1，预期失败：

```powershell
wsl -d spark-ubuntu -- bash -lc "chmod +x /mnt/d/solution/data/harbor_api_review_tasks/api-review-agent-mock-001-compact-v1/solution/solve.sh /mnt/d/solution/data/harbor_api_review_tasks/api-review-agent-mock-001-compact-v1/tests/test.sh /mnt/d/solution/data/harbor_api_review_tasks/api-review-agent-mock-001-compact-v2/solution/solve.sh /mnt/d/solution/data/harbor_api_review_tasks/api-review-agent-mock-001-compact-v2/tests/test.sh && cd /opt/spark/spark-skills && /root/.local/bin/uv run harbor run --path /mnt/d/solution/data/harbor_api_review_tasks/api-review-agent-mock-001-compact-v1 --agent oracle --jobs-dir /opt/spark/agent-mock-api-review-001-v1-jobs --n-concurrent 1 --n-attempts 1 --debug"
```

运行 Harbor v2，预期通过：

```powershell
wsl -d spark-ubuntu -- bash -lc "cd /opt/spark/spark-skills && /root/.local/bin/uv run harbor run --path /mnt/d/solution/data/harbor_api_review_tasks/api-review-agent-mock-001-compact-v2 --agent oracle --jobs-dir /opt/spark/agent-mock-api-review-001-v2-jobs --n-concurrent 1 --n-attempts 1 --debug"
```

将最新 Harbor job 复制回 workspace。时间戳按实际输出替换：

```powershell
wsl -d spark-ubuntu -- bash -lc "rm -rf /mnt/d/solution/outputs/harbor-agent-mock-api-review-001/compact_v1 /mnt/d/solution/outputs/harbor-agent-mock-api-review-001/compact_v2 && mkdir -p /mnt/d/solution/outputs/harbor-agent-mock-api-review-001 && cp -a /opt/spark/agent-mock-api-review-001-v1-jobs/2026-06-05__12-42-51 /mnt/d/solution/outputs/harbor-agent-mock-api-review-001/compact_v1 && cp -a /opt/spark/agent-mock-api-review-001-v2-jobs/2026-06-05__12-44-57 /mnt/d/solution/outputs/harbor-agent-mock-api-review-001/compact_v2"
```

转换和闭环：

```powershell
python integrations\spark\convert_harbor_result.py `
  --job-dir outputs\harbor-agent-mock-api-review-001\compact_v1 `
  --output-dir outputs\harbor-agent-mock-api-review-001\compact_v1_converted

python integrations\spark\convert_harbor_result.py `
  --job-dir outputs\harbor-agent-mock-api-review-001\compact_v2 `
  --output-dir outputs\harbor-agent-mock-api-review-001\compact_v2_converted

python integrations\spark\apply_spark_feedback.py `
  --source-run-dir outputs\mvp_vertical_slice\baseline_001 `
  --spark-report outputs\harbor-agent-mock-api-review-001\compact_v1_converted\execution_report_spark.json `
  --comparison-report outputs\harbor-agent-mock-api-review-001\compact_v2_converted\execution_report_spark.json `
  --output-dir outputs\mvp_vertical_slice\agent_mock_api_review_001 `
  --created-at 2026-06-05T04:50:00+00:00
```

预期：

```text
compact_v1 agent output: R001-R004
compact_v1 Harbor reward: 0.0
compact_v1 verifier: missing R005 R006

compact_v2 agent output: R001-R006
compact_v2 Harbor reward: 1.0
compact_v2 verifier: covers R001-R006
```

边界：

```text
mock agent 只验证执行接口，不证明真实 LLM 能稳定完成任务。
```

## 7. 运行 OpenAI-compatible LLM Agent Layer

这一层先在 Harbor 外部运行，避免同时调试 Docker 网络、环境变量和模型输出格式。

RightCode GPT 当前可用配置：

```powershell
$env:OPENAI_BASE_URL="https://www.right.codes/codex/v1"
$env:OPENAI_API_KEY="<your-api-key>"
$env:MODEL="gpt-5.5"
```

注意：官方 GPT-Codex 示例中出现过 `gpt-5.2`，但当前 key 对 `/codex` 站点实际可用的是 `gpt-5.5`。不要把 API key 写入仓库文件。

单次运行：

```powershell
python agents\api_review_llm_agent.py `
  --skill outputs\mvp_vertical_slice\baseline_001\compact_skill_v1.md `
  --case data\harbor_api_review_tasks\api-review-001-compact-v1\case_001_openapi.md `
  --output outputs\mvp_vertical_slice\llm_agent_api_review_001\case001_compact_v1\review.json
```

四组 matrix：

```powershell
python scripts\run_llm_agent_api_review_matrix.py `
  --output-dir outputs\mvp_vertical_slice\llm_agent_api_review_001 `
  --created-at 2026-06-05T05:15:00+00:00
```

当前已使用 RightCode `gpt-5.5` 补跑四组 matrix：

```text
D:\solution\outputs\mvp_vertical_slice\llm_agent_api_review_001
```

预期结果：

```text
case001 + compact_v1: reward 0.0, missing R005 R006
case001 + compact_v2: reward 1.0, covers R001-R006
case002 + compact_v1: reward 0.0, missing R005 R006
case002 + compact_v2: reward 1.0, covers R001-R006
```

边界：

```text
LLM agent 层用于验证真实模型接口和 skill-conditioned output。
模型输出可能不稳定，不作为两周 demo 的唯一主线。
```

## 8. 运行 Counterfactual Patch Utility

方法探索支线，不替换稳定 demo 主线：

```powershell
python scripts\run_counterfactual_patch_utility.py
```

输出：

```text
D:\solution\outputs\mvp_vertical_slice\counterfactual_patch_utility_001
```

关键检查：

```powershell
Get-Content outputs\mvp_vertical_slice\counterfactual_patch_utility_001\summary.md
Get-Content outputs\mvp_vertical_slice\counterfactual_patch_utility_001\per_failure_results.json
```

预期观察：

```text
missing_rule:
  compiler_patch resolves failure
  no_patch / random_patch / wrong_type_patch do not

output_format_error:
  output_contract_patch resolves the format failure
  wrong_missing_rule_patch does not resolve the format failure
```

边界：

```text
这是 toy counterfactual，用来探索机制解释力。
它不是大规模 benchmark，也不证明通用 patch compiler。
```
## 9. 运行 Fixed-Budget Compiler 探索

该支线不替换稳定 demo 主线，只用于检查 execution-aware compact policy 是否能在固定预算内做规则取舍。

```powershell
python scripts\run_fixed_budget_compiler.py
```

输出：

```text
D:\solution\outputs\mvp_vertical_slice\fixed_budget_compiler_001
```

关键检查：

```powershell
Get-Content outputs\mvp_vertical_slice\fixed_budget_compiler_001\comparison.md
Get-Content outputs\mvp_vertical_slice\fixed_budget_compiler_001\comparison.json
```

当前预期观察：

```text
priority-only: 4/6, misses R005/R006
risk-cost: 4/6, misses R003/R006
execution-aware-fixed-budget: 5/6, recovers R005/R006 but misses R003
```

边界：

```text
这是固定预算机制探针，不是 benchmark，也不证明已经得到最优 compact compiler。
```

## 10. 运行 Rollback Gate 探索

该支线用于验证：patch 解决原始失败后，仍需要检查 regression / budget / failure-critical preservation。

```powershell
python scripts\run_rollback_gate.py
```

输出：

```text
D:\solution\outputs\mvp_vertical_slice\rollback_gate_001
```

关键检查：

```powershell
Get-Content outputs\mvp_vertical_slice\rollback_gate_001\validation_gate.json
Get-Content outputs\mvp_vertical_slice\rollback_gate_001\rollback_report.md
```

当前预期观察：

```text
resolves_original_failure: true
regression_detected: true
lost_previously_covered_rules: R003
accepted: false
decision: reject_and_rollback
```

边界：

```text
这是 toy validation-gated revision slice，不是成熟 rollback 系统。
```
## 11. 运行 Validation-Aware Compiler 探索

该支线把 fixed-budget compiler 和 rollback gate 联动起来，用于检查 compiler 是否能在固定预算下同时补 failure-critical rules 并保留 previously covered rules。

```powershell
python scripts\run_validation_aware_compiler.py
```

输出：

```text
D:\solution\outputs\mvp_vertical_slice\validation_aware_compiler_001
```

关键检查：

```powershell
Get-Content outputs\mvp_vertical_slice\validation_aware_compiler_001\summary.md
Get-Content outputs\mvp_vertical_slice\validation_aware_compiler_001\validation_results.json
```

当前预期观察：

```text
candidate_A_naive_execution_aware: reject_regression, misses R003
candidate_B_preserve_covered_first: reject_over_budget, original R001-R006 cost exceeds budget
candidate_C_compressed_required_rules: accept, covers R001-R006 with compressed wording
candidate_D_infeasible_original_wording: infeasible_under_budget
```

边界：

```text
这是 validation-aware fixed-budget recompilation 的 toy 探针。
如果 compressed wording 成功，只能说 success with compressed wording，不能说原始 selector 已经自然成功。
```

## 12. 运行 Semantic Preservation Audit

该支线用于检查 compressed candidate 是否保留规则语义，而不是只保留 rule ID。

```powershell
python scripts\run_semantic_preservation_audit.py
```

输出：

```text
D:\solution\outputs\mvp_vertical_slice\semantic_preservation_audit_001
```

关键检查：

```powershell
Get-Content outputs\mvp_vertical_slice\semantic_preservation_audit_001\semantic_audit.md
Get-Content outputs\mvp_vertical_slice\semantic_preservation_audit_001\per_rule_audit.json
```

当前预期观察：

```text
overall_status: preserved
```

边界：

```text
这是启发式审计，不替代人工审查或复杂语义 judge。
```

## 13. 运行 Compressed Candidate Execution

该支线用 candidate_C 跑 mock agent 和可用的 OpenAI-compatible LLM agent，并使用 stricter semantic verifier 检查输出。

```powershell
python scripts\run_compressed_candidate_execution.py
```

如果要启用 RightCode GPT，需要临时设置环境变量，不要写入文件：

```powershell
$env:OPENAI_BASE_URL="https://www.right.codes/codex/v1"
$env:OPENAI_API_KEY="<your-api-key>"
$env:MODEL="gpt-5.5"
python scripts\run_compressed_candidate_execution.py
Remove-Item Env:\OPENAI_API_KEY
Remove-Item Env:\OPENAI_BASE_URL
Remove-Item Env:\MODEL
```

输出：

```text
D:\solution\outputs\mvp_vertical_slice\compressed_candidate_execution_001
D:\solution\outputs\mvp_vertical_slice\semantic_verifier_001
```

当前预期观察：

```text
mock + semantic verifier: pass on case001/case002
RightCode gpt-5.5 + semantic verifier: pass on case001/case002 when endpoint env is configured
```

边界：

```text
通过该 slice 只能说明 toy case 中 compressed wording 有语义保真迹象，不能证明通用 fixed-budget compiler。
```

## 14. 运行 Skill-to-Agent Loop 探索

该支线用于检查 compact skill 是否只是进入 prompt，还是能让 agent 输出可验证的 rule-application trace。

```powershell
python scripts\run_skill_to_agent_loop.py
```

如果要启用 RightCode GPT，需要临时设置环境变量，不要写入文件：

```powershell
$env:OPENAI_BASE_URL="https://www.right.codes/codex/v1"
$env:OPENAI_API_KEY="<your-api-key>"
$env:MODEL="gpt-5.5"
python scripts\run_skill_to_agent_loop.py
Remove-Item Env:\OPENAI_API_KEY
Remove-Item Env:\OPENAI_BASE_URL
Remove-Item Env:\MODEL
```

输出：

```text
D:\solution\outputs\mvp_vertical_slice\skill_to_agent_loop_001
```

关键检查：

```powershell
Get-Content outputs\mvp_vertical_slice\skill_to_agent_loop_001\summary.md
Get-Content outputs\mvp_vertical_slice\skill_to_agent_loop_001\protocol_results.json
Get-Content outputs\mvp_vertical_slice\skill_to_agent_loop_001\semantic_verifier_results.json
```

当前预期观察：

```text
candidate_C_compressed_skill:
  simple/semantic verifier may pass, trace verifier fails without rule_applications

rule_id_shortcut_skill:
  trace verifier fails

protocolized_compressed_skill:
  mock trace verifier passes
  RightCode gpt-5.5 trace verifier passes when endpoint env is configured
```

边界：

```text
这是 M5 的 toy protocol probe，不能证明真实复杂任务正确性或通用 agent protocol。
```
## 15. 运行 Traceable Compact Compiler Integration

该支线用于把 M2 fixed-budget compiler、M3 validation gate 和 M5 skill-to-agent protocol 接成一个统一检查链路：

```powershell
python scripts\run_traceable_compiler_integration.py
```

输出：

```text
D:\solution\outputs\mvp_vertical_slice\traceable_compiler_integration_001
```

关键检查：

```powershell
Get-Content outputs\mvp_vertical_slice\traceable_compiler_integration_001\summary.md
Get-Content outputs\mvp_vertical_slice\traceable_compiler_integration_001\variant_results.json
Get-Content outputs\mvp_vertical_slice\traceable_compiler_integration_001\compiler_contract.json
```

当前预期观察：

```text
plain compact skill:
  fails coverage and trace verification

compressed compact skill:
  passes simple/semantic verification
  fails trace verification

compressed compact skill + protocol:
  passes trace verification
  exceeds fixed token budget

compressed compact skill + protocol + validation gate:
  rejected as over budget
```

当前结论：

```text
partially_supported_with_protocol_overhead
```

边界：

```text
这不是通用 compiler 证明。它说明 trace verifier 能阻止 shallow output / rule-id shortcut，但当前 protocol overhead 仍然太高，validation gate 拒绝部署是合理结果。
```
## 16. Run Real Effect Evaluation

This slice checks whether skill-conditioned deployment improves API-review behavior on a small controlled holdout set:

```powershell
python scripts\run_real_effect_eval.py
```

Input:

```text
D:\solution\data\api_review_holdout_cases
```

Output:

```text
D:\solution\outputs\mvp_vertical_slice\real_effect_eval_001
```

Key checks:

```powershell
Get-Content outputs\mvp_vertical_slice\real_effect_eval_001\summary.md
Get-Content outputs\mvp_vertical_slice\real_effect_eval_001\per_variant_results.json
Get-Content outputs\mvp_vertical_slice\real_effect_eval_001\cost_effect_table.md
```

Expected observation:

```text
compact_v1: lower holdout coverage and recurring critical misses
patched_compact: restores controlled holdout coverage
patched_compact_selective_trace: keeps coverage while exposing trace for selected critical rules
```

Boundary:

```text
This is a 4-case controlled holdout, not a benchmark or general real-world correctness proof.
```

## 17. Run Selective Trace Compiler

This slice compares where traceability cost should be spent:

```powershell
python scripts\run_selective_trace_compiler.py
```

Output:

```text
D:\solution\outputs\mvp_vertical_slice\selective_trace_compiler_001
```

Key checks:

```powershell
Get-Content outputs\mvp_vertical_slice\selective_trace_compiler_001\summary.md
Get-Content outputs\mvp_vertical_slice\selective_trace_compiler_001\variant_results.json
```

Expected observation:

```text
no_trace:
  cheapest, but shortcut_blocked=false

full_trace:
  shortcut_blocked=true, but reject_over_budget

selective_trace_failure_critical:
  traces R005/R006, stays under budget, shortcut_blocked=true
```

Boundary:

```text
This is a toy selective-trace policy, not a mature tracing strategy.
```

## 18. Run Artifact Claim Audit

This slice audits what each core artifact can safely support before demos or reports:

```powershell
python scripts\run_artifact_claim_audit.py
```

Output:

```text
D:\solution\outputs\mvp_vertical_slice\artifact_claim_audit_001
```

Key checks:

```powershell
Get-Content outputs\mvp_vertical_slice\artifact_claim_audit_001\summary.md
Get-Content outputs\mvp_vertical_slice\artifact_claim_audit_001\summary.json
```

Expected observation:

```text
status: ok
missing_artifacts: []
```

Boundary:

```text
The audit is a claim guard. It does not add new experimental evidence.
```

## 19. Review Related-Work Delta And Component Baselines

Use these documents before writing slides or claims:

```text
D:\solution\docs\RELATED_WORK_DELTA_AUDIT.md
D:\solution\docs\COMPONENT_BASELINE_PLAN.md
```

Purpose:

```text
RELATED_WORK_DELTA_AUDIT.md:
  explains what is inherited, adapted, or genuinely explored relative to SPARK-PDI and COLLEAGUE.SKILL.

COMPONENT_BASELINE_PLAN.md:
  explains how to attribute improvements to expert rules, compacting, patching, validation gate, trace protocol, and selective trace.
```

Boundary:

```text
These are positioning and planning documents. They do not add new benchmark evidence.
```

## 20. Run Repository Maturity Patch Checks

The repository now has a minimal package/schema/test skeleton:

```text
pyproject.toml
src/skill_deployment/
tests/
scripts/validate_task_cases.py
scripts/skill_deploy.py
```

Run fast tests:

```powershell
python -m pytest
```

Expected:

```text
11 passed
```

Validate holdout cases:

```powershell
python scripts\validate_task_cases.py
python scripts\skill_deploy.py validate-cases
```

Use the lightweight CLI wrapper:

```powershell
python scripts\skill_deploy.py check-existing
python scripts\skill_deploy.py audit-claims
python scripts\skill_deploy.py validate-cases
python scripts\skill_deploy.py run-holdout
```

Boundary:

```text
This patch adds minimum engineering maturity. It does not convert the repository into a mature platform.
```

## 21. Run Component Baseline Attribution

Run the direct-summary component baseline:

```powershell
python scripts\run_component_baseline_eval.py
```

Or use the lightweight CLI wrapper:

```powershell
python scripts\skill_deploy.py compare-baselines
```

Output:

```text
D:\solution\outputs\mvp_vertical_slice\component_baseline_direct_summary_001
```

Expected observation:

```text
direct_summary_skill: avg coverage 0.92, pass@1 3/4
patched_compact: avg coverage 1.00, pass@1 4/4
```

Boundary:

```text
This is a deterministic component attribution slice. It is not a benchmark and does not prove broad superiority over direct summarization.
```

## 22. Run Risk Trace Policy Baseline

Run the risk-vs-random selective trace baseline:

```powershell
python scripts\run_risk_trace_policy_baseline.py
```

Or use the lightweight CLI wrapper:

```powershell
python scripts\skill_deploy.py compare-trace-policy
```

Output:

```text
D:\solution\outputs\mvp_vertical_slice\risk_trace_policy_baseline_001
```

Expected observation:

```text
random_selective_trace: traced R002/R003, 183/237 tokens, failure-critical trace coverage 0.00
risk_based_selective_trace: traced R005/R006, 183/237 tokens, failure-critical trace coverage 1.00
```

Boundary:

```text
This is a toy policy baseline with one random seed. It is not statistical validation of a mature trace-selection policy.
```

## 23. Run Risk Trace Robustness Enumeration

Enumerate every size=2 trace allocation over R001-R006:

```powershell
python scripts\run_risk_trace_policy_robustness.py
```

Or use the lightweight CLI wrapper:

```powershell
python scripts\skill_deploy.py trace-robustness
```

Output:

```text
D:\solution\outputs\mvp_vertical_slice\risk_trace_policy_robustness_001
```

Expected observation:

```text
total_combinations: 15
full_failure_critical_coverage_count: 1
risk_based_selective_trace: R005/R006
```

## 24. Run Direct Summary Miss Analysis

Analyze the only failed direct-summary case:

```powershell
python scripts\run_direct_summary_miss_analysis.py
```

Or use the lightweight CLI wrapper:

```powershell
python scripts\skill_deploy.py analyze-summary-miss
```

Output:

```text
D:\solution\outputs\mvp_vertical_slice\direct_summary_miss_analysis_001
```

Expected observation:

```text
failed_case_id: case004_validation_sensitive_idempotency
missed_rule_ids: R006
```

Boundary:

```text
This is explanatory evidence for the current controlled family, not a general long-tail failure proof.
```
