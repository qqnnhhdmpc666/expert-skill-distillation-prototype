# Initial Skill Construction Method Spec

状态：`normative_target_not_yet_implemented`

方法对象：从隔离专家材料构建可验证 Knowledge IR，并投影为 Skill IR 与 Knowledge Projection。

## 1. 方法主张

V1 不把“一次模型调用生成 `SKILL.md`”定义为 Knowledge Compiler。正式方法是有状态、可审计、逐阶段失败的知识编译：

```text
capture
-> segment
-> explicit extraction
-> evidence binding
-> synthesis and conflict preservation
-> limited induction
-> modality projection
-> Skill IR compilation
-> automated source-grounded validation
-> candidate ReleaseBundle
```

每一步产生不可变 artifact。LLM 负责语义理解和候选建议，程序负责输入隔离、schema、证据地址、权限、边界、状态转换和 gate。

## 2. 输入隔离

### 2.1 Compiler 可见输入

- 冻结 expert specification 原文；
- OSV schema/documentation 的冻结版本；
- build split 中预注册的正例、反例和异常例；
- Knowledge/Skill IR schema；
- 本方法固定 prompt contract；
- 明确允许的 domain primitive documentation。

### 2.2 Compiler 禁止输入

- held-out task gold、expected verdict 或 hidden verifier fields；
- 人工整理的 Knowledge IR gold；
- 另一方法生成的 Knowledge IR 或 Skill IR；
- promotion 结果、held-out 分数或 Judge 对其他候选的评价；
- 运行时未授权的 live knowledge；
- candidate 试错后泄漏的 held-out failure details。

每次 build 写 `source_visibility_manifest.json`。任何不可证明来源的输入使该 build `invalid_for_formal_comparison`。

## 3. 统一阶段结果

```yaml
stage_result:
  schema_version: compiler_stage_result.v1
  build_id: string
  stage_id: string
  status: complete | partial | blocked | rejected
  input_refs: []
  output_refs: []
  issue_refs: []
  evidence_request_refs: []
  quarantined_item_refs: []
  model_call_refs: []
  deterministic_tool_refs: []
  metrics: {}
  next_action: continue | acquire_evidence | rebuild | stop
```

`partial` 不是隐式成功。只有 eligible item 进入后续 projection；quarantined item 保留在 build closure，但不进入 active Bundle。

## 4. 阶段契约

### Stage 0: Capture

输入：`SourceRef`。

输出：`SourceSnapshot`、raw digest、capture metadata、license/access/retention policy。

确定性检查：UTF-8 decode、文件边界、hash、source identity、重复 snapshot。Capture 不做知识判断。

失败：无法读取、权限缺失或 retention 不允许保存时 `blocked`。

### Stage 1: Segment

输入：Expert document snapshot。

输出：section/list/code-aware `EvidenceUnit[]`。

V1 规则：

- heading 保留层级路径；
- list item 保留父项和相邻上下文；
- code fence 不按普通段落拆散；
- `must/should/may/must not` 等 modality 原文保留；
- example/counterexample 与对应规则建立候选关系；
- 每个 unit 有 source byte/line span。

不得用 fixed-token chunking 作为唯一分段。过长 section 可以二次切分，但必须保留 parent span。

### Stage 2: Explicit Extraction

输入：EvidenceUnit window、schema、build-domain context。

输出：仅包含来源明确表达的 candidate nodes：

```text
proposition
procedure
constraint
case
```

LLM 输出必须遵循结构化 contract：

```yaml
candidate_node:
  semantic_type: string
  content: object
  modality: must | should | may | must_not
  explicit_evidence_refs: []
  quoted_support_spans: []
  scope_claim: {}
  uncertainty: string|null
```

本阶段禁止补充模型常识。没有 exact support span 的候选直接 quarantine，不进入“稍后再补引用”的默认路径。

### Stage 3: Evidence Binding

输入：candidate nodes、Evidence Ledger。

