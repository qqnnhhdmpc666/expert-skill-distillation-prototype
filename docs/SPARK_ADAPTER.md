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

后续当 SPARK task 失败或产生 PDI warning 时，转换流程应扩展为：

```text
execution_report_spark.json
-> failure_type
-> affected_rule_id
-> rule_ledger.patch
-> compact_skill_v2
```

也就是说，SPARK adapter 是从真实执行 artifact 到 `rule_ledger.json` 的桥，而不是另一个独立日志系统。
