# 环境部署与 SPARK 最小链路进度记录

记录时间：2026-06-03 21:35（Asia/Shanghai）

## 1. 当前定位

本轮环境部署不是把 SPARK 当成唯一主线，而是验证它的“真实执行反馈模块”能否接入我们的 MVP 闭环：

```text
专家材料
-> full skill
-> evidence verification
-> compact skill
-> 真实/离线执行反馈
-> PDI / judge signal
-> skill patch
-> compact skill v2
-> 成本与效果对比
```

因此本轮测试分成两条线：

- 完整运行线：WSL2 + Docker + uv + Harbor + LLM endpoint，目标是尝试 `run_pipeline.py` 的最小真实执行链路。
- 离线反馈线：使用 SPARK 已发布的 trajectory artifact，复算 PDI signal，目标是先验证 execution-feedback 接口可以被我们复用。

## 2. 路径与空间策略

正式项目 workspace：

- `D:\solution`

外部仓库缓存：

- `D:\solution\external_repos\spark-skills`
- `D:\solution\external_repos\colleague-skill`

WSL 与 Docker 重型数据：

- WSL distro：`spark-ubuntu`
- WSL 安装位置：`D:\wsl\spark-ubuntu-24.04`
- WSL VHD：`D:\wsl\spark-ubuntu-24.04\ext4.vhdx`
- Docker 数据位置：WSL 内部 `/var/lib/docker`，实际落在上述 D 盘 VHD 中

空间检查结果：

- `C:` 可用空间约 79GB。
- `D:` 可用空间约 108GB。
- `D:\solution` 当前体量很小，主要增长来自 `D:\wsl\spark-ubuntu-24.04\ext4.vhdx`。
- WSL 根文件系统上限约 79GB，当前已用约 3.0GB，可用约 72GB。
- 当前 VHD 实体大小约 3.7GB。

结论：

- 不把 Docker Desktop 装到 C 盘，不把 Docker 镜像默认落到 Windows C 盘。
- 当前采用“Docker Engine inside WSL”的方式，把重型镜像/容器数据控制在 D 盘 VHD 内。
- 目前空间安全，可以继续安装 SPARK/Harbor 依赖；后续若拉大镜像，需要继续监控 VHD 增长。

## 3. WSL2 状态

已完成：

- 安装 Ubuntu 24.04 到 `D:\wsl\spark-ubuntu-24.04`。
- WSL distro 名称：`spark-ubuntu`。
- WSL2 可启动，root 用户可进入。
- systemd 已启用。
- Ubuntu 版本：24.04.4 LTS。

注意：

- WSL 每次启动时会输出一段 localhost/NAT 相关的编码乱码警告。
- 该警告目前不影响 apt、Docker、uv、Python 命令运行。

## 4. Docker 状态

已完成：

- 在 WSL 内安装 `docker.io` 与 `docker-compose-v2`。
- Docker service 已启动。
- Docker 版本：29.1.3。
- Docker Compose 版本：2.40.3+ds1。
- Docker storage driver：overlayfs。

网络处理：

- 直连 Docker Hub 官方 registry 超时。
- 已配置 Docker registry mirror：
  - `https://docker.m.daocloud.io`
  - `https://docker.1panel.live`

验证结果：

```text
docker run --rm hello-world
```

已成功拉取并运行 `hello-world`。

结论：

- Docker 基础能力可用。
- 后续 Harbor 若需要拉复杂基础镜像，仍需继续观察网络稳定性和镜像体积。

## 5. uv 状态

已完成：

- WSL 内安装 uv。
- uv 路径：`/root/.local/bin/uv`
- uv 版本：`uv 0.11.18`

SPARK 依赖安装：

```bash
cd /opt/spark/spark-skills
/root/.local/bin/uv sync
```

当前状态：

- `uv sync` 已开始运行，仍在后台继续。
- 已确认不是死锁：`uv` 有到 Python package CDN 的活动 TLS 连接。
- `/root/.cache/uv` 持续增长，说明正在下载/解包依赖。
- 已观察到正在处理的重包包括 `pyarrow`、`pandas`、`numpy`、`litellm`、`claude_agent_sdk`、`kubernetes`、`tokenizers` 等。
- `.venv` 尚未真正铺开，推测当前仍处于缓存/解包阶段。