输出：bound nodes 或 `binding_failure`。

程序检查：

- evidence ref 存在且 digest 匹配；
- support span 落在 EvidenceUnit 内；
- modality 与原句不反转；
- scope 不超出来源可见对象；
- source license/access 允许当前用途。

LLM 可以提出“哪段支持哪条”的建议，最终引用有效性由确定性检查决定。

### Stage 4: Synthesis

输入：bound explicit nodes。

输出：去重但不抹平冲突的 candidate Knowledge IR。

操作：

- semantic-equivalent deduplication；
- procedure step assembly；
- rule/example/counterexample linking；
- exception linking；
- source conflict preservation；
- scope intersection，而非无证据 union；
- stable identity proposal。

冲突节点使用 `contradicts` 和 `validation_status=disputed`。V1 不自动选择“多数来源即真理”。

### Stage 5: Limited Induction

输入：explicit/synthesized nodes 和 build examples。

输出：`derivation_mode=induced|hypothesized` 的候选。

允许：从多个明确案例归纳可检验的 procedure ordering、precondition 或 exception candidate。

禁止：仅凭模型常识扩大 task family、生态、版本范围或权限。

规则：

- induced node 必须引用至少两个独立 evidence/case；
- hypothesized node 不能成为 active Bundle 的 hard dependency；
- 所有 induction 记录生成模型、prompt、输入 refs 和 counterexample search；
- 没有 build-split validation 支持时 quarantine。

### Stage 6: Modality Projection

输入：validated Knowledge IR nodes。

输出：每个 node 的 `ProjectionDecision`。

透明基线：

| 条件 | disposition |
|---|---|
| 稳定、程序性、跨任务复用的 workflow/constraint | `skill` |
| 动态、具体、大规模、版本相关事实 | `knowledge` |
| 稳定执行规则需要运行时事实才能完成 | `both` |
| 无关、证据不足、冲突未解决、越权 | `none` |

模型只可建议 disposition 和 reason；程序检查 eligibility、freshness、scope、evidence sufficiency。V1 不声称该决策已由学习算法最优化。

### Stage 7: Skill IR Compilation

输入：`skill|both` nodes、Skill profile。

输出：Skill IR。

规则映射优先：

```text
procedure -> workflow / partial order
constraint -> constraints / forbidden assumptions
requires -> required evidence / knowledge requirements
exception_to -> exceptions / abstention conditions
case -> examples / counterexamples
scope -> invocation and contraindication
```

LLM 可用于表达压缩，但不能：

- 增加 Knowledge IR 不存在的 hard rule；
- 删除例外、禁用项或 abstention；
- 扩大 capability、permission 或 tool scope；
- 将动态 advisory 事实写进 Skill。

Skill IR 编译后再由同一个 deterministic runtime compiler 生成 Agent-compatible artifact 和 `SKILL.md` view。

### Stage 8: Knowledge Projection

输入：`knowledge|both` nodes 和 structured snapshots。

输出：queryable projection、query schema、provenance manifest。

V1：expert sections 使用 exact/full read；OSV 使用 frozen typed SQLite；build cases 使用 JSONL metadata filter。Skill 与 projection 分别有 digest。

### Stage 9: Automated Source-Grounded Validation

输入：Knowledge IR、Skill IR、projection、source snapshots。

输出：BuildAttestation，不直接 promotion。

四类检查：

1. Deterministic：schema、lineage、digest、evidence span、scope containment、modality、dependency closure。
2. Independent LLM Judge blind review：entailment、unsupported claim、scope overreach、modality mismatch、missing exception。
3. Perturbation：冲突来源、过宽范围、缺失证据、过期规则、断裂引用。
4. Build/dev task evaluation：输出正确性、justified unresolved、false-safe、knowledge access 和 negative control。

不存在人工 Knowledge IR gold；LLM Judge 也不表述为人工专家评价。

## 5. Prompt contract

