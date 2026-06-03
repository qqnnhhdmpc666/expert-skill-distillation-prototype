# 当前进度对齐摘要

记录时间：2026-06-03 21:55（Asia/Shanghai）

## 1. 当前项目定位

当前主线不是单纯复现某一篇论文，也不是只做成本统计，而是构建一个：

```text
基于证据与执行反馈的专家 Skill 蒸馏原型系统
```

一句话表达：

```text
生成要可信，执行要有效，调用要尽量轻。
```

最小闭环：

```text
专家材料
-> full skill package
-> evidence coverage / verification
-> compact skill v1
-> task execution / trajectory feedback
-> repair log / skill patch
-> compact skill v2
-> cost/effect comparison
```

## 2. 第一层任务进度

第一层任务是“可复现审查”，目标不是完整复现实验，而是判断两篇工作哪些能直接用于两周 demo。

已完成：

- 已将 `COLLEAGUE.SKILL` 与 `SPARK-PDI` 仓库下载到 `D:\solution\external_repos`。
- 已完成 `COLLEAGUE.SKILL` 本地测试，15 个测试通过。
- 已定位 `COLLEAGUE.SKILL` 最适合借鉴 artifact lifecycle、versioned skill package、manifest、correction/update/rollback。
- 已定位 `SPARK-PDI` 最适合借鉴 trajectory verification、PDI signal、execution memo、online intervention、six evidence blocks。
- 已写入 `D:\solution\reports\REPRO_AUDIT.md`。
- 已新增 `D:\solution\reports\ENV_SETUP_LOG.md`，记录 WSL/Docker/uv/Harbor 相关部署进度。

## 3. 环境部署进度

已完成：

- WSL2 Ubuntu 24.04 已安装到 D 盘：`D:\wsl\spark-ubuntu-24.04`。
- Docker Engine 已安装在 WSL 内，不依赖 Docker Desktop。
- Docker 数据落在 D 盘 WSL VHD 内，不默认占用 C 盘。
- Docker registry mirror 已配置。
- `docker run --rm hello-world` 已成功。
- uv 已安装到 WSL：`/root/.local/bin/uv`，版本 `0.11.18`。

当前进行中：

- 正在 WSL 内对 SPARK 执行 `uv sync`。
- Harbor 已经被 uv 拉入缓存，说明 GitHub Harbor 依赖不是完全阻塞。
- 当前慢点主要是 `pyarrow`、`pandas`、`numpy`、`litellm`、`claude_agent_sdk` 等重依赖下载/解包。

空间状态：

- C 盘仍有约 79GB 可用。
- D 盘仍有约 108GB 可用。
- WSL 根文件系统约 79GB，当前已用约 3GB。
- 当前路径控制符合预期，重型数据没有散落到项目目录或 C 盘。

## 4. SPARK 最小反馈链路验证

虽然完整 Harbor 运行链路仍在安装，但已经先完成了 SPARK 离线反馈模块验证。

新增脚本：

- `D:\solution\scripts\offline_spark_pdi_probe.py`

验证内容：

- 使用 SPARK 原仓库的 `PDITracker`。
- 读取已有 artifact：`3d-scan-calc/attempts.json`。
- 复算 PDI snapshots。
- 对比仓库保存的 PDI history。

结果：

```text
task: 3d-scan-calc
attempts: 9
final: PASS
stored_pdi_history: 8
recomputed_pdi_history: 8
triggers: 2
step=3 level=soft weighted_pdi=-0.5287
step=4 level=strong weighted_pdi=-1.4584
```

判断：

- SPARK 的 execution-feedback signal 可以脱离完整 Docker/Harbor 链路复用。
- 它可以作为 MVP 中 `execution_report -> repair_log -> compact_skill_v2` 的反馈接口。
- 即使完整 SPARK pipeline 因 LLM endpoint、镜像或 Harbor 配置受阻，两周 demo 仍然可以继续推进。

## 5. 当前关键判断

第一，完整 SPARK 复现是增强项，不是 demo 主线阻塞项。

第二，`COLLEAGUE.SKILL` 提供 skill package 工程结构，`SPARK-PDI` 提供 execution feedback 验证机制。我们的系统价值来自把它们放进同一个闭环。

第三，成本优化应该进入系统结构，而不是最后统计：

- compact skill 减少上下文成本；
- cheap-first verification 减少不必要 LLM verifier；
- execution-feedback patch 减少重复失败和重试。

