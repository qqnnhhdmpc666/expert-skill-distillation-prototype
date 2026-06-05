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
