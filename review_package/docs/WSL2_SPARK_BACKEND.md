# WSL2 / SPARK 后端状态

更新时间：2026-06-08 01:30 CST

## 已完成

- WSL2 发行版：`Ubuntu-24.04-Codex`
- Windows 后端目录：`C:\Users\31552\wsl2-spark-backend`
- WSL 内 SPARK 路径：`/opt/spark/spark-skills`
- SPARK commit：`4c79c5a`
- Harbor locked source：`/opt/spark/harbor-src-locked`
- Docker Engine：已安装并启动
- Docker Compose v2：已安装
- 本地 Ubuntu 镜像：已由 WSL rootfs 导入为 `ubuntu:24.04`
- 本地 Docker smoke：`spark-wsl-smoke:local` 可运行

## 已跑通的真实闭环

当前已跑通一个最小 SPARK / Harbor / Docker / LLM distillation smoke：

```text
Harbor oracle agent
-> Docker task environment
-> shell verifier writes reward
-> SPARK trajectory writer
-> LiteLLM / RightCode / gpt-5.5 distills SKILL.md
-> pipeline_summary PASS
```

关键产物位于 WSL 内：

```text
/opt/spark/spark-pipeline-smoke/jobs/
/opt/spark/spark-pipeline-smoke/results/oracle/hello-local/SKILL.md
/opt/spark/spark-pipeline-smoke/results/oracle/hello-local/attempts.json
/opt/spark/spark-pipeline-smoke/results/oracle/hello-local/trajectory.jsonl
/opt/spark/spark-pipeline-smoke/results/oracle/pipeline_summary.json
```

`pipeline_summary.json` 当前结果：

```text
total_tasks = 1
passed = 1
failed = 0
pass_rate = 100%
```

## 已跑通的真实安全任务

除 hello smoke 外，当前还新增并跑通了一个 Harbor / Docker 上传安全审查任务：

```text
task: real-upload-security-review
agent: Harbor oracle
environment: Docker in WSL2
verifier: checks security_report.json schema, evidence, and expected capability coverage
reward: 1.0
```

项目内任务定义：

```text
integrations/wsl_harbor_tasks/real-upload-security-review/
```

项目内结果镜像：

```text
outputs/wsl_harbor_real_upload_001/
outputs/wsl_harbor_real_upload_001/summary.md
outputs/wsl_harbor_real_upload_001/real-upload-security-review__dCxSUn5/artifacts/security_report.json
outputs/wsl_harbor_real_upload_001/real-upload-security-review__dCxSUn5/artifacts/result.json
```

验证覆盖：

```text
UPLOAD_TYPE_MAGIC
UPLOAD_PATH_ISOLATION
UPLOAD_AUDIT_RETENTION
```

## 重要边界

这一步证明了真实 WSL2 sandbox execution 已经可用，但还不是最终的通用 LLM agent 版本。

已真实发生：

- Harbor 真实创建 Docker task environment。
- Verifier 在容器任务上执行并产生 reward。
- SPARK 记录 trajectory、attempts 和 result。
- LLM 通过 OpenAI-compatible endpoint 生成 `SKILL.md`。

尚未完成：

- 用 `codex` / `qwen-coder` / `claude-code` 等真实 agent CLI 在 Harbor 中解决复杂任务。
- 将 WSL2 运行过程完整接入 Streamlit 前端。

## 检查命令

从项目根目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\check_wsl2_spark_backend.ps1
```

期望字段：

```text
wsl_available = true
distro_installed = true
spark_present = true
spark_core_imports = true
harbor_available = true
docker_available = true
docker_compose_available = true
pipeline_smoke_passed = true
```

真实安全任务结果也应存在：

```powershell
Get-Content outputs\wsl_harbor_real_upload_001\summary.md
```

## 复跑最小 SPARK smoke

不要把 API key 写入文件。只在当前命令会话注入环境变量：

```bash
cd /opt/spark/spark-skills
export OPENAI_BASE_URL="https://www.right.codes/codex/v1"
export OPENAI_API_KEY="..."

.venv/bin/python run_pipeline.py \
  --agent oracle \
  --model oracle \
  --summary-model gpt-5.5 \
  --tasks-dir tasks_no_skills_generate \
  --tasks hello-local \
  --max-retries 1 \
  --parallelism 1 \
  --no-dashboard \
  --result-dir /opt/spark/spark-pipeline-smoke/results \
  --output-dir /opt/spark/spark-pipeline-smoke/jobs
```

运行后需要检查并脱敏 artifact 中的环境变量记录。