第四，当前最稳的 demo 路径是：

```text
专家材料
-> full_skill.md
-> evidence_report.md
-> compact_skill_v1.md
-> execution_report_v1.json
-> PDI / judge feedback
-> repair_log.md
-> compact_skill_v2.md
-> cost_summary.json
```

## 6. 下一步

优先级 1：

将本地 mock endpoint 替换为真实 OpenAI-compatible endpoint，验证真实模型是否能完成 skill generation。

优先级 2：

准备一个更接近 demo 场景的最小 task，例如 API / 代码评审任务，让 SPARK execution artifact 与我们的 MVP 场景对齐。

优先级 3：

并行推进我们自己的 MVP vertical slice，不等待完整 SPARK 全链路：

```text
API / 代码评审专家材料
-> rule extraction
-> evidence map
-> compact skill
-> simulated execution report
-> PDI-style feedback
-> skill patch
-> cost/effect comparison
```

## 7. 当前可对外汇报的一句话

我们已完成两篇工作的可复现审查与本地定位：`COLLEAGUE.SKILL` 的 artifact 生命周期可以直接借鉴，`SPARK-PDI` 的 PDI execution-feedback 信号已通过离线 artifact 成功复算；同时 WSL2/Docker/uv/Harbor 环境已经在 D 盘隔离部署并跑通最小 SPARK pipeline smoke test。当前 demo 主线不会被完整论文实验复现阻塞，可以进入“专家材料 -> 可验证 skill -> 执行反馈 -> 修正 -> 轻量化调用”的 MVP 机制整合阶段。

## 8. 最新更新：最小 SPARK 工程链路已跑通

更新时间：2026-06-03 23:30（Asia/Shanghai）

环境状态已经从“安装验证中”升级为“最小工程链路可运行”。

新增完成：

- `uv sync --locked --no-dev` 已成功，SPARK 运行依赖安装完成。
- Harbor CLI 可用，`run_pipeline.py --help`、`run_tasks_gen.py --help`、`run_eval_skills.py --help` 均可运行。
- 已创建最小 Harbor smoke task：`D:\solution\outputs\harbor-smoke\smoke-task`。
- 已用 Harbor + Docker + oracle agent 跑通 smoke task，reward = 1.0。
- 已新增本地 mock OpenAI-compatible server：`D:\solution\scripts\mock_openai_server.py`。
- 已用 mock endpoint 跑通 SPARK pipeline：`execute -> judge -> skill_gen_call -> save result`。

SPARK pipeline smoke test 结果：

```text
Total tasks: 1
Passed: 1
Failed: 0
Pass rate: 100.0%
[PASS] smoke-task (attempts: 1, reward: 1.0)
```

已保存 artifact：

- `D:\solution\outputs\spark-pipeline-smoke-results\mock-model\pipeline_summary.json`
- `D:\solution\outputs\spark-pipeline-smoke-results\mock-model\smoke-task\SKILL.md`
- `D:\solution\outputs\spark-pipeline-smoke-results\mock-model\smoke-task\attempts.json`
- `D:\solution\outputs\spark-pipeline-smoke-results\mock-model\smoke-task\trajectory.jsonl`

更新后的判断：

- Docker / Harbor / uv / SPARK 主 CLI 在当前 Windows + WSL2 环境中可用。
- 当前真正缺的是“真实 OpenAI-compatible endpoint + 真实 task source”，不是基础环境。
- demo 主线可以大胆推进到第二层机制整合：专家材料蒸馏、证据映射、compact skill、执行反馈与修正。
- SPARK 的完整真实任务运行可作为增强项；PDI 离线探针和 smoke pipeline artifact 可作为稳定 fallback。

更新后可对外汇报的一句话：

我们已在 D 盘隔离的 WSL2 环境中完成 Docker、uv、Harbor 与 SPARK 依赖部署，并跑通了一个不依赖真实 API key 的最小 SPARK pipeline smoke test：Harbor 真实执行 task、verifier 返回 reward=1.0、SPARK 记录 trajectory 并通过 mock OpenAI-compatible endpoint 生成 `SKILL.md`。这说明工程链路可用，下一步可以把 mock endpoint 替换为真实模型，或直接把 SPARK 的 trajectory/PDI 机制接入我们的专家 Skill 蒸馏 MVP。
