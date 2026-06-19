# v0.2 Design Review Summary

更新日期：2026-06-19
结论状态：`architecture_research_complete / implementation_not_started / design_freeze_pending`

## 1. 当前方案最值得保留的是什么

最值得保留的不是某个安全 Skill，也不是当前固定 capability registry，而是已经形成的 **可审计 Skill 生命周期控制平面**：

- Skill Package、版本、安装、active pointer 和 rollback；
- task-conditioned activation 与 out-of-scope guard；
- Evidence Bundle、hash/provenance 和失败保留；
- Candidate、rejected buffer、strict held-out gate；
- Agent-visible 与 verifier-only 的隔离意识；
- 不把 infra blocked、replay 或 negative result 包装成成功。

这些能力能成为新架构的 Skill Registry、Evidence Ledger 和 Promotion Control 基础。

## 2. 最大结构性缺口是什么

最大缺口不是“没有向量数据库”，而是以下五项尚未成为一等对象：

1. Source Record；
2. Knowledge Atom；
3. 长期知识形态决策与 per-task runtime route；
4. Knowledge Access Plan 与 Retrieval Receipt；
5. observed trajectory 到 Skill / case knowledge 的双向更新契约。

当前 open-world distillation 仍把材料投影到固定 `CAPABILITY_SPECS`，因此更接近 bounded closed-vocabulary compilation，不是开放知识建模。

另一个结构性问题是核心与实验混居：约 110 个脚本、2.7 万行实验编排和 7,000 余个已跟踪 output 文件使 canonical Runtime 难以辨认。这个问题应在契约冻结后分阶段清理，不能现在大搬家。

## 3. 是否应该引入 RAG，以及应是什么形态

应该引入，但不应引入传统固定链：

```text
chunk -> embedding -> Top-k -> prompt concat
```

推荐形态是 **source-aware adaptive knowledge access**：

- exact/filter/BM25 处理 ID、版本、符号和明确术语；
- dense retrieval 补语义召回；
- reranker 在小候选集上重排；
- Agent 可多轮改写查询、读取来源并根据证据充足度停止；
- repo 使用 `rg`、symbol/AST/LSP、测试和静态分析等原生工具；
- API/数据库走原生结构化查询；
- 小 corpus 保留 full-context baseline；
- 每次访问写 Retrieval Receipt；
- GraphRAG 只作为未来 provider，不作为默认底座。

RAG 的作用是给 Skill 提供动态参数、事实、案例和环境证据。Skill 的作用是规定稳定 workflow、工具策略、边界和检索触发。两者不是替代关系。

## 4. 怎样兼顾通用核心和漏洞挖掘落地

采用 **双平面 + adapter**：

### 通用核心

- 知识、任务、轨迹、评价契约；
- Knowledge Form Policy；
- Skill Registry / Knowledge Provider / Trajectory Store 接口；
- Agent Backend、Evidence Bundle、promotion/rollback；
- experiment assignment 和 leakage control。

### Security Adapter

- 安全任务 taxonomy 与 report contract；
- repo search、AST/LSP、dependency/advisory provider；
- defensive sandbox policy；
- patch/test/SAST/benchmark-native evaluator；
- 禁止 exploit、攻击链和未授权目标的边界。

漏洞场景适合作为第一垂直方向，因为工具轨迹、代码证据和测试结果可观测。但第一阶段应从已知漏洞定位、安全审查和补丁验证开始，不直接 claim 开放式漏洞发现。

## 5. 哪些设计必须冻结后才能编码

必须冻结：

1. `SourceRecord`、`KnowledgeAtom`、`AgentProfile`、`TaskEnvelope`、`TrajectoryEvent`、`EvaluationRecord`；
2. 长期 `KnowledgeFormDecision` 与运行时 `KnowledgeAccessPlan` 的不同职责；
3. Knowledge Provider 与 Retrieval Receipt；
4. Skill v2 中的 retrieval trigger、knowledge policy 和 source refs；
5. agent/router/evaluator 的可见字段；
6. observed/synthesized/replay 轨迹分类；
7. internal diagnostic 与 external outcome 的优先级；
8. core 对 security adapter 的单向依赖；
9. P/K/H/N 任务分层和 7 路 baseline；
10. runtime state、fresh run、fixture、publishable evidence 的目录语义。

