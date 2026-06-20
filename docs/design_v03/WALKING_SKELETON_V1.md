# Walking Skeleton V1

状态：`acceptance_spec_not_yet_implemented`

目标：用最短真实链路证明 Knowledge Compiler、Knowledge Provider、Skill Runtime、ReleaseBundle 和 rollback 可以协同运行。

## 1. 唯一纵向任务

```text
Python dependency-advisory pair applicability
```

输入：

- 一份 Markdown 专家审查规范；
- 一份 frozen OSV snapshot；
- 一份 pinned `requirements.txt`；
- 一个 environment profile；
- 一个 advisory id。

输出：一个 pair-level `advisory_applicable | advisory_not_applicable | unresolved` decision，或独立的 parse/runtime failure。该结果不表示调用路径可达、漏洞可利用或项目真实存在安全风险。

## 2. Fixture 布局

```text
data/v1_walking_skeleton/
  expert_spec/
    python_advisory_review.md
  osv/
    snapshot.json
    snapshot_manifest.json
  build_examples/
    examples.jsonl
  dev_cases/
    cases.jsonl
  heldout_cases/
    cases.jsonl
  runtime_inputs/
    requirements.txt
    environment.json
```

`heldout_cases` 不进入 build closure。所有数据记录公开来源 URL、capture timestamp、license、digest 和 split manifest。

## 3. 用户命令

### 3.1 初始化与来源注册

```powershell
eskill init --state-dir .eskill
eskill source add data/v1_walking_skeleton/expert_spec/python_advisory_review.md --adapter expert-document
eskill source add data/v1_walking_skeleton/osv/snapshot.json --adapter osv-snapshot
```

验收：

- source snapshot 和 EvidenceUnit 进入 content-addressed store；
- SQLite 有 source/evidence 索引；
- 重复 add 同内容不产生新 digest；
- source visibility manifest 不包含 held-out。

### 3.2 构建 candidate Bundle

```powershell
eskill build python-advisory --profile compiler-v1 --examples data/v1_walking_skeleton/build_examples/examples.jsonl
```

验收：

- 生成 Stage 0-9 结果；
- 生成 Knowledge IR、Skill IR、Knowledge Projection、Agent artifact 和 ReleaseBundleManifest；
- 至少一条动态 OSV record 仅存在于 projection，不存在于 Skill IR；
- 至少一个无证据/冲突测试项被 quarantine；
- Bundle closure 的所有 hard dependency digest 可解析；
- 命令只返回 candidate digest，不修改 ActiveBinding。

### 3.3 验证与晋升

```powershell
eskill validate bundle <candidate-A-digest> --suite v1-build
eskill promote python-advisory <candidate-A-digest> --expected-generation 0
```

验收：

- deterministic、Judge、perturbation 和 dev task attestation 分离；
- validation failure 不会写 active binding；
- promotion 使用 compare-and-swap；
- ActiveBinding generation 从 0 到 1；
- DeploymentEvent 指向原始 candidate digest，而不是复制内容。

### 3.4 运行与解释

```powershell
eskill run python-advisory --requirements data/v1_walking_skeleton/runtime_inputs/requirements.txt --environment data/v1_walking_skeleton/runtime_inputs/environment.json --advisory <OSV-ID>
eskill inspect session <session-id>
```

验收：

- session 开始时 pin candidate A digest；
- Skill 声明 advisory evidence requirement；
- KnowledgeAccessBinding 解析到 frozen OSV provider；
- typed query 返回有 provenance 的 EvidenceEnvelope；
- outcome 恰好包含一个 pair decision；
- inspect 展示 Skill/Bundle/projection/provider digest、规则 refs、query、evidence、verdict reason 和 verifier result；
- hard evidence 不可用时 abstain/block，不从模型记忆补全。

## 4. 五条件诊断

在相同 Agent/runtime、domain primitives、snapshot、权限、case 和任务预算下运行：

```text
no_skill
full_material
direct_to_skill_ir
compiler_distilled_skill
human_authored_reference_skill
```

`human_authored_reference_skill` 是人工策划参考基线，不是 gold 或理论上界。没有可用人工版本时允许标为 `not_available`，不能临时让开发者根据 held-out 写一个。

另做机制对照：

```text
knowledge_only
skill_only_with_required_knowledge_unavailable
skill_plus_knowledge
```

`skill_only_with_required_knowledge_unavailable` 只验证 abstention/false-safe，不参与效果排名。

## 5. A/B Knowledge Snapshot

### Snapshot A

```powershell
eskill build python-advisory --profile compiler-v1 --knowledge-snapshot <snapshot-A-digest>
```

### Snapshot B

只更换冻结 OSV data，不修改 expert specification：

```powershell
eskill build python-advisory --profile compiler-v1 --knowledge-snapshot <snapshot-B-digest>
```