风险：

- SPARK 的 `pyproject.toml` 主依赖包含 `harbor @ git+https://github.com/laude-institute/harbor.git`。
- Harbor 进一步依赖较多重包，安装时间可能较长。
- 如果后续长时间无增长，再考虑终止并改用 `uv sync --no-dev --locked` 做最小依赖安装。

## 6. SPARK 离线反馈探针

为了不让完整环境安装阻塞 MVP 设计，已先完成一条离线 SPARK PDI 验证。

新增脚本：

- `D:\solution\scripts\offline_spark_pdi_probe.py`

作用：

- 读取 SPARK 已发布 artifact 中的 `attempts.json`。
- 调用 SPARK 原仓库的 `PDITracker`。
- 根据 memo history、agent commands、test summary 复算 PDI snapshots。
- 输出 trigger step、trigger level、weighted PDI 等字段。

验证命令：

```powershell
$env:PYTHONIOENCODING='utf-8'
python D:\solution\scripts\offline_spark_pdi_probe.py
```

验证样例：

- task：`3d-scan-calc`
- artifact：`D:\solution\external_repos\spark-skills\spark_skills_gen\skills_gen_result\all_model_pdi\3d-scan-calc\attempts.json`

结果摘要：

```text
attempts: 9
final: PASS
final_reward: 1.0
stored_pdi_history: 8
recomputed_pdi_history: 8
triggers: 2
step=3 level=soft weighted_pdi=-0.5287
step=4 level=strong weighted_pdi=-1.4584
```

结论：

- SPARK 的 PDITracker 可以脱离 Harbor/Docker 完整执行链路进行离线复用。
- 输入接口可抽象为：`memo_history + agent_commands + test_summary`。
- 输出接口可抽象为：`proxy_exec + proxy_plan + proxy_oss + weighted_pdi + trigger level`。
- 这可以作为我们 MVP 的 execution-feedback module fallback。

## 7. 对 MVP 的意义

当前已经验证出一个现实可走的分层策略：

- 若 Harbor/真实 Docker pipeline 跑通：用 `run_pipeline.py --limit 1 --max-retries 1 --parallelism 1 --no-dashboard` 验证最小真实执行链路。
- 若 Harbor/LLM endpoint/镜像拉取阻塞：用离线 PDI 探针接入我们自己的 compact skill 执行报告，先完成 demo 闭环。

推荐接入方式：

```text
execution_report.json
-> convert to memo/test_summary/commands-like signal
-> PDITracker or simplified PDI adapter
-> repair_log.md
-> compact_skill_v2.md
```

这样 SPARK 不只是论文引用，而是提供“执行轨迹是否真正吸收进 skill/memo”的反馈机制。

## 8. 下一步

当前环境部署已完成最小工程链路验证。后续继续：

1. 将 mock endpoint 替换为真实 OpenAI-compatible endpoint。
2. 使用真实模型运行：
   ```bash
   cd /opt/spark/spark-skills
   OPENAI_API_KEY=<real_key> \
   OPENAI_BASE_URL=<real_base_url> \
   /root/.local/bin/uv run python run_pipeline.py \
     --agent qwen-coder \
     --model <real_model> \
     --tasks-dir <tasks_dir> \
     --max-retries 1 \
     --parallelism 1 \
     --limit 1 \
     --no-dashboard \
     --pdi-observe-only
   ```
3. 准备一个更接近两周 demo 的 API / 代码评审类 Harbor task，替换当前 `smoke-task`。
4. 继续保留离线 PDI 探针作为 fallback。

两周 demo 主线建议：

- 不等待完整 SPARK 全实验复现。
- 把 SPARK 的 PDI/trajectory signal 作为 execution-feedback module 接入我们的专家 skill 蒸馏闭环。
- 成本优化继续放在 compact skill、cheap-first verification、execution-feedback patch 三个机制里。

