# v0.2 Experiment and Migration Plan

## 1. 目标

第一阶段不是证明某个 RAG 技术先进，而是回答：

1. 哪类任务主要受益于 Skill？
2. 哪类任务主要受益于 Retrieval？
3. 两者组合是否有互补收益？
4. 轨迹更新是否能在独立任务上带来净增益而不增加误报？

## 2. 任务分层

首批防御性安全任务应按知识需求预注册，而不是只按漏洞类型分组。

| 分层 | 主要需求 | 示例 | 预期形态 |
|---|---|---|---|
| P: Procedure-dominant | 稳定审查/修复流程 | 输入验证、权限检查、补丁最小化、测试顺序 | Skill |
| K: Knowledge-dominant | 当前事实、版本、公告 | 依赖版本是否受 CVE 影响、框架当前安全配置 | Retrieval |
| H: Hybrid | 稳定流程 + 动态事实/仓库证据 | 定位依赖 -> 查询 advisory -> 验证可达性 -> 修复 | Both |
| N: Negative/unsupported | 无漏洞、证据不足或越界 | clean repo、未知版本、需 exploit 才能确认 | None/abstain |

建议 pilot 为 24 个任务，每层 6 个。任务太少时先做 12 个 plumbing smoke，但不能据此声称架构优越。

## 3. 固定实验矩阵

同一任务、同一模型、同一 Agent interface、同一工具权限和预算下比较：

1. `no_external_knowledge`
2. `full_material_context`
3. `traditional_hybrid_retrieval`：固定一次 sparse+dense+rerank
4. `agentic_retrieval`：允许多轮查询与停止
5. `skill_only`
6. `skill_plus_retrieval`
7. `skill_plus_retrieval_plus_trajectory_update`

必要的附加 oracle 仅用于 plumbing：

- gold source retrieval；
- gold patch；
- full trusted context。

oracle 不计入系统性能。

## 4. 防泄漏设计

每个 case 分成：

```text
agent-visible:
  task, target repository, permitted tools, public knowledge sources

router-visible:
  task metadata, corpus metadata, cost budget

evaluator-only:
  expected vulnerability, gold evidence span, hidden tests,
  clean/negative label, gold patch, grading rubric
```

candidate generation 只能读取公开 failure report、diagnostic feedback、retrieval receipt、evidence summary 和 limitation summary。不得读取 evaluator-only 字段。

## 5. Agent 与知识访问设置

### Agent

- 第一阶段使用一个 tool-using Agent；
- 固定模型、temperature、最大轮数和 tool budget；
- 为每组实验冻结 `AgentProfile` 和 profile hash；
- 至少 3 个随机 seed/repeat；
- 保存所有模型调用、tool call、stdout/stderr 和停止原因。

若更换模型、原生搜索能力或上下文窗口，必须进入新的实验 block，不能与旧结果直接汇总。

### Knowledge providers

- docs exact/BM25；
- optional dense/reranker；
- repo `rg`/symbol search；
- dependency/advisory structured lookup；
- trajectory case index。

每个 provider 必须输出 Retrieval Receipt。

## 6. Evaluator

### 最终指标

- patch/test 是否通过；
- benchmark-native resolved/unresolved；
- 已知漏洞是否被正确定位并有 target-grounded evidence；
- clean case 是否零误报；
- unsupported case 是否正确 abstain。

### 内部诊断

- capability activation；
- retrieval recall@k / selected-source precision；
- evidence grounding；
- schema/trace 完整性；
- 读取文件与工具覆盖；
- 检索污染和过时知识命中。

内部诊断不能覆盖最终测试失败。

## 7. 统计与决策

不要先做人工加权总分。报告：

- 每个 task 的 paired win/tie/loss；
- 分层 pass rate 与 bootstrap 置信区间；
- 二元 paired outcome 可用 McNemar 或 exact sign test；
- false positive、scope violation、cost、latency 独立展示；
- 用 Pareto dominance 判断质量/成本权衡。

核心对比：

```text
Retrieval marginal value = retrieval - no_external_knowledge
Skill marginal value = skill_only - no_external_knowledge
Complementarity = skill_plus_retrieval - max(skill_only, retrieval)
Trajectory update value = updated - frozen_hybrid
```

## 8. 轨迹更新实验

### 训练/验证/隐藏划分

- generation trajectories；
- validation tasks；
- sealed hidden tasks；
- negative/clean controls 单独保留。

### 更新候选

