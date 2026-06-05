# Runbook

日期：2026-06-05

## 1. 前置条件

工作目录：

```powershell
cd D:\solution
```

Windows 侧需要：

- Python 可用。
- Git 可用。

WSL 侧需要：

- WSL distro：`spark-ubuntu`
- Docker Engine 可用。
- SPARK repo 位于：`/opt/spark/spark-skills`
- uv 位于：`/root/.local/bin/uv`

ARIS 科研工作流位于：

```text
C:\Users\老板\Desktop\new\aris_repo
```

当前本项目暂不依赖 `aris` 命令入口，而是吸收 ARIS 的科研工作流习惯：

- 按 claim -> evidence -> run order 组织实验。
- 每个输出目录保留 manifest 和关键 artifact。
- 结果分析同时给 raw table、key finding、next experiment。

若后续需要，可以把本 runbook 的命令封装成 ARIS workflow 或 experiment tracker。

## 2. 复现 deterministic MVP baseline

```powershell
python scripts\run_mvp_vertical_slice.py `
  --run-id baseline_001 `
  --created-at 2026-06-03T18:06:09.686982+00:00
```

输出：

```text
D:\solution\outputs\mvp_vertical_slice\baseline_001
```

关键检查：

```powershell
Get-Content outputs\mvp_vertical_slice\baseline_001\comparison_summary.json
Get-Content outputs\mvp_vertical_slice\baseline_001\cost_summary.json
```

预期结果：

```text
no_skill: 0 / 6
full_skill: 6 / 6
compact_v1: 4 / 6
compact_v2: 6 / 6
```

## 3. 复现 SPARK fixture feedback

转换失败 fixture：

```powershell
python integrations\spark\convert_spark_artifacts.py `
  --task-dir data\spark_failed_fixture `
  --output-dir outputs\spark-adapter-failure-fixture\baseline_001
```

应用反馈：

```powershell
python integrations\spark\apply_spark_feedback.py `
  --source-run-dir outputs\mvp_vertical_slice\baseline_001 `
  --spark-report outputs\spark-adapter-failure-fixture\baseline_001\execution_report_spark.json `
  --output-dir outputs\mvp_vertical_slice\spark_feedback_001 `
  --created-at 2026-06-04T00:00:00+00:00
```

输出：

```text
D:\solution\outputs\mvp_vertical_slice\spark_feedback_001
```

## 4. 运行真实 Harbor API-review task

先在 WSL 中给脚本执行权限：

```powershell
wsl -d spark-ubuntu -- bash -lc "chmod +x /mnt/d/solution/data/harbor_api_review_tasks/api-review-001-compact-v1/solution/solve.sh /mnt/d/solution/data/harbor_api_review_tasks/api-review-001-compact-v1/tests/test.sh /mnt/d/solution/data/harbor_api_review_tasks/api-review-001-compact-v2/solution/solve.sh /mnt/d/solution/data/harbor_api_review_tasks/api-review-001-compact-v2/tests/test.sh"
```

运行 compact v1，预期失败：

```powershell
wsl -d spark-ubuntu -- bash -lc "cd /opt/spark/spark-skills && /root/.local/bin/uv run harbor run --path /mnt/d/solution/data/harbor_api_review_tasks/api-review-001-compact-v1 --agent oracle --jobs-dir /opt/spark/harbor-api-review-v1-jobs --n-concurrent 1 --n-attempts 1 --debug"
```

运行 compact v2，预期通过：

```powershell
wsl -d spark-ubuntu -- bash -lc "cd /opt/spark/spark-skills && /root/.local/bin/uv run harbor run --path /mnt/d/solution/data/harbor_api_review_tasks/api-review-001-compact-v2 --agent oracle --jobs-dir /opt/spark/harbor-api-review-v2-jobs --n-concurrent 1 --n-attempts 1 --debug"
```

预期结果：

```text
compact_v1: reward = 0.0, missing R005 R006
compact_v2: reward = 1.0, covers R001-R006
```

## 5. 转换 Harbor 原生结果

当前仓库已保存转换后的轻量结果。如果重新运行 Harbor 后需要更新转换结果，使用：