如果这些未冻结就接向量库，结果很可能是又一条不可归因的实验脚本。

## 6. 第一批最值得实现和验证的功能是什么

只实现一个窄 MVP：

```text
read-only Knowledge Sidecar
+ Source/Atom contract
+ exact/BM25 provider
+ Skill/Retrieval/Both/None rule router
+ Retrieval Receipt in Evidence Bundle
+ 12-case P/K/H/N experiment matrix
```

实验必须比较：

- 无外部知识；
- 完整材料；
- 传统混合检索；
- Agent 主动检索；
- Skill-only；
- Skill + Retrieval；
- Skill + Retrieval + trajectory update。

先证明 Retrieval 对 K 类任务有边际收益、Skill 对 P 类任务有边际收益、Both 对 H 类任务有互补收益，再决定 embedding、reranker、GraphRAG 或 learned router。

## 7. 对当前设想的明确反驳

### 反驳一：不能从“Skill 在某些实验优于 RAG”推出“知识应尽量 Skill 化”

Skill 的优势来自稳定流程压缩；对易变事实和环境例外，固化会制造过期和误导。知识形态必须由任务效用实验决定。

### 反驳二：不能把 trajectory 全部作为 Skill 或 RAG 输入

轨迹含偶然网络错误、模型风格、无效工具调用和私密数据。必须先做 provenance、failure taxonomy、去重、权限与 teaching utility 判断。

### 反驳三：不能让自建 verifier 同时定义能力、生成更新并决定成功

这会形成自证闭环。内部 verifier 应负责 contract/diagnostic，最终任务结果由测试、sandbox 或第三方 evaluator 决定。

### 反驳四：多 Agent 不是轨迹研究成熟度的替代品

当前单 Agent 轨迹 schema、知识访问和 attribution 尚未统一。此时加入多 Agent 会放大混乱，不能自动产生研究创新。

## 8. 推荐决策

```text
推荐目标架构：方案 A，双平面 + 类型化存储 + provider adapters
推荐首个实现：方案 C，只读 Retrieval Sidecar 作为方案 A 的 MVP
第一垂直场景：防御性已知漏洞定位/安全审查/补丁验证
第一研究问题：知识形态决策与 Skill/Retrieval 互补边际效用
暂缓：向量数据库、GraphRAG、多 Agent、在线 RL、自动生产写回
```

## 9. 当前可以和不可以说什么

可以说：

> 仓库已经具备受控、可审计的 Skill 生命周期原型；本轮完成了 Knowledge-Skill-Trajectory 混合架构的仓库审计和设计预研，并给出了可证伪的最小实验方案。

不可以说：

- 已经实现先进 RAG；
- 已经证明混合架构优于 Skill-only 或 RAG-only；
- 已经完成开放知识蒸馏；
- 已经具备真实漏洞挖掘能力；
- 已经冻结 v0.2 架构。

下一步应先由团队审阅并冻结 contracts、dependency direction 和实验矩阵，再开始编码。

## 10. 文档索引

- [SITUATION_ANALYSIS.md](SITUATION_ANALYSIS.md)
- [PROBLEM_DEFINITION.md](PROBLEM_DEFINITION.md)
- [ARCHITECTURE_OPTIONS.md](ARCHITECTURE_OPTIONS.md)
- [KNOWLEDGE_MODEL_AND_CONTRACTS.md](KNOWLEDGE_MODEL_AND_CONTRACTS.md)
- [TECHNOLOGY_DECISIONS.md](TECHNOLOGY_DECISIONS.md)
- [EXPERIMENT_AND_MIGRATION_PLAN.md](EXPERIMENT_AND_MIGRATION_PLAN.md)
