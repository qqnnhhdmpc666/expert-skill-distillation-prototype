# v0.2 Knowledge Model and Contracts

## 1. 建模原则

1. 来源、派生知识、Skill、轨迹和评价必须是不同对象。
2. 原始来源和 observed trajectory 不可原地修改，只能追加新版本或派生记录。
3. 任何进入 Skill 的规则必须能追溯到 source/trajectory/evaluation。
4. 检索结果必须带 receipt，不能只保留最终 prompt。
5. 时间、环境、权限和适用范围是一等字段。
6. verifier-only oracle 不得进入 Agent、router、retriever 或 candidate generator。

## 2. 核心对象

### 2.1 `SourceRecord`

表示不可变原始来源。

```yaml
source_id: src_sha256
source_type: document | repository | api_snapshot | database_snapshot | trajectory
uri: string
content_hash: sha256
captured_at: timestamp
publisher: string|null
license: string|null
trust_tier: official | expert | community | unknown
valid_from: timestamp|null
valid_until: timestamp|null
sensitivity: public | internal | restricted
access_policy_id: string
parser_version: string
metadata: {}
```

关键约束：API 或网页内容必须以 snapshot 建模，不能只保存会变化的 URL。

### 2.2 `KnowledgeAtom`

表示从来源中提取的最小可引用知识单元，而不是任意固定长度 chunk。

```yaml
atom_id: atom_sha256
atom_type: procedure | fact | constraint | case | observation | hypothesis
content: string
source_refs:
  - source_id: src_sha256
    span: page/line/symbol/json-pointer
scope:
  task_families: []
  repositories: []
  ecosystems: []
  versions: []
temporal:
  valid_from: timestamp|null
  valid_until: timestamp|null
  volatility: low | medium | high
procedurality: low | medium | high
environment_dependence: low | medium | high
confidence: unverified | weak | supported | externally_validated
contradiction_group: string|null
security_label: public | internal | restricted
created_by: parser/model/human id
created_at: timestamp
```

`KnowledgeAtom` 不等于向量条目。索引是它的派生视图。

### 2.3 `KnowledgeFormDecision`

显式记录知识的长期保存/编译形态。它是 control-plane 决策，不等于某次任务的 runtime route。

```yaml
decision_id: string
atom_ids: []
decision: skill | retrieval | both | trajectory_only | discard
reasons: []
policy_id: form_policy_v1
policy_mode: rule | llm | learned
agent_profile_id: string
task_distribution_id: string
evidence_refs: []
review_status: proposed | approved | rejected
created_at: timestamp
```

初始规则基线：

| 条件 | 默认形态 |
|---|---|
| 高程序化、低波动、跨任务复用 | Skill |
| 高波动、事实型、版本/环境相关 | Retrieval |
| 稳定流程需要动态参数或案例 | Both |
| 单次异常、价值未验证 | Trajectory-only |
| 无来源、冲突未解、越权 | Discard/Quarantine |

这只是可证伪基线，不是最终研究算法。

同一个 Atom 可以长期保留在 Knowledge Store，同时其稳定程序片段被编译进 Skill；此时 `both` 必须记录两个派生对象和共同来源，不能复制后丢失 lineage。

### 2.4 `SkillPackageV2`

现有 `SkillPackage` 应兼容扩展为：

```yaml
skill_id: string
version: string
task_contract:
  supported_families: []
  preconditions: []
  out_of_scope: []
workflow:
  steps: []
  recovery: []
knowledge_policy:
  required_sources: []
  retrieval_triggers: []
  query_templates: []
  evidence_sufficiency: []
tool_policy:
  allowed_tools: []
  denied_actions: []
output_contract: []
trace_contract: []
source_atom_refs: []
validation_refs: []
supersedes: string|null
rollback_to: string|null
status: candidate | active | quarantined | deprecated | retired
```

Skill 可以包含“遇到依赖版本问题时查询官方 advisory provider”这种稳定流程，但不能把某日的 CVE 列表固化为永久规则。

### 2.5 `TaskEnvelope`

```yaml
task_id: string
task_family_hint: string|null
instruction: string
target_refs: []
environment_ref: string|null
allowed_actions: []
denied_actions: []
budget:
  model_tokens: int|null
  retrieval_calls: int|null
  tool_calls: int|null
  wall_time_seconds: int|null
visibility:
  agent_visible_fields: []
  evaluator_only_fields: []
```

### 2.6 `AgentProfile`

知识价值依赖 Agent 本身。必须记录其基础能力，避免把模型升级误认为知识系统收益。

```yaml
agent_profile_id: string
backend_id: string
model_id: string
model_snapshot: string|null
context_limit: int|null
tool_capabilities: []
native_repository_search: bool
native_web_or_api_access: bool
skill_runtime_support: bool
known_limitations: []
profile_hash: sha256
```

所有 form decision、runtime route 和 paired evaluation 都引用固定 `agent_profile_id`。

### 2.7 `KnowledgeAccessPlan`

这是 per-task runtime 决策，和 `KnowledgeFormDecision` 分离。长期存成 Retrieval 的知识，在某个无需外部事实的任务中仍可选择不检索。

```yaml
plan_id: string
task_id: string
agent_profile_id: string
route: no_external_knowledge | full_context | retrieval | skill_only | skill_and_retrieval
providers: []
queries: []
budget: {}
stop_conditions: []
rationale: []
```

### 2.8 `RetrievalReceipt`

每次检索必须写 receipt：

