# SPARK Adapter

日期：2026-06-04

## 1. 目标

SPARK adapter 的目标不是重写 SPARK，也不是复现完整实验，而是把 SPARK / Harbor 的执行 artifact 转换为本项目统一的 execution evidence。

输入：

```text
attempts.json
trajectory.jsonl
```

输出：

```text
execution_report_spark.json
spark_adapter_report.md
```

当前脚本：

```text
D:\solution\integrations\spark\convert_spark_artifacts.py
```

Harbor 原生结果转换脚本：

```text
D:\solution\integrations\spark\convert_harbor_result.py
```

## 2. 当前已验证输入

已在 smoke baseline 上验证：

```text
D:\solution\outputs\spark-pipeline-smoke-results\mock-model\smoke-task
```

该目录包含：

- `attempts.json`
- `trajectory.jsonl`
- `SKILL.md`

转换输出：

```text
D:\solution\outputs\spark-adapter-smoke\baseline_001
```

结果：

```text
task_name: smoke-task
passed: true
final_status: PASS
final_reward: 1.0
attempt_count: 1
skill_gen_calls: 1
input_tokens: 100
output_tokens: 80
pdi_enabled: true
pdi_history_count: 0
```

## 3. 统一字段

`execution_report_spark.json` 当前包含：

- `passed`
- `final_status`
- `final_reward`
- `attempt_count`
- `status_trajectory`
- `reward_trajectory`
- `failure_type`
- `pdi`
- `cost`
- `events`
- `raw_files`

这些字段对应 MVP 中的三类证据：

| Evidence Type | SPARK Field |
|---|---|
| 执行证据 | `passed`, `final_status`, `final_reward`, `status_trajectory` |
| 成本证据 | `cost.input_tokens`, `cost.output_tokens`, `cost.skill_gen_calls`, `cost.total_time_s` |
| 诊断证据 | `failure_type`, `pdi.history`, `events` |

## 4. Failure Taxonomy v0

当前只实现最小分类：

```text
PASS or reward == 1.0 -> none
trajectory event has error -> execution_error
reward < 1.0 -> verifier_failure
otherwise -> unknown_failure
```

同时，adapter 会从 `test_summary`、`agent_stdout_full`、`test_stdout_full`、`error` 等文本字段中抽取 `Rxxx` 格式的规则编号，形成：

```json
{
  "diagnosis": {
    "affected_rule_ids": ["R005", "R006"],
    "patch_ready": true,
    "patch_hint": "Map affected_rule_ids to rule_ledger patches."
  }
}
```

后续要扩展成 rule-level patch taxonomy：

```text
missing_rule -> patch/add rule
weak_rule -> strengthen rule
output_format_error -> rewrite output contract
irrelevant_rule_interference -> prune rule
cost_heavy_unused_rule -> drop or compress rule
tool_contract_mismatch -> add tool/contract constraint
```

## 5. 与 rule_ledger 的关系

当前 smoke task 是 PASS，因此 adapter 只提供正向执行证据，不产生 repair patch。

为了验证失败路径，当前也提供了一个离线 fixture：

```text
D:\solution\data\spark_failed_fixture
```

转换输出：

```text
D:\solution\outputs\spark-adapter-failure-fixture\baseline_001
```

结果：

```text
task_name: api-review-fixture
passed: false
failure_type: verifier_failure
affected_rule_ids: R005, R006
patch_ready: true
pdi_history_count: 1
```

后续当 SPARK task 失败或产生 PDI warning 时，转换流程应扩展为：

```text
execution_report_spark.json
-> failure_type
-> affected_rule_id
-> rule_ledger.patch
-> compact_skill_v2
```

也就是说，SPARK adapter 是从真实执行 artifact 到 `rule_ledger.json` 的桥，而不是另一个独立日志系统。

## 6. SPARK Feedback Application

已新增反馈应用脚本：

```text
D:\solution\integrations\spark\apply_spark_feedback.py
```

输入：

```text
source_run_dir/
  full_skill.md
  compact_skill_v1.md
  evidence_map.json
  rule_ledger.json

execution_report_spark.json
```

输出：

```text
rule_ledger_patched.json
repair_log_spark.md
compact_skill_v2.md
cost_summary.json
spark_feedback_report.md
validation_gate.json
manifest.json
```

当前验证输出：

```text
D:\solution\outputs\mvp_vertical_slice\spark_feedback_001
```

当前结果：

```text
failure_type: verifier_failure
affected_rule_ids: R005, R006
patch_ready: true
compact_skill_v1_tokens: 265
compact_skill_v2_from_spark_tokens: 315
compression_ratio_v2_from_spark: 0.237
validation_gate_accepted: true
token_increase_ratio: 0.189
```

边界：

```text
当前失败输入是 fixture，因此证明的是接口行为，不是真实任务效果提升。
下一步需要把 fixture 替换为真实 Harbor API review task。
```

## 7. Validation Gate v0

为了避免失败反馈无条件进入 compact skill，当前实现了一个最小 promotion gate：

```text
patch_ready == true
affected_rule_ids is not empty
all affected rules appear in compact_skill_v2
token increase ratio <= max_token_increase_ratio
```

默认阈值：

```text
max_token_increase_ratio = 0.30
```

当前 `spark_feedback_001` 结果：

```text
accepted: true
affected_rules_present: true
within_budget: true
token_increase_ratio: 0.189
```

这个 gate 只是 MVP 级别的约束，不等价于完整 held-out validation 或 Pareto frontier selection。

## 8. Real Harbor API Review Task

已新增真实 Harbor verifier 任务：

```text
D:\solution\data\harbor_api_review_tasks\api-review-001-compact-v1
D:\solution\data\harbor_api_review_tasks\api-review-001-compact-v2
```

任务要求输出：

```text
/app/review.json
```

verifier 检查：

```text
review.json 是否覆盖 required rule ids: R001-R006
```

真实 Harbor 结果：

```text
compact_v1: reward = 0.0, missing R005 R006
compact_v2: reward = 1.0, covers R001-R006
```

转换输出：

```text
D:\solution\outputs\harbor-api-review-real\compact_v1_converted
D:\solution\outputs\harbor-api-review-real\compact_v2_converted
```

闭环输出：

```text
D:\solution\outputs\mvp_vertical_slice\harbor_api_review_001
```

当前 `harbor_api_review_001` 意义：

```text
real Harbor verifier failure
-> missing_rule: R005, R006
-> rule_ledger patch
-> validation gate accepted
-> compact_skill_v2 generated
```

这一步证明了 execution feedback 不再只是 simulated 或 fixture，而是可以来自真实 Docker/Harbor verifier。