## 9. 更新：SPARK 最小工程链路已跑通

更新时间：2026-06-03 23:30（Asia/Shanghai）

在完成 `uv sync --locked --no-dev` 后，SPARK 运行依赖安装成功：

- 解析包数：163
- 安装运行依赖：147
- 关键依赖：`harbor==0.1.45`、`litellm`、`claude-agent-sdk`、`pyarrow`、`pandas`、`numpy`、`uvicorn`

已验证命令：

```bash
cd /opt/spark/spark-skills
/root/.local/bin/uv run python run_pipeline.py --help
/root/.local/bin/uv run python run_tasks_gen.py --help
/root/.local/bin/uv run python run_eval_skills.py --help
/root/.local/bin/uv run harbor --help
/root/.local/bin/uv run harbor tasks --help
```

### 9.1 Harbor + Docker smoke test

新增最小 Harbor task：

- `D:\solution\outputs\harbor-smoke\smoke-task`

该任务不依赖 LLM，不联网安装测试依赖，只检查 `/app/answer.txt` 是否等于 `spark-ok`。

运行命令：

```bash
cd /opt/spark/spark-skills
/root/.local/bin/uv run harbor run \
  --path /mnt/d/solution/outputs/harbor-smoke/smoke-task \
  --agent oracle \
  --jobs-dir /opt/spark/harbor-smoke-jobs \
  --n-concurrent 1 \
  --n-attempts 1 \
  --debug
```

结果：

```text
Trials: 1
Errors: 0
Mean: 1.000
Reward: 1.0
```

结论：

- WSL 内 Docker 可真实构建并运行 Harbor task。
- Harbor 可执行 solution、运行 verifier、写出 reward。

### 9.2 SPARK pipeline smoke test

由于当前没有真实 `OPENAI_API_KEY` / `OPENAI_BASE_URL`，新增本地 mock OpenAI-compatible server：

- `D:\solution\scripts\mock_openai_server.py`

用途：

- 只用于本地工程链路 smoke test。
- 响应 `/v1/chat/completions`。
- 返回固定 `SKILL.md` 内容。

运行 SPARK 最小 pipeline：

```bash
cd /opt/spark/spark-skills
OPENAI_API_KEY=dummy \
OPENAI_BASE_URL=http://127.0.0.1:8099/v1 \
/root/.local/bin/uv run python run_pipeline.py \
  --agent oracle \
  --model mock-model \
  --summary-model openai/mock-model \
  --tasks-dir /mnt/d/solution/outputs/harbor-smoke \
  --output-dir /opt/spark/spark-pipeline-smoke-jobs \
  --result-dir /opt/spark/spark-pipeline-smoke-results \
  --max-retries 1 \
  --parallelism 1 \
  --limit 1 \
  --no-dashboard \
  --pdi-observe-only
```

结果：

```text
Total tasks: 1
Passed: 1
Failed: 0
Pass rate: 100.0%
[PASS] smoke-task (attempts: 1, reward: 1.0)
```

已复制回 Windows workspace：

- `D:\solution\outputs\spark-pipeline-smoke-results`
- `D:\solution\outputs\spark-pipeline-smoke-jobs`

关键 artifact：

- `D:\solution\outputs\spark-pipeline-smoke-results\mock-model\pipeline_summary.json`
- `D:\solution\outputs\spark-pipeline-smoke-results\mock-model\smoke-task\SKILL.md`
- `D:\solution\outputs\spark-pipeline-smoke-results\mock-model\smoke-task\attempts.json`
- `D:\solution\outputs\spark-pipeline-smoke-results\mock-model\smoke-task\trajectory.jsonl`

结论升级：

- SPARK 最小工程链路已在 Windows + WSL2 + Docker + uv + Harbor 环境中跑通。
- 当前没有真实 API key 不再是环境安装阻塞，而是下一阶段把 mock endpoint 替换为真实 OpenAI-compatible endpoint 的配置问题。
- 对两周 demo 来说，完整 SPARK 代码路径可作为参考和部分集成基础；PDI 离线探针仍然是更稳的 execution-feedback fallback。