```powershell
python integrations\spark\convert_harbor_result.py `
  --job-dir outputs\harbor-api-review-real\compact_v1 `
  --output-dir outputs\harbor-api-review-real\compact_v1_converted

python integrations\spark\convert_harbor_result.py `
  --job-dir outputs\harbor-api-review-real\compact_v2 `
  --output-dir outputs\harbor-api-review-real\compact_v2_converted
```

## 6. 复现真实 Harbor feedback 闭环

```powershell
python integrations\spark\apply_spark_feedback.py `
  --source-run-dir outputs\mvp_vertical_slice\baseline_001 `
  --spark-report outputs\harbor-api-review-real\compact_v1_converted\execution_report_spark.json `
  --comparison-report outputs\harbor-api-review-real\compact_v2_converted\execution_report_spark.json `
  --output-dir outputs\mvp_vertical_slice\harbor_api_review_001 `
  --created-at 2026-06-04T00:30:00+00:00
```

关键检查：

```powershell
Get-Content outputs\mvp_vertical_slice\harbor_api_review_001\spark_feedback_report.md
Get-Content outputs\mvp_vertical_slice\harbor_api_review_001\validation_gate.json
```

预期结果：

```text
failure_type: missing_rule
affected_rule_ids: R005, R006
validation_gate.accepted: true
```

## 7. 当前边界

- `baseline_001` 是 deterministic execution。
- `spark_feedback_001` 使用 SPARK-compatible fixture。
- `harbor_api_review_001` 使用真实 Harbor verifier，但执行者仍是 oracle solution。
- 下一步增强方向是新增 holdout case，并尝试 mock / scripted LLM agent。

## 8. 运行 api-review-002 holdout case

运行 compact v1，预期失败：

```powershell
wsl -d spark-ubuntu -- bash -lc "chmod +x /mnt/d/solution/data/harbor_api_review_tasks/api-review-002-compact-v1/solution/solve.sh /mnt/d/solution/data/harbor_api_review_tasks/api-review-002-compact-v1/tests/test.sh /mnt/d/solution/data/harbor_api_review_tasks/api-review-002-compact-v2/solution/solve.sh /mnt/d/solution/data/harbor_api_review_tasks/api-review-002-compact-v2/tests/test.sh && cd /opt/spark/spark-skills && /root/.local/bin/uv run harbor run --path /mnt/d/solution/data/harbor_api_review_tasks/api-review-002-compact-v1 --agent oracle --jobs-dir /opt/spark/harbor-api-review-002-v1-jobs --n-concurrent 1 --n-attempts 1 --debug"
```

运行 compact v2，预期通过：

```powershell
wsl -d spark-ubuntu -- bash -lc "cd /opt/spark/spark-skills && /root/.local/bin/uv run harbor run --path /mnt/d/solution/data/harbor_api_review_tasks/api-review-002-compact-v2 --agent oracle --jobs-dir /opt/spark/harbor-api-review-002-v2-jobs --n-concurrent 1 --n-attempts 1 --debug"
```

转换和闭环：

```powershell
python integrations\spark\convert_harbor_result.py `
  --job-dir outputs\harbor-api-review-002-real\compact_v1 `
  --output-dir outputs\harbor-api-review-002-real\compact_v1_converted

python integrations\spark\convert_harbor_result.py `
  --job-dir outputs\harbor-api-review-002-real\compact_v2 `
  --output-dir outputs\harbor-api-review-002-real\compact_v2_converted

python integrations\spark\apply_spark_feedback.py `
  --source-run-dir outputs\mvp_vertical_slice\baseline_001 `
  --spark-report outputs\harbor-api-review-002-real\compact_v1_converted\execution_report_spark.json `
  --comparison-report outputs\harbor-api-review-002-real\compact_v2_converted\execution_report_spark.json `
  --output-dir outputs\mvp_vertical_slice\harbor_api_review_002 `
  --created-at 2026-06-05T03:10:00+00:00
```

预期结果：

```text
compact_v1: reward = 0.0, missing R005 R006
compact_v2: reward = 1.0, covers R001-R006
validation_gate.accepted: true
```
