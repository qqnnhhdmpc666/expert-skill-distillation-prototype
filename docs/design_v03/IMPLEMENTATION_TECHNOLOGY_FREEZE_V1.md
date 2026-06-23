# Implementation Technology Freeze V1

状态：`core_local_implemented_external_qualification_pending`

本文件仍是规范性目标，但不再把已经落地的本地核心写成“尚未实现”。当前
`src/expert_skill_system/` 已具备内容寻址 Artifact Store、SQLite metadata、分阶段
Compiler、ReleaseBundle、本地 Runtime、晋升/拒绝/按原 digest 回滚和 `eskill` CLI。
尚未转正的是成熟 AgentHost、公开任务原生 evaluator 与 Harbor parity；这些外部门
未通过前，不得把本地 reference/deterministic 路径写成 Agent 或外部任务有效性。

上位规范：`SYSTEM_ARCHITECTURE_FREEZE_V1.md`

适用范围：Python dependency-advisory walking skeleton。

## 1. 决策摘要

V1 采用本地优先的模块化单体：

```text
one Python distribution
+ one primary CLI
+ content-addressed filesystem artifact store
+ SQLite metadata and binding store
+ frozen OSV JSON/SQLite projection
+ optional external evaluation backends
```

V1 不采用微服务、远程向量数据库、消息队列、Kubernetes、Web UI、通用 Repo index 或多智能体编排。

这是实现形态冻结，不代表所有具体 Agent/model 已经选定。需要经验资格测试的选择使用 `qualification_required`，不能用临时代码暗中决定。

## 2. 进程与包边界

### 2.1 单进程主路径

Build、registry、local runtime 和 inspect 在同一 Python 进程内通过显式 service interface 调用。LLM API、Agent host、Harbor 和外部 scanner 是进程外 adapter。

```text
eskill CLI
  -> Application Services
     -> Compiler / Runtime / Evaluation / Evolution
        -> ArtifactStore + MetadataStore + Providers
        -> external adapters when explicitly selected
```

禁止核心 service 通过 `subprocess` 调用仓库内另一个 Python 脚本。`subprocess` 只允许用于外部工具、Agent host、container harness 和 legacy compatibility command。

### 2.2 Python namespace

目标 namespace：

```text
src/expert_skill_system/
  core/
  sources/
  knowledge/
  compiler/
  skills/
  runtime/
  evaluation/
  evolution/
  registry/
  domains/python_advisory/
  cli/
```

迁移期间：

- `skill_deployment` 保留为旧 CLI 和原型 API compatibility facade。
- 新对象不得继续堆入单个 `schemas.py`、`runner.py` 或 `cli.py`。
- 不做一次性改名；每个 walking-skeleton slice 迁移一条真实调用链。
- 旧脚本只有在被新 application service 调用或明确标为 `legacy_experiment` 时保留。

## 3. 存储冻结

### 3.1 Workspace 布局

默认 runtime state 位于项目或用户指定目录的 `.eskill/`：

```text
.eskill/
  artifacts/sha256/<prefix>/<digest>
  metadata.sqlite
  projections/
    osv/<snapshot_digest>/osv.sqlite
  sessions/<session_id>/
  exports/
  locks/
```

Git 仓库中的 `outputs/` 只用于显式导出的实验或 review artifact，不再承担 runtime truth。`.eskill/` 默认不入 Git；可复现实验通过 manifest 导出精确 artifact closure。

### 3.2 Artifact Store

不可变 payload 使用内容寻址文件系统。`ArtifactRef` 至少包含：

```yaml
artifact_id: string
digest: sha256:...
media_type: string
schema_version: string
size_bytes: integer
```

规则：

- 写入时 canonicalize、计算 digest、原子 rename。
- digest 相同可复用，digest 不同不得覆盖。
- Bundle rollback 重新绑定既有 digest，不重新编译“近似旧版本”。
- 大型 source-native index 由 adapter 持有；中央 store 保存 snapshot 和版本化句柄。

### 3.3 SQLite Metadata Store

SQLite 使用 WAL、foreign keys 和显式 transaction。最小表：

```text
artifact
source_snapshot
evidence_index
dependency_edge
build_record
evaluation_attestation
active_binding
deployment_event
session
cost_event
decision_record
```

SQLite 保存索引和可变绑定，不保存大型 artifact payload。`active_binding` 使用 generation 做 compare-and-swap。`deployment_event` 和 `decision_record` append-only。

V1 不引入 SQLAlchemy。使用标准库 `sqlite3`、显式 migration version 和 repository classes；当 schema 复杂度超过单文件 migration 可维护边界时再提交 ADR。

## 4. V1 Source 与 Knowledge 技术

### 4.1 实现的 Adapter