同一批轨迹产生两类 proposal：

1. Skill edit：跨任务稳定的流程、工具顺序或恢复策略；
2. Knowledge update：版本/环境特定案例、失败恢复、事实更正。

比较：

- top-reward only；
- success/failure contrast；
- diversity；
- active discriminative evidence；
- no update。

现有 v0.2 sealed hidden 是 flat signal，因此不能预设 active method 优胜。新实验必须扩大有区分度的失败类型，同时保持 hidden 封存。

## 9. 安全场景首批任务建议

### Procedure-dominant

- upload validation 和路径隔离；
- authorization ownership check；
- patch + targeted regression test；
- config secret/audit review。

### Knowledge-dominant

- 给定 package/version，查询官方 advisory 判断受影响范围；
- 查询框架当前安全默认值；
- API 版本迁移导致的安全行为变化。

### Hybrid

- 从 repo 定位依赖和调用 -> 查询 advisory -> 判断 reachability -> 生成修复；
- 按 Skill 执行权限审查 -> 检索框架文档 -> 运行测试验证；
- 已知 CVE 的仓库级安全补丁。

### Negative/unsupported

- 干净实现；
- 版本信息缺失；
- 检索来源冲突；
- 需要执行 exploit 才能确认的任务，必须 abstain。

## 10. 外部验证选择

- 优先 benchmark-native 防御性 patch/test，例如 AutoPatchBench 类任务；
- SWE-bench 可验证通用软件修复与 sandbox readiness，但不支撑安全主 claim；
- CVE-Bench 以 exploit 为目标，不适合作为第一阶段防御性主 benchmark；
- 自建 local mini-suite 只能做机制诊断。

## 11. 分阶段迁移

### Phase 0：设计冻结

只完成 schema、接口、task matrix 和 leakage policy。不得接数据库。

验收：三个知识形态示例可用契约完整表达；core 不引用 security capability id。

### Phase 1：只读 Knowledge Sidecar

在现有 installed Skill runtime 旁接一个 provider interface：

- file snapshot + SQLite FTS5；
- exact/BM25；
- Retrieval Receipt；
- rule-based `Skill/Retrieval/Both/None` router。

不允许轨迹自动写回。

验收：完成 7 路 baseline 的 12-case plumbing matrix。

### Phase 2：Security Adapter

- repo search provider；
- advisory/version provider；
- defensive tools 与 sandbox；
- benchmark-native evaluator adapter。

验收：24-case 预注册矩阵，至少包含 P/K/H/N 四层。

### Phase 3：轨迹双向更新

- observed trajectory store；
- case knowledge proposal；
- bounded Skill edit；
- held-out gate 与 rejected buffer。

验收：至少一个 Skill candidate 和一个 knowledge update 在独立任务上有正边际收益，且 clean/unsupported 不退化。

### Phase 4：扩展与清理

- 把核心 Runtime 从实验脚本中收敛；
- outputs/runtime/evidence/reports 分层；
- 再评估 dense retrieval、GraphRAG、多 Agent。

## 12. 暂缓功能

- 向量数据库产品选型；
- GraphRAG 默认底座；
- 多 Agent trajectory orchestration；
- 在线强化学习；
- 自动写回生产知识库；
- 开放式零日发现；
- Harbor 作为唯一 sandbox；
- UI/database/service API。

## 13. 风险与停止条件

| 风险 | 观测 | 停止/回退条件 |
|---|---|---|
| Retrieval 污染 | false positive 或错误版本引用增加 | Both 连续劣于 Skill-only，回退只读检索并修 provider |
| Skill 固化错误 | hidden/negative regression | reject + rollback，相关 atom quarantine |
| Router 无收益 | 固定策略与 router 打平且成本更高 | 保留规则 baseline，不训练复杂 router |
| Verifier 自证 | 内部分高、外部测试失败 | 外部 outcome 一票否决 |
| 轨迹递归漂移 | 同源 evidence 被重复采样 | lineage 去重，暂停自动 proposal |
| 工程失控 | 新模块无独立实验贡献 | 不合入核心 Runtime |

## 14. 第一阶段交付物

设计冻结后，最值得实现的只有：

1. 核心 contracts；
2. 一个只读 Knowledge Provider；
3. 一个四路 rule router；
4. Retrieval Receipt 写入 Evidence Bundle；
5. 一个 12-case P/K/H/N 小矩阵。

这些足以判断混合结构是否值得继续，不需要先建设完整 RAG 平台。