必须满足：

```text
Skill IR digest A == Skill IR digest B
Knowledge Projection digest A != Knowledge Projection digest B
KnowledgeAccessBinding digest A != KnowledgeAccessBinding digest B
ReleaseBundle digest A != ReleaseBundle digest B
```

这证明 Skill 与知识库在身份和更新生命周期上分离，而不是把 OSV 事实固化进 Skill。

## 6. Evolution 三动作

### A. Accepted update

向专家规范新增一条有证据的稳定规则，例如 environment marker 不可判定时必须 `unresolved`：

```text
source snapshot changes
-> explicit dependency impact set
-> conservative rebuild candidate B
-> old regression + new dev case + unrelated negative pass
-> promote B
-> ActiveBinding A -> B
```

### B. Rejected unsafe update

注入过宽规则，明确标为 `unsafe-update fault injection`：

```text
build candidate C
-> negative/false-safe control regresses
-> promotion(C) = rejected
-> ActiveBinding remains B
```

C 不得进入任何 active binding；rejection 和原因进入 decision history。

### C. Explicit rollback

```powershell
eskill rollback python-advisory <candidate-A-digest> --expected-generation <current-generation>
```

必须验证：

- ActiveBinding 从 B 重新绑定原始 A digest；
- Knowledge IR、Skill IR、Agent artifact、projection、bindings、verifier 和 permission closure 全部恢复 A；
- 新 session 使用 A；
- rollback 前已启动 session 继续固定 B；
- rollback 不是重新编译 A；
- promotion、rejection、rollback 各有 DeploymentEvent。

## 7. 失败注入

| Fault | Expected status | Forbidden behavior |
|---|---|---|
| unsupported requirements syntax | `completed + parse_error` | 伪装为 dependency absent |
| advisory missing in snapshot | `completed + unresolved` | 输出 not applicable |
| version unknown | `completed + unresolved` | 猜测版本 |
| OSV projection missing/expired | `blocked` or policy abstain | 使用模型记忆 |
| corrupt bundle closure | `runtime_failure` | 部分加载继续执行 |
| provider process failure | `runtime_failure` | 计入 unresolved accuracy |
| candidate scope overreach | validation rejected | 自动修宽 verifier |
| stale CAS generation | promotion conflict | 覆盖较新 active binding |

## 8. 外部与 Agent qualification

Walking skeleton 的 core DoD 不依赖 Harbor 网络或某个商业模型持续可用。正式研究证据另加两道门：

1. 至少一个 `AgentHostBackend` 通过预注册 smoke qualification。
2. 至少一个公开 task adapter 通过原 harness 与 Harbor parity test。

如果这两项未完成，状态只能是：

```text
core_walking_skeleton=pass
agent_host_qualification=blocked|partial
external_evaluation_backend=blocked|partial
```

不得把 core deterministic pass 写成外部 Agent 有效。

## 9. 实施切片

### WS-0: Schemas and state

- versioned models and JSON Schemas；
- canonical hash；
- ArtifactStore；
- SQLite migrations；
- runtime envelope tests。

### WS-1: Sources and projection

- ExpertDocumentAdapter；
- RequirementsAdapter；
- OSVSnapshotAdapter/Provider；
- source/evidence provenance tests。

### WS-2: Compiler

- Stage 0-9 orchestrator；
- direct_to_skill_ir baseline；
- quarantine；
- source-grounded evaluator。

### WS-3: Bundle and runtime

- Skill compiler；
- KnowledgeAccessBinding；
- ReleaseBundle closure；
- ReferenceDecisionBackend；
- session inspect。

### WS-4: Deployment transactions

- candidate validation；
- CAS promotion；
- unsafe rejection；
- full-bundle rollback；
- pinned running session test。

### WS-5: Agent and external qualification

- AgentHost qualification matrix；
- Harbor adapter parity；
- public paired skill/no-skill smoke。

任何 slice 都不能用只生成 JSON/报告代替真实状态驱动和运行行为。

## 10. Definition of Done

只有以下全部成立，V1 walking skeleton 才是 `pass`：

- clean environment 一条文档化流程可安装；
- CLI 主链不依赖开发者理解内部脚本；
- 真实专家材料生成可审计 Knowledge IR 和 Skill IR；
- Skill + frozen knowledge 完成一个真实 pair decision；
- verdict 可追溯到 exact Bundle、Skill、projection、query 和 evidence；
- A/B snapshot 保持 Skill digest 不变；
- unresolved、parse error、blocked、runtime failure 可区分；
- accepted update、rejected unsafe candidate、explicit rollback 都真实改变或保持 ActiveBinding；
- failed/rejected/blocked artifacts 被保留；
- direct baseline 和 Compiler 的数据可见范围、资源包络与 evaluator 公平；
- 当前原型回归测试保持通过。