| Adapter | 输入 | 实现 | 输出 |
|---|---|---|---|
| `ExpertDocumentAdapter` | UTF-8 Markdown/TXT | heading/list/code-fence aware parser | `SourceSnapshot` + section-level `EvidenceUnit` |
| `RequirementsAdapter` | pinned `requirements.txt` | 受限 grammar + `packaging` 的 name/version/marker primitives | normalized dependency inventory |
| `OSVSnapshotAdapter` | frozen OSV JSON records | validation + deterministic SQLite materialization | typed advisory query provider |

V1 不实现 PDF OCR、网页爬虫、多模态、通用 RepositoryAdapter。RepositoryAdapter 只保留 Protocol 和 `unsupported_in_v1` capability declaration。

### 4.2 Knowledge Provider

V1 provider：

```text
ExpertSectionProvider: exact section/full-document read
OSVSnapshotProvider: typed SQLite query
BuildCaseProvider: JSONL + metadata filter
```

短专家规范不需要 embedding。只有预注册材料超过 context threshold 且 exact/section baseline 不满足预算时，才资格测试 BM25。V1 不引入向量数据库或 GraphRAG。

### 4.3 OSV snapshot

正式实验只使用 digest-pinned snapshot。每条 query 记录：

```text
snapshot_digest
provider_version
query_contract_digest
normalized_parameters
result_digest
elapsed_ms
```

Live OSV API 可用于开发抓取，但其结果必须先 materialize 成 snapshot 才能进入正式效果结论。

## 5. 核心 Protocol

以下 Protocol 在编码前冻结；具体实现可替换：

```python
class SourceAdapter(Protocol):
    def parse(self, source_ref: SourceRef) -> SourceSnapshot: ...
    def materialize(self, snapshot: SourceSnapshot) -> list[EvidenceUnit]: ...

class CompilerStage(Protocol):
    def run(self, inputs: StageInputs, context: BuildContext) -> StageResult: ...

class KnowledgeProvider(Protocol):
    def query(self, request: KnowledgeQuery) -> EvidenceEnvelope: ...

class SkillCompiler(Protocol):
    def compile(self, knowledge_ir: KnowledgeIR, profile: SkillProfile) -> SkillIR: ...

class AgentHost(Protocol):
    def execute(self, request: AgentExecutionRequest) -> ExecutionTrace: ...

class RuntimeVerifier(Protocol):
    def verify(self, trace: ExecutionTrace, contract: TaskContract) -> VerificationResult: ...

class ArtifactRegistry(Protocol):
    def put(self, artifact: Artifact) -> ArtifactRef: ...
    def get(self, ref: ArtifactRef) -> Artifact: ...
    def promote(self, binding: BindingKey, digest: str, expected_generation: int) -> ActiveBinding: ...
    def rollback(self, binding: BindingKey, target_digest: str, expected_generation: int) -> ActiveBinding: ...
```

`ArtifactRegistry` 的 `promote/rollback` 是 application transaction，不允许 Compiler 或 Evolution Builder 直接调用数据库更新 active row。

## 6. Runtime 与 Agent 决策

### 6.1 两类执行后端

```text
ReferenceDecisionBackend
AgentHostBackend
```

`ReferenceDecisionBackend` 使用相同 TaskContract、Knowledge Provider、domain primitives 和 outcome schema，提供确定性 plumbing/evaluator baseline。它不是 Agent 效果证据。

`AgentHostBackend` 才执行 Agent-compatible Skill artifact。这样避免为了一个结构化 dependency pair 任务，强迫核心 runtime 依赖 coding-agent 会话实现。

### 6.2 Agent host 资格测试

候选：Codex CLI 为 primary candidate，OpenHands 为 secondary candidate。二者在 held-out 前运行相同 3-5 个公开/本地非 oracle smoke tasks，测量：

- unattended invocation；
- tool/file/shell capability；
- permission enforcement；
- structured output reliability；
- trajectory completeness；
- timeout/cancellation；
- Windows/WSL/Docker portability；
- model/provider replacement；
- install and pin reproducibility。

通过后写入 `AGENT_HOST_QUALIFICATION.json`，只冻结一个主宿主和一个 smoke 宿主。资格测试前，不在规范中指定 GPT、DeepSeek 或其他具体模型为唯一选择。

### 6.3 Model role profiles

冻结角色，不先冻结营销名称：

```yaml
model_profile:
  profile_id: string
  role: compiler | runtime_agent | independent_judge
  provider: string
  model_id: string
  endpoint_alias: string
  parameters: {}
  max_input_tokens: integer
  max_output_tokens: integer
  retry_policy_id: string
  prompt_contract_digest: string
  credential_ref: environment_alias
```

密钥不得进入 artifact。Judge model 必须与被评 Compiler 的输出盲化；如果条件允许，Judge provider/model 不与 Compiler 相同。模型矩阵只在 build/dev split 上选定，held-out 后不得调参。

## 7. Knowledge Access 与权限

Runtime 顺序固定：

