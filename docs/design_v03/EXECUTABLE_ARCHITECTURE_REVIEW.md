# Executable Architecture Review

状态：`accepted_with_corrections`

本文件审查“本地优先模块化单体、成熟 Agent、Harbor、公开 benchmark 与外部 verifier”建议。结论不是照搬外部方案，而是把架构冻结进一步压到可运行边界。

## 1. 总体裁决

接受以下主干：

- V1 使用本地优先模块化单体，而不是微服务平台；
- 不可变大对象进入内容寻址 Artifact Store，可变索引与绑定进入 SQLite；
- Skill 与 Knowledge Projection 独立版本化，通过 ReleaseBundle 共同发布；
- 不自造通用 coding agent，以 AgentHost adapter 接成熟宿主；
- 正式 Agent 结论优先来自公开任务的原生 harness，或通过 parity 的 Harbor adapter；
- verifier 分成确定性契约检查、独立 LLM Judge、外部任务 evaluator，三者不能相互冒充；
- 模型、prompt、预算和 fallback 在 held-out 前冻结。

但修正四个过度判断：

1. **Harbor 不是产品 Runtime 的默认依赖。** 它是首选外部评测后端候选，只有通过原 harness parity 才取得正式证据资格。
2. **Codex/OpenHands 不是凭声誉直接冻结。** 先用 build/dev smoke 资格测试，再冻结主宿主与兼容宿主。宿主、模型和沙箱是三个独立变量。
3. **不是每个模块都需要神经网络。** Parser、hash、registry、typed query、版本判断、transaction 和 deterministic verifier 必须保持确定性。模型只进入无法由可靠规则完成的语义阶段。
4. **技术冻结不是永久锁死实现。** 冻结的是角色、输入输出、预算、失败语义和版本；具体实现只能通过 ADR 和重新资格测试替换。

## 2. V1 运行拓扑

```text
eskill CLI
  -> application services
     -> compiler / runtime / deployment / evaluation
     -> filesystem CAS + SQLite metadata
     -> local knowledge providers
     -> optional process adapters
        -> compiler model
        -> AgentHost
        -> independent Judge
        -> Harbor/native benchmark harness
```

核心进程不得通过仓库内脚本拼接业务主链。外部进程失败必须返回 `blocked` 或 `runtime_failure`，不能变成领域 `unresolved`。

## 3. 模块是否使用模型

| 模块 | V1 默认 | 模型职责 | 不允许 |
|---|---|---|---|
| source capture/segment | deterministic | 无 | 用 LLM 猜文件边界或 provenance |
| explicit extraction | model-assisted | 从可见 evidence span 提结构化候选 | 补充无来源常识 |
| evidence binding | deterministic-first | 可提出绑定建议 | 决定 digest/span 是否有效 |
| synthesis/conflict | hybrid | 语义等价与冲突候选 | 抹平冲突、扩大 scope |
| modality projection | rules + model suggestion | 对 Skill/Knowledge/Both/None 提议 | 绕过 eligibility gate |
| Skill IR rendering | deterministic-first | 仅可做受约束表达压缩 | 新增 hard rule |
| knowledge query | deterministic provider | 无 | 用模型记忆代替冻结事实 |
| runtime task execution | qualified AgentHost | 工具规划与执行 | 越过 Bundle/permission |
| source-grounded review | independent Judge | 语义盲评 | 称作人工专家 gold |
| promotion/rollback | deterministic transaction | 无 | 让模型直接改 ActiveBinding |

## 4. Agent 与执行后端

AgentHost 资格测试固定检查：无人值守调用、Skill 注入、结构化输出、轨迹完整性、权限、超时、版本可复现和 provider 可替换性。通过前只能写 `candidate` 或 `blocked`。

后端分工：

- `ReferenceDecisionBackend`：验证 domain contract、知识查询和 evaluator plumbing，不证明 Agent 效果；
- `AgentHostBackend`：验证成熟 Agent 是否真正利用 Skill/Knowledge；
- benchmark-native harness：保持公开任务语义的首选证据；
- `HarborEvaluationBackend`：通过 parity 后用于统一容器、轨迹与结果包装；
- local deterministic runner：开发和回归路径，不冒充外部有效性。

## 5. 数据与 evaluator

V1 正式领域轨使用公开 OSV 来源确定性生成 dependency-advisory pair：冻结 source records、schema、generator、split manifest 和 evaluator。OSV-Scanner/Trivy 仅做 disagreement cross-check，不是 gold。

通用 Skill 轨只在许可证、环境和原 verifier 可复现后选择公开子集。适配到 Harbor 时必须同时保留原 harness 结果，验证：

```text
original task + original verifier
~= same task through Harbor adapter + original verifier semantics
```

不允许用项目自制 verifier 替换公开 benchmark 的原生 evaluator 后仍声称是该 benchmark 结果。

## 6. 研究机制与工程边界

工程贡献是：CAS、SQLite、schema、provider、CLI、adapter、transaction 和 provenance。

候选研究机制是：

- source-grounded Knowledge Compiler 相对 `direct_to_skill_ir` 的增量价值；
- Skill/Knowledge/Both/None 的受约束形态决策；
- paired no-skill/skill trajectory 对边际行为的归因；
- 多轨迹 evidence 到 candidate knowledge 的保守归纳；
- 整 Bundle 的验证、晋升、拒绝和回滚。

V1 不主张 RL、自主语义影响分析或稳定自动改进。危险候选被拒只证明 safety gate，不证明 improvement。

## 7. 执行顺序

```text
1. 冻结 benchmark/verifier 协议
2. 用 build/dev 资格测试冻结模型与 AgentHost profile
3. 完成公开发布规格与 clean-install contract
4. 运行 walking skeleton
5. 运行公开 OSV pilot
6. 通过 parity 后启用 Harbor 外部评测
7. 才进入正式 held-out 比较
```

该顺序不是继续概念扩张，而是避免实现时临时换 Agent、模型、数据或 evaluator。

