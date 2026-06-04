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

## 9. 最新更新：MVP vertical slice 主链路已跑通

更新时间：2026-06-04（Asia/Shanghai）

当前已不再停留在系统设想阶段，已经完成一个确定性 baseline：

```text
API / 代码评审专家材料
-> full_skill.md
-> evidence_map.json
-> evidence_report.md
-> compact_skill_v1.md
-> execution_report_v1.json
-> repair_log.md
-> compact_skill_v2.md
-> execution_report_v2.json
-> cost_summary.json
```

新增完成：

- 已将 `D:\solution` 初始化为 Git 仓库，并完成两个基线提交。
- 已新增 `D:\solution\docs\MVP_VERTICAL_SLICE_PLAN.md`，固定两周 demo 的最小闭环。
- 已新增 API / 代码评审专家材料和合成 API case。
- 已新增 deterministic MVP runner：`D:\solution\scripts\run_mvp_vertical_slice.py`。
- 已生成 baseline artifact：`D:\solution\outputs\mvp_vertical_slice\baseline_001`。

baseline 结果：

```text
full_skill_tokens: 1294
compact_skill_v1_tokens: 222
compact_skill_v2_tokens: 285
compression_ratio_v1: 0.172
compression_ratio_v2: 0.220
execution_v1: detected 4 / expected 6
execution_v2: detected 6 / expected 6
```

这个结果表达的是：

- `compact_skill_v1` 先只保留高优先级、证据充分的规则，因此成本最低，但漏掉了执行中重要的 R005/R006。
- 执行反馈发现漏检规则后，`repair_log.md` 将 R005/R006 标记为 execution-critical。
- `compact_skill_v2` 在仍明显小于 full skill 的情况下补回关键规则，完成 6/6 检出。

当前判断：

- 成本已经进入系统机制，而不是最后附加统计。
- MVP 已经具备可演示 artifact 流：生成、证据映射、compact、执行反馈、修正、成本/效果对比。
- 下一步应把 deterministic execution 替换或并联为 Harbor/SPARK execution artifact，让 `trajectory.jsonl / attempts.json` 自动转成 `execution_report` 和 `repair_log`。

当前 Git 提交：

```text
f25d662 Initialize expert skill distillation MVP workspace
e18c966 Add deterministic MVP vertical slice runner
```

## 10. 最新更新：rule-level ledger 已进入 MVP 主链路

更新时间：2026-06-04（Asia/Shanghai）

根据 related work 风险判断，当前不把 `rule_ledger.json` 过度包装为强创新方法，而是把它定位为 MVP 的内部统一表示：

```text
rule-level evidence ledger as a decision backbone
```

也就是把 skill 拆成规则单元，并为每条规则记录：

- 材料证据：这条规则是否来自专家材料；
- 执行证据：这条规则是否在任务执行中触发、漏检或变成 failure-critical；
- 成本证据：这条规则是否应进入 compact skill；
- 决策结果：keep / drop / patch。

更稳的判断是：

```text
短期内，ledger 负责让最小系统可解释、可复现；
中期以后，真正可能产生方法价值的是 ledger 上的 decision policy。
```

新增完成：

- 新增 schema 文档：`D:\solution\docs\SKILL_PACKAGE_SCHEMA.md`。
- MVP runner 已生成 `rule_ledger.json`。
- `compact_skill_v1.md` 已改为由 `decision_v1` 驱动。
- `compact_skill_v2.md` 已改为由执行反馈更新后的 `decision_v2` 驱动。
- `repair_log.md` 现在按 rule-level patch 解释 R005/R006 为什么进入 v2。

baseline 更新后结果：

```text
no_skill_tokens: 0
full_skill_tokens: 1330
compact_skill_v1_tokens: 265
compact_skill_v2_tokens: 339
compression_ratio_v1: 0.199
compression_ratio_v2: 0.255
execution_no_skill: detected 0 / expected 6
execution_full_skill: detected 6 / expected 6
execution_v1: detected 4 / expected 6
execution_v2: detected 6 / expected 6
```

关键变化：

- `R005` 和 `R006` 在 v1 中因成本约束被 drop。
- 执行反馈发现 v1 漏检它们。
- `rule_ledger.json` 将二者标为 `failure_critical` 和 `compact_patch`。
- v2 不是人工随意补规则，而是根据 ledger 的 `decision_v2 = patch` 生成。

这使当前 MVP 的表达从：

```text
生成 skill + 执行反馈 + token 统计
```

升级为：

```text
材料证据 / 执行证据 / 成本证据
-> rule-level decision backbone
-> compact skill evolution
```

当前不声称 `rule_ledger` 本身已经构成强方法创新。四组对比 baseline 已生成，详见：

- `D:\solution\reports\DEMO_REPORT.md`
- `D:\solution\outputs\mvp_vertical_slice\baseline_001\demo_report.md`
- `D:\solution\outputs\mvp_vertical_slice\baseline_001\comparison_summary.json`

## 11. 最新更新：SPARK artifact adapter 第一版已跑通

更新时间：2026-06-04（Asia/Shanghai）

已新增 SPARK adapter，用于把 SPARK / Harbor 的执行 artifact 转成项目统一的 execution evidence。

新增脚本：

```text
D:\solution\integrations\spark\convert_spark_artifacts.py
```

验证输入：

```text
D:\solution\outputs\spark-pipeline-smoke-results\mock-model\smoke-task
```

验证输出：

```text
D:\solution\outputs\spark-adapter-smoke\baseline_001\execution_report_spark.json
D:\solution\outputs\spark-adapter-smoke\baseline_001\spark_adapter_report.md
```

