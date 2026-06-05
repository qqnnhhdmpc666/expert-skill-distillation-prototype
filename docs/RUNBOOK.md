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