```text
resolve ActiveBinding and pin Bundle digest
-> load TaskContract
-> resolve Skill artifact
-> compute AllowedScope
-> build bounded QueryPlan
-> resolve KnowledgeAccessBinding
-> execute provider queries
-> execute backend
-> verify
-> commit session trace and outcome
```

```text
AllowedScope = TaskContract scope ∩ Bundle policy ∩ granted permission
EffectiveQuery = AllowedScope ∩ QueryPlan
```

`no_skill` 可以生成受限 QueryPlan，但不能读取 Skill 的隐藏中间产物。Skill 声明 semantic knowledge requirement；物理 provider 由 Bundle binding 决定。

## 8. 失败语义

Domain outcome 外增加 runtime envelope，避免把基础设施失败伪装成 `unresolved`：

```yaml
execution_envelope:
  execution_status: completed | blocked | runtime_failure
  domain_outcome: object|null
  failure:
    category: string|null
    reason_codes: []
    retryable: boolean|null
  session_id: string
  bundle_digest: string
```

规则：

- 合法输入但公告缺失、版本未知或证据冲突：`completed + verdict=unresolved`。
- 输入不属于 V1 grammar：`completed + task_status=parse_error`。
- hard knowledge requirement 越权/过期且策略为 block：`blocked`，无 domain decision。
- bundle 损坏、provider crash、Agent host timeout、schema decode failure：`runtime_failure`。
- `unresolved`、`blocked` 和 `runtime_failure` 都必须保留，不得计为正确的 negative decision。

## 9. Evaluation 技术冻结

三条独立 lane：

1. Deterministic evaluator：schema、digest、lineage、PEP 440/marker、OSV pair verdict、permission、closure。
2. Independent LLM-as-Judge：entailment、unsupported claim、scope overreach、modality mismatch、missing exception；盲化方法名和下游结果。
3. External task evaluator：公开 held-out task 的原生 test/oracle/verifier。

LLM Judge 不能被称为人工专家。OSV-Scanner/Trivy 仅作 cross-check。Harbor 只有通过原 harness parity 后才成为 `HarborEvaluationBackend`，且不进入本地 build 的强依赖。

## 10. CLI 冻结

新 CLI 名称：`eskill`。迁移期 `skill-deploy` 作为 alias 保留。

```text
eskill source add <path> --adapter expert-document
eskill source add <path> --adapter osv-snapshot
eskill build python-advisory --profile compiler-v1
eskill validate bundle <digest> --suite v1-build
eskill promote python-advisory <digest> --expected-generation <n>
eskill run python-advisory --requirements <path> --advisory <id>
eskill inspect session <session-id>
eskill inspect bundle <digest>
eskill history python-advisory
eskill rollback python-advisory <digest> --expected-generation <n>
```

CLI 直接调用 application service，不继续增长“一个子命令转发一个脚本”的模式。实验命令进入 `eskill experiment ...` 或仓库外研究 harness，不污染用户主路径。

## 11. 当前仓库迁移映射

| Current | Decision | Target |
|---|---|---|
| `provenance.py` | 保留 canonical hash 经验，补 media/schema | `core/artifacts.py` |
| `schemas.py` | 作为 legacy schema；不继续膨胀 | versioned models under `core/` |
| `distillation.py` | 保留为 keyword/direct baseline；不能改名冒充 Compiler | `compiler/` staged pipeline |
| `runner.py` | 保留 BackendRunner 经验，拆 host 与 domain runtime | `runtime/backends.py`, `runtime/hosts.py` |
| `evidence.py` | 迁移为 session/evidence ledger writer | `registry/evidence.py` |
| `install_state.py` | JSON registry 作为 migration input | SQLite `active_binding` + immutable bundles |
| `verifier.py` | 保留 controlled verifier；明确 evaluator lane | `evaluation/deterministic.py` |
| `harbor_adapter.py` | 当前是 replay，不得标为正式 backend | `evaluation/harbor.py` after parity |
| `cli.py` | 冻结新增 legacy 子命令 | thin `eskill` application CLI |
| `scripts/` | 分类为 migrate / experiment / retire | services + `experiments/legacy/` |

## 12. 暂缓

```text
vector database
GraphRAG
general repository index
multi-agent orchestration
RL/contextual bandit
automatic semantic impact analysis
live OSV in formal evaluation
distributed registry
service API
Web UI
Harbor as product runtime
```

## 13. 完成条件

本文件从 `specified_not_implemented` 转为 `implemented`，必须同时满足：

- `.eskill` artifact/SQLite state 真实驱动 build、run、promote 和 rollback；
- 旧 `outputs/` JSON 不再是 runtime truth；
- V1 三个 Adapter 与三个 Provider 有 contract test；
- runtime envelope 区分 unresolved、parse error、blocked、runtime failure；
- CLI 主路径不通过仓库内脚本转发；
- Agent/Harbor 采用状态与资格测试结果一致；
- clean environment 能执行 `WALKING_SKELETON_V1.md` 的完整命令序列。