转换结果：

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
failure_type: none
```

当前意义：

- SPARK 最小执行链路不再只是外部结果，已经可以转成我们自己的 `execution_report` 格式。
- smoke task 是 PASS，因此只提供正向执行证据，不产生 repair patch。
- 已补充离线失败 fixture，验证 `failure_type -> affected_rule -> patch_ready` 的最小路径。
- 下一步需要构造一个 API review Harbor task，让这个失败路径来自真实 Harbor/SPARK 执行，而不是 fixture。

新增说明文档：

```text
D:\solution\docs\SPARK_ADAPTER.md
```

失败 fixture 结果：

```text
task_name: api-review-fixture
passed: false
failure_type: verifier_failure
affected_rule_ids: R005, R006
patch_ready: true
pdi_history_count: 1
```

## 12. 最新更新：SPARK feedback 已能回写 rule_ledger

更新时间：2026-06-04（Asia/Shanghai）

已新增 SPARK feedback 应用脚本：

```text
D:\solution\integrations\spark\apply_spark_feedback.py
```

它将 SPARK-compatible execution report 回写到 MVP 的 rule-level decision layer：

```text
execution_report_spark.json
-> affected_rule_ids
-> rule_ledger_patched.json
-> repair_log_spark.md
-> compact_skill_v2.md
```

已生成完整闭环输出：

```text
D:\solution\outputs\mvp_vertical_slice\spark_feedback_001
```

结果：

```text
failure_type: verifier_failure
affected_rule_ids: R005, R006
patch_ready: true
full_skill_tokens: 1330
compact_skill_v1_tokens: 265
compact_skill_v2_from_spark_tokens: 315
compression_ratio_v2_from_spark: 0.237
```

当前意义：

- SPARK/Harbor 风格的执行失败不再只是日志，已经能改变具体 rule 的状态。
- `R005/R006` 被标记为 `failure_critical` 与 `compact_patch`。
- patched ledger 能生成新的 `compact_skill_v2.md`。

边界：

- 当前失败输入仍是 fixture，不是真实 Harbor API review task。
- 因此当前证明的是结构接口已打通，不是证明真实任务成功率提升。

下一步：

```text
构造真实 Harbor API review task
-> 注入 compact_skill_v1
-> 产生真实 attempts / trajectory
-> adapter 转 execution_report_spark
-> 回写 rule_ledger
```

## 13. 最新更新：related work 定位与 validation gate

更新时间：2026-06-04（Asia/Shanghai）

已新增 related work 定位文档：

```text
D:\solution\docs\RELATED_WORK_POSITIONING.md
```

当前定位进一步收缩为：

```text
不 claim 通用 skill lifecycle / self-evolution / rollback / cost-aware framework；
只 claim expert-material-first vertical slice；
重点展示 SPARK-compatible feedback 如何回写 rule-level deployment decision。
```

同时已给 SPARK feedback patch 增加 MVP 级 validation gate：

```text
patch_ready == true
affected_rule_ids is not empty
affected rules appear in compact_skill_v2
token increase ratio <= threshold
```

当前 `spark_feedback_001` gate 结果：

```text
accepted: true
max_token_increase_ratio: 0.30
token_increase_ratio: 0.189
affected_rule_ids: R005, R006
affected_rules_present: true
within_budget: true
```

更新后的成本结果：

```text
full_skill_tokens: 1330
compact_skill_v1_tokens: 265
compact_skill_v2_from_spark_tokens: 315
compression_ratio_v2_from_spark: 0.237
```

报告中新增五个轻量评估维度：

- Completeness：checklist coverage / missed rules。
- Executability：pass / reward / verifier result。
- Maintainability：rule-level repair log and patched ledger。
- Cost-awareness：input tokens / compact ratio / patch token increase。
- Auditability：evidence map / rule ledger / source execution report。

## 14. 最新更新：真实 Harbor API-review verifier 已跑通

更新时间：2026-06-04（Asia/Shanghai）

已新增真实 Harbor API-review task：

```text
D:\solution\data\harbor_api_review_tasks\api-review-001-compact-v1
D:\solution\data\harbor_api_review_tasks\api-review-001-compact-v2
```

任务要求 agent / oracle solution 输出：

```text
/app/review.json
```

Harbor verifier 检查 `review.json` 是否覆盖：

```text
R001, R002, R003, R004, R005, R006
```

真实 Harbor 运行结果：

```text
compact_v1: reward = 0.0
compact_v1 verifier: FAIL: missing expected findings for R005 R006

compact_v2: reward = 1.0
compact_v2 verifier: PASS: review.json covers required rule ids R001-R006
```

已新增 Harbor 原生结果转换脚本：

```text
D:\solution\integrations\spark\convert_harbor_result.py
```

转换输出：

```text
D:\solution\outputs\harbor-api-review-real\compact_v1_converted\execution_report_spark.json
D:\solution\outputs\harbor-api-review-real\compact_v2_converted\execution_report_spark.json
```

已生成真实 Harbor feedback 闭环：

```text
D:\solution\outputs\mvp_vertical_slice\harbor_api_review_001
```

该闭环证明：

```text
real Harbor verifier failure
-> failure_type = missing_rule
-> affected_rule_ids = R005, R006
-> rule_ledger_patched.json
-> validation_gate accepted
-> compact_skill_v2.md
```

边界：

- 当前使用 Harbor oracle solution，不是真实 LLM agent。
- 但失败/通过已经由 Docker/Harbor verifier 实际产生，不再是手写 fixture。
