# v0.2 Technology Decisions and Related Work

## 1. 决策原则

技术选型按以下顺序判断：

1. 是否对应一个不可替代的问题；
2. 是否能形成可归因实验；
3. 是否可控、可复现、可审计；
4. 是否与当前数据规模匹配；
5. 维护与迁移成本；
6. 最后才是“是否先进”。

本轮不选择具体向量数据库，不引入 GraphRAG，不引入多 Agent 框架。

## 2. 同期工作给出的架构信号

检索日期：2026-06-19。以下资料均来自论文页或官方代码仓库；2026 年 Skill 工作目前应按预印本/近期工作对待，不把摘要结论直接当作本项目证据。

| 工作 | 核心信号 | 对本项目的启发 | 不应照搬之处 |
|---|---|---|---|
| [Self-RAG](https://arxiv.org/abs/2310.11511) | 检索应按需触发，并对检索与生成自反思 | “是否检索”应是显式动作 | 依赖训练 reflection tokens，不适合当前 frozen-model MVP |
| [Adaptive-RAG](https://arxiv.org/abs/2403.14403) | 按查询复杂度选择 no-retrieval、单步或迭代检索 | 先做规则/分类器 router baseline | QA complexity 不能直接代表工具任务的知识需求 |
| [CRAG](https://arxiv.org/abs/2401.15884) | 检索质量需评估，失败时触发纠正动作 | Retrieval Receipt 应记录质量与 fallback | 自评器不能成为高风险安全任务唯一真值 |
| [RAG vs Long Context](https://arxiv.org/abs/2407.16833) | 长上下文更强但更贵，路由可兼顾成本 | full-context 必须作为 baseline，不默认切块检索 | 结论依赖模型和数据，不应普遍化 |
| [RAGRouter-Bench](https://arxiv.org/abs/2602.00296) | query-corpus compatibility 决定 RAG 范式；不存在单一最优方案 | router 输入应包含任务和 corpus 特征 | 当前为 2026 预印本，且以生成任务为主 |
| [RepoCoder](https://arxiv.org/abs/2303.12570) | 代码检索与生成可迭代互相修正 | repository search 应支持多轮 query reformulation | 代码补全不等同于漏洞定位 |
| [CodeRAG-Bench](https://arxiv.org/abs/2406.14497) | 多来源检索能增益，但 retriever 和 context integration 仍是瓶颈 | 必须区分 retrieval quality 与 agent use quality | 不能只用最终代码分数解释检索机制 |
| [SWE-agent](https://arxiv.org/abs/2405.15793) / [official repo](https://github.com/SWE-agent/SWE-agent) | Agent-computer interface 显著影响仓库任务表现 | 工具接口、文件导航和测试执行与 RAG 同等重要 | 不应把其 offensive 用途引入本项目安全边界 |
| [Agent Workflow Memory](https://arxiv.org/abs/2409.07429) | 可从轨迹诱导可复用 workflow，并按任务选择 | 轨迹可形成 Skill，但需选择与泛化验证 | web workflow 与安全代码任务的迁移需重新验证 |
| [Trace2Skill](https://arxiv.org/abs/2603.25158) / [official repo](https://github.com/Qwen-Applications/Trace2Skill) | 并行多轨迹归纳优于顺序补丁；可压缩 recurring failure | 保留多轨迹归纳、成功/失败差异化诊断 | 不能替代本项目的外部效用 gate |
| [EvoSkill](https://arxiv.org/abs/2603.02766) / [official repo](https://github.com/sentient-agi/EvoSkill) | 失败分析、结构化 Skill、held-out Pareto selection | 候选必须在 held-out 上产生净收益 | 不应把生成候选本身称为进化成功 |
| [SkillOpt](https://arxiv.org/abs/2605.23904) / [official repo](https://github.com/microsoft/SkillOpt) | bounded edit、rejected buffer、严格 validation gate | 延续有限编辑与拒绝缓冲 | 高质量稳定 reward 是前提，当前 verifier 仍不足 |
| [SkillRouter](https://arxiv.org/abs/2603.22455) | 大型 Skill 库路由需要 full-text retrieve/rerank | 将来 Skill routing 可复用 retrieval 技术 | 当前 Skill 数量很小，不值得先建大规模 Skill index |
| [CVE-Bench](https://arxiv.org/abs/2503.17332) | 真实漏洞 benchmark 需要可复现实例和 sandbox | 强化 benchmark-native evaluator 思路 | 目标是 exploit，和本项目 defensive-only 边界冲突，不作为首批任务 |
| [CyberSecEval 4 / AutoPatchBench](https://github.com/meta-llama/PurpleLlama/tree/main/CybersecurityBenchmarks) | 官方防御性补丁任务可提供外部 evaluator | 适合作为后续安全修复证据 | 本地 approximation 不能称作官方结果 |

综合判断：现代 RAG 的关键不是“embedding + Top-k”，而是 source-aware access、adaptive routing、quality correction、iterative search、long-context fallback 和成本约束。

引用信息：

- Asai et al., 2023, *Self-RAG*（ICLR 2024）。
- Jeong et al., 2024, *Adaptive-RAG*（arXiv preprint）。
- Yan et al., 2024, *Corrective Retrieval Augmented Generation*（arXiv preprint）。
- Li et al., 2024, *Retrieval Augmented Generation or Long-Context LLMs?*（arXiv preprint）。
- Wang et al., 2026, *RAGRouter-Bench*（arXiv preprint）。
- Zhang et al., 2023, *RepoCoder*（repository-level code completion work）。
- Wang et al., 2024, *CodeRAG-Bench*（arXiv preprint）。
- Yang et al., 2024, *SWE-agent*（NeurIPS 2024）。
- Wang et al., 2024, *Agent Workflow Memory*（arXiv preprint）。
- Ni et al., 2026, *Trace2Skill*（arXiv preprint，v5 updated 2026-06-04）。
- Alzubi et al., 2026, *EvoSkill*（arXiv preprint）。
- Yang et al., 2026, *SkillOpt*（arXiv preprint）。
- Zheng et al., 2026, *SkillRouter*（arXiv preprint）。
- Zhu et al., 2025, *CVE-Bench*（arXiv preprint；其 exploit 目标不属于本项目首批安全边界）。

## 3. 文档解析与知识单元

### 候选

- 原生解析：Markdown/JSON/YAML/HTML/PDF 各用结构化 parser；
- 通用文档框架：Unstructured、LlamaIndex/LangChain loaders；
- 代码：Tree-sitter、LSP/SCIP，而不是文本 chunker。

### 决策

MVP 采用“原生 parser + 明确 SourceRecord”的薄层：

- Markdown/文本按标题、列表、代码块切分；
- JSON/YAML 保留 JSON Pointer；
- PDF 只在来源明确且版面可控时接入；
- 代码不转成普通文档块。

暂不引入大型 ingestion framework，避免其隐含 chunk/schema 成为系统真值。

## 4. 文本知识检索

### 基线层

- 关键词：SQLite FTS5/BM25；
- 过滤：来源、版本、时间、权限、任务族；
- exact lookup：ID、CVE、package/version、symbol。

### 增强层

- dense embedding：只作为召回通道；
- sparse+dense 用 Reciprocal Rank Fusion；
- reranker 对小候选集重排；
- query reformulation 由 Agent 在预算内多轮执行；
- Retrieval Receipt 记录每层分数和选择。

### 决策

先实现 BM25/exact + provider interface 的实验基线，再决定 embedding 模型。原因：当前首批安全任务含大量符号、版本和 ID，纯 dense 不是可靠默认。

## 5. 代码仓库知识访问

按成本从低到高：

1. `rg` / file glob / manifest lookup；
2. Tree-sitter symbol/AST index；
3. LSP/SCIP definition/reference/call hierarchy；
4. 语言专用静态分析、dataflow/call graph；
5. 必要时再物化图查询。

推荐 MVP：`rg + Tree-sitter optional adapter + test runner`。调用图不是默认知识库；只有任务需要 reachability/dataflow 且实验表明文本/AST 不足时才加入。

## 6. Reranker

候选：

- 规则/字段优先级；
- cross-encoder；
- LLM reranker；
- task outcome learned reranker。

决策：第一阶段以可复现的 RRF + 小型 cross-encoder/API reranker 为候选实验，不把 LLM reranker 默认用于所有查询。高风险事实必须经过来源/版本过滤，相关性分高不能覆盖权限和时效规则。

## 7. 长上下文

完整材料直接输入必须是正式 baseline。路由条件可包括：

- corpus 小且可放入预算；
- 信息分散、检索容易漏掉 bridge evidence；
- 原文结构重要；
- 隐私和权限允许。

长上下文不是 Knowledge Store 的替代，因为仍需 snapshot、权限、版本和访问证据。

## 8. 轨迹存储与检索

### 存储

- 原始事件：append-only JSONL 或 Parquet；
- 索引：SQLite 表记录 run/task/event/source/evaluation；
- 大 payload：内容寻址文件；
- case summary：单独 KnowledgeAtom，不覆盖原始轨迹。

### 检索

- 先按 task family、tool、failure taxonomy、environment、outcome 过滤；
- 再做文本/embedding 相似度；
- 检索 unit 可是 episode、subtrajectory 或 failure-recovery pair；
- 成功和失败轨迹都必须可检索。

不建议直接把每个 event embedding 后 Top-k；它会丢失因果顺序和工具结果边界。

## 9. Agent Backend

当前 `BackendRunner` 与 `ExecutionBackend` 应统一为：

- `AgentBackend`：模型和 action loop；
- `ToolProvider`：文件、搜索、命令、API；
- `SandboxBackend`：隔离执行；
- `KnowledgeProvider`：知识访问；
- `Evaluator`：结果判断。

模型 provider 应保持 OpenAI-compatible adapter，但 HTTP、重试、usage、secret handling 只实现一次。

## 10. Sandbox

优先级：

1. benchmark-native sandbox/evaluator；
2. Docker 本地可复现实例；
3. Harbor 作为统一任务适配层；
4. 无沙箱本地执行仅用于低风险开发。

Harbor 不应替代 benchmark-native evaluator，也不应成为知识存储层。

## 11. Verifier 与 Reward

分为三层：

1. **Contract validator**：JSON/schema/trace/provenance；
2. **Diagnostic checker**：coverage、evidence grounding、retrieval quality、scope；
3. **Outcome evaluator**：测试、patch acceptance、benchmark-native result、人工评审。

promotion 应优先使用第三层，并把前两层作为 veto 或诊断。不要先设计一个人工加权总分。初期使用：

- paired pass/fail；
- win/tie/loss；
- false-positive/non-regression veto；
- Pareto frontier；
- bootstrap confidence interval 或配对二项检验。

## 12. Provenance、版本与权限

- 内容寻址 hash；
- source snapshot 与 index version 分开；
- Skill、knowledge snapshot、Agent、model、tool、evaluator 均记录版本；
- access decision 写入 receipt；
- restricted source 不得进入公开 artifact；
- 删除采用 tombstone/retired 状态，保留审计链。

## 13. 为什么现在不选 GraphRAG

[Microsoft GraphRAG](https://github.com/microsoft/graphrag) 是有价值的图式 RAG 系统，但当前仓库尚未证明：

- 任务需要全局社区摘要；
- 实体关系图优于 repo-native symbol/call tools；
- 图构建成本能被任务收益抵消；
- 图的更新与权限模型已清楚。

因此图结构应作为 provider，而不是系统底座。只有在跨文档实体关系或仓库调用链任务上出现可重复增益时再启用。

## 14. 当前技术冻结建议

```text
Store: file snapshots + SQLite metadata/FTS5 (MVP)
Text retrieval: exact/filter + BM25 baseline; dense/rerank behind interface
Code access: rg + repository-native tools; AST optional
Trajectory: append-only events + indexed episode metadata
Agent: one tool-using backend contract
Sandbox: benchmark-native first, Docker adapter second
Verifier: contract + diagnostic + outcome three-layer split
GraphRAG/vector DB/multi-agent: deferred until measured need
```