V1 冻结 prompt contract 的输入输出和禁令，不冻结自然语言措辞。每个 LLM stage 必须包含：

```text
role and stage objective
allowed evidence refs
output JSON schema
forbidden inference list
abstention behavior
scope/modality preservation rule
opaque build/sample ids
```

每次调用保存：model profile、prompt contract digest、rendered prompt digest、input refs、raw response digest、parsed output、token/cost/timing、retry count。密钥和完整私有材料不得写入公开 artifact。

Malformed output：允许按固定 retry policy 做一次 schema-repair call；仍失败则 stage `partial/blocked`，不能由正则猜测关键语义。

## 6. Quarantine 与失败处理

以下情况强制 quarantine：

- 无 exact evidence ref；
- modality mismatch；
- scope overreach；
- 冲突未解决却被提为 hard rule；
- induction 缺少独立案例；
- freshness 失效；
- permission/retention 不允许发布；
- Judge 指出 unsupported claim 且确定性检查无法反证；
- perturbation test 失败。

Quarantine item 保留：原候选、来源、诊断、模型调用和后续 decision。默认不会因为下一次 build 没再生成它而删除历史。

## 7. `direct_to_skill_ir` 基线

基线定义：

```text
same raw materials
-> one-stage direct generation to the same Skill IR schema
-> same deterministic Runtime compiler
-> same Agent-compatible artifact generator
-> same verifier/evaluator
```

它不读取 Compiler 的 segmentation、Knowledge IR、projection decision 或中间结论。允许底层 API 的固定网络/schema retry，但不能增加独立 extraction、synthesis、validation pipeline。

比较两套预注册配置：

- `effectiveness`：各方法合理默认配置。
- `budget_matched`：相同总 input/output tokens、API cost、external access 和 wall-clock envelope；不限制内部调用次数。

另报告 compile、rebuild、runtime、evaluation 和维护成本，以及随任务复用和来源更新的摊销成本。若不存在有限 break-even，必须明确报告。

## 8. Candidate Bundle gate

Build 完成只产生 candidate Bundle。进入 promotion evaluation 前必须满足：

```text
no hard dependency on quarantined/hypothesized nodes
all hard refs resolve to exact digests
deterministic validation pass
source-grounded Judge has no unresolved critical issue
build/dev regression pass
negative controls non-regressing
permission request non-expanding without evidence
```

Promotion 仍由独立 application transaction 完成。Compiler 无权修改 ActiveBinding。

## 9. 当前实现差距

当前 `src/skill_deployment/distillation.py`：

- 从预定义 `CAPABILITY_SPECS`/task-family universe 选择能力；
- keyword projection 是默认路径；
- semantic projection 仍在预定义 capability universe 内选择；
- 直接生成 package/Markdown，缺少 Knowledge IR、conflict-preserving synthesis、modality decision 和 Knowledge Projection；
- `project_case_capabilities` 可读取 case expected capabilities，不能进入正式 open-world Compiler evidence chain。

因此它应保留为：

```text
legacy_keyword_projection baseline
controlled runtime fixture builder
```

不得通过改名或增加一个 LLM call 宣称已实现本规格。

## 10. 最小验收

- 一份真实 Markdown 专家规范经过全部阶段，产出逐阶段 artifact。
- 每个 eligible KnowledgeNode 有可定位 EvidenceRef。
- 动态 OSV 事实不进入 Skill IR。
- 至少一个 unsupported/contradictory item 被 quarantine 并保留。
- Skill IR 与 Knowledge Projection 由同一 Knowledge IR 产生但 digest 独立。
- `direct_to_skill_ir` 使用相同目标 schema 和 evaluator。
- Compiler/基线均看不到 held-out gold。
- 自动 source-grounded evaluation 可检测 scope overreach、modality mismatch 和 missing evidence 扰动。
- 生成的 candidate Bundle 通过 walking skeleton build/dev gate，但不会自动 promotion。