```yaml
receipt_id: string
plan_id: string
provider_id: bm25_docs | dense_docs | repo_rg | ast_index | advisory_api | trace_index
query: string
filters: {}
requested_at: timestamp
snapshot_refs: []
candidates:
  - atom_id: string
    sparse_score: float|null
    dense_score: float|null
    rerank_score: float|null
    selected: bool
selection_method: rrf | reranker | exact | structured_query
latency_ms: int
cost: number|null
result_hash: sha256
```

不得只保存 Top-k 文本；否则无法分析 retrieval failure、污染和重复信息。

### 2.9 `TrajectoryEvent`

```yaml
run_id: string
event_id: string
sequence: int
timestamp: timestamp
event_type: observe | retrieve | read | tool_call | tool_result | model_action | parse_repair | checkpoint | finish
actor_id: string
parent_event_ids: []
input_refs: []
output_refs: []
payload_hash: sha256
payload: {}
visibility: agent | internal | evaluator_only
trajectory_kind: observed | synthesized | replay
```

多 Agent 将来可用 `parent_event_ids` 表示非线性编排；第一阶段仍按单 Agent sequence 执行。

### 2.10 `EvaluationRecord`

```yaml
evaluation_id: string
run_id: string
evaluator_type: external_test | benchmark_native | static_analysis | internal_diagnostic | human_review
evaluator_version: string
input_hashes: []
outcome: pass | fail | partial | infra_blocked | inconclusive
metrics: {}
failure_taxonomy: []
oracle_visibility: evaluator_only
artifact_refs: []
```

规则：`external_test` 和 `benchmark_native` 优先于 `internal_diagnostic`；内部 verifier 不能覆盖环境失败。

### 2.11 `LearningProposal`

```yaml
proposal_id: string
proposal_type: skill_edit | knowledge_add | knowledge_correct | knowledge_retire | no_change
input_trajectory_refs: []
input_evaluation_refs: []
allowed_input_classes: [public_feedback, evidence_summary, limitation_summary]
forbidden_oracle_access_confirmed: true
patch: {}
risk_assessment: {}
heldout_plan_id: string
```

### 2.12 `PromotionDecision`

保留现有 gate 思路，但增加知识形态与外部结果：

```yaml
decision: promote | reject | quarantine | rollback | retire | insufficient_evidence
paired_task_results: []
negative_control_delta: number
external_outcome_delta: number|null
cost_delta: number|null
scope_violation: bool
retrieval_pollution_delta: number|null
reason: string
```

## 3. 模块接口草案

以下只是冻结接口，不是本轮实现：

```python
class SourceConnector(Protocol):
    def snapshot(self, request: SourceRequest) -> SourceRecord: ...

class KnowledgeCompiler(Protocol):
    def extract(self, source: SourceRecord) -> list[KnowledgeAtom]: ...

class KnowledgeFormPolicy(Protocol):
    def decide(self, atoms: list[KnowledgeAtom], context: FormContext) -> KnowledgeFormDecision: ...

class RuntimeKnowledgeRouter(Protocol):
    def route(self, task: TaskEnvelope, agent: AgentProfile, catalog: KnowledgeCatalog) -> KnowledgeAccessPlan: ...

class KnowledgeProvider(Protocol):
    def search(self, query: RetrievalQuery) -> RetrievalReceipt: ...

class SkillCompiler(Protocol):
    def compile(self, atoms: list[KnowledgeAtom], decision: KnowledgeFormDecision) -> SkillPackageV2: ...

class AgentBackend(Protocol):
    def run(self, task: TaskEnvelope, skill: SkillResolution, knowledge: KnowledgeAccess) -> RunHandle: ...

class Evaluator(Protocol):
    def evaluate(self, run: RunHandle) -> EvaluationRecord: ...

class ExperienceMiner(Protocol):
    def propose(self, trajectories: list[TrajectoryEvent], evaluations: list[EvaluationRecord]) -> list[LearningProposal]: ...
```

## 4. 存储逻辑

逻辑上保持三个 registry/store：

- Skill Registry：版本、active pointer、状态和 rollback；
- Knowledge Store：Source、Atom、索引、时间与权限；
- Trajectory Store：append-only event、run、evaluation 和 proposal。

物理上 MVP 可共用 SQLite + 文件内容寻址目录，不要求三套数据库。逻辑分离比物理分离更重要。

## 5. 更新与退休

### Skill 更新

必须经过多轨迹/独立任务证据、paired comparison、negative control 和 held-out gate。

### Knowledge 更新

- 新 snapshot 不覆盖旧 snapshot；
- 冲突知识进入同一 contradiction group；
- 高波动知识设置 TTL 或 `valid_until`；
- 被官方来源否定时标记 superseded，不物理删除审计历史。

### Trajectory 归档

- 原始 observed trajectory 只追加；
- 可生成脱敏 case summary 进入 Knowledge Store；
- 生成 Skill candidate 时记录所用 trajectory id；
- 失败轨迹不能因 candidate 被拒而删除。

## 6. 权限与安全

- Source、Atom、Receipt 和 Event 均带 sensitivity/access policy；
- restricted 内容不能进入公开 Skill；
- retrieval provider 必须按 task principal 过滤；
- prompt/model call artifact 不保存 API key；
- 安全 adapter 默认 defensive-only；
- evaluator-only oracle 不进入 retrieval index；
- 真实仓库必须有授权声明和 sandbox boundary。

## 7. 设计冻结检查

在实现前，用 3 个手写示例验证 schema：

1. 稳定 upload 审查流程 -> Skill；
2. 某依赖版本的当前 CVE -> Retrieval；
3. “按固定流程定位依赖，再查询当前 advisory” -> Both。

若三个例子仍需把核心字段塞入任意 `metadata`，说明契约尚未冻结。
