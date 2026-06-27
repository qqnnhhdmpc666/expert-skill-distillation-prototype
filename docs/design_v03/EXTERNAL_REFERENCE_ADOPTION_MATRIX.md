# External Reference Adoption Matrix

状态：`reviewed_for_v1`

核验日期：2026-06-21
性质：技术采用决策，不是相关工作性能复现报告。

## 1. 使用原则

本项目不靠重新实现 Agent、Skill 文件格式、容器评测框架或漏洞扫描器形成贡献。外部项目只在其成熟边界内复用；本项目的研究重点保留为：

```text
source-grounded expert knowledge compilation
+ Skill / retrievable knowledge joint projection
+ immutable ReleaseBundle
+ trajectory-grounded conservative evolution
+ marginal-utility and safety-gated promotion
```

表中论文结论是作者报告结果，尚未由本项目独立复现。`adopt_v1` 表示采用机制或接口，不表示复现论文全部系统或接受其全部性能主张。

状态枚举：

- `adopt_v1`：V1 直接采用其公开契约或经验证原则。
- `adapt_v1`：V1 借鉴机制，但按本项目对象边界改写。
- `qualify_before_freeze`：先做小型资格测试，再决定主实现。
- `cross_check_only`：只作外部对照，不是真值来源。
- `defer_v2`：研究价值明确，但不是 V1 walking skeleton 依赖。

## 2. 采用矩阵

| Concern | Reference | Status | Borrow | Adapt | Do not borrow | Acceptance test |
|---|---|---|---|---|---|---|
| Agent Skill 兼容格式 | Agent Skills specification | `adopt_v1` | `SKILL.md` 最小元数据、资源目录、progressive disclosure | `SKILL.md` 由 Skill IR 编译，是兼容视图而非真相源 | 不把任意 Markdown 当成已验证 Skill；不把宿主发现机制写入核心语义 | 同一 Skill IR 编译出的结构化 artifact 与 `SKILL.md` 在 scope、约束、例外和资源引用上等价 |
| 外部材料到程序性知识 | Anything2Skill | `adapt_v1` | evidence windows、结构化 skill contract、原知识与 Skill 双路访问、生命周期意识 | 使用 EvidenceUnit/Knowledge IR 作为可追溯中间层；SkillBank 被 ReleaseBundle + registry 取代 | 不直接复制 taxonomy；不以作者在 qsv/GitHub-CLI 的结果推断跨域有效 | `direct_to_skill_ir` 与 Compiler 在同一输入、Skill IR schema、资源包络和 held-out evaluator 下比较 |
| 环境后验轨迹 | SPARK/PDI | `adapt_v1` | 保存环境验证轨迹；把 posterior evidence 用作诊断和候选依据 | PDI 只作为研究参考；V1 使用 typed trace、external attestation 和 task outcome | 不声明复现 PDI；不把 plan 或自评当环境 reward | 至少一条正式任务的命令、stdout/stderr、verifier artifact 和 outcome 可关联到同一 session/bundle digest |
| 可安装、可纠正 Skill 包 | COLLEAGUE.SKILL | `adapt_v1` | 可检查 package、版本、纠正历史、安装与回滚 | 发布单位升级为 Skill + Knowledge Projection + bindings 的 ReleaseBundle | 不把 person-grounded behavior track 作为通用核心；不以 star 数证明方法有效 | 安装、纠正、候选验证、晋升和完整 bundle rollback 均有 DeploymentEvent |
| 多轨迹归纳 | Trace2Skill | `defer_v2` | 轨迹池并行分析、成功/失败差异化诊断、冲突合并，避免逐 badcase patch | V1 先冻结 `TrajectoryBatchInduction` 输入输出，演化仅用显式依赖和保守重建 | 不在 V1 复制重型多 analyst pipeline；不允许单轨迹直接改 active Skill | 同一候选 lesson 至少由多条独立轨迹支持；冲突/低频 lesson 被保留为诊断而非 hard rule |
| 无隐藏 gold 的更新审计 | SkillAudit | `adapt_v1` | 同任务 with/without-skill paired trajectories、固定 structural verifier、harmful rollback | 只用于无确定性 gold 的辅助 lane；V1 OSV 任务仍以冻结公开数据和确定性 evaluator 为主 | 不用 LLM evaluator 取代可用的确定性任务结果；不把 paired divergence 本身当提升 | 相同 task/budget/environment 的 paired run 可复现，candidate 失败时 active binding 不变 |
| 持久决策历史 | SkillHone | `adapt_v1` | 保留 diagnosis、proposal、evidence、rejection 和 outcome，而非只保留最终 Skill | 用 DecisionRecord、BuildAttestation、EvaluationAttestation、DeploymentEvent 表达 | 不在 V1 引入多角色 subagent orchestration | 后续构建可查询某类已拒绝方案及原因；历史不参与 active selection，除非显式读取 |
| 通用 Skill 边际效用 | SkillsBench | `qualify_before_freeze` | paired no-skill/skill、确定性 verifier、跨 model-harness 报告、focused skill 设计 | 作为公开兼容性 track；V1 主任务仍是 dependency-advisory pair | 不把其平均增益当本系统增益；不为接 benchmark 改写核心 domain contract | 先选 3-5 个许可证和环境可复现任务，验证原始结果与 adapter 结果一致 |
| 软件工程 Skill 效用 | SWE-Skills-Bench | `defer_v2` | 固定 commit、明确 acceptance criteria、同时报告 helpful/neutral/harmful Skill | 用于 V2 软件工程迁移和 Skill compatibility stress | 不把 SWE 结果当安全公告主证据；不在 V1 重开 SWE-bench 基础设施主线 | paired run 保持 commit、agent、model、budget、tests 一致，并报告零收益和负收益 |
| 容器化正式评测 | Harbor | `qualify_before_freeze` | task/environment/agent/verifier packaging、Docker 执行、公开 dataset、trajectory artifacts | 作为 `HarborEvaluationBackend`；本地构建与产品运行不强依赖 Harbor | 不把 Harbor 当 registry、Knowledge Service 或唯一 runtime；不把 adapter 完成当 benchmark 通过 | 3-5 个相同任务在原 harness 与 Harbor adapter 上结果一致，差异有逐项解释 |
| 主 Agent host 候选 | Codex CLI | `qualify_before_freeze` | 成熟本地 coding agent、脚本化调用和公开源码 | 通过 `AgentHostAdapter` 接入；模型、版本、权限和 sandbox 由 AgentProfile 固定 | 不把 Codex 内部会话格式写入核心 schema；不预先指定未经资格测试的模型 | 在相同 3-5 个任务上完成工具调用、artifact capture、超时和失败恢复测试 |
| 次 Agent host 候选 | OpenHands | `qualify_before_freeze` | 可自托管、多 backend/模型和 sandbox 能力 | 仅作为第二宿主兼容性 smoke，不成为 V1 walking skeleton 硬依赖 | 不复制其应用/UI/自动化平台；不把当前快速变化的内部目录作为稳定 API | 同一 AgentHost contract 下能运行至少一个相同任务，输出统一 ExecutionTrace |
| OSV 依赖事实 | OSV schema/data + OSV-Scanner | `adopt_v1` / `cross_check_only` | 冻结 OSV snapshot、机器可读 affected ranges；OSV-Scanner 作外部实现对照 | 本系统使用 snapshot-owned typed query 和 pair-level applicability semantics | 不把扫描器输出当唯一 gold；不把 applicability 声称为 reachability/exploitability | snapshot digest 固定；本系统与 OSV-Scanner disagreement 被分类为 parser/policy/data/version 差异 |
| 第二扫描器对照 | Trivy | `cross_check_only` | filesystem/repository/dependency vulnerability scan 结果作 disagreement check | 仅在共同支持的 pinned dependency slice 比较 | 不让 Trivy 决定 Knowledge IR 或 promotion；不把一致性当正确性证明 | 保存版本、DB digest/更新时间、命令和原始输出；差异不静默抹平 |

## 3. 对外部反馈的校正

### 3.1 不冻结具体 Agent 或模型名称

“Codex + 某旗舰模型”目前只能是资格测试候选，不能由二手评价直接成为 V1 唯一实现。Agent host、模型和执行环境是三个独立变量。正式冻结必须来自预注册的小型矩阵，而不是模型新旧印象。

V1 先冻结角色：

```text
CompilerModelProfile
RuntimeAgentProfile
JudgeModelProfile
AgentHostProfile
ExecutionEnvironmentProfile
```

具体 provider/model/version 在 held-out 前通过 qualification 固定。当前 DeepSeek 接口可以进入候选矩阵，但不能因已经可用就自动成为论文中的唯一模型。

### 3.2 Harbor 是正式评测后端候选，不是产品主循环

Harbor 官方说明支持 Codex CLI、OpenHands 等 Agent，并且是 Terminal-Bench 2.0 的 official harness。这支持将其用于正式容器评测。它不支持以下推论：

- 每次本地 build 都必须启动 Harbor；
- Harbor 应拥有 ActiveBinding 或 ReleaseBundle；
- 迁移一个 task pack 就等于保持原 benchmark 语义。

因此必须先做 adapter parity test，再将 Harbor 标为正式 backend。

### 3.3 V1 不应实现通用 repo knowledge layer

V1 纵向任务是 Python dependency-advisory pair，不需要 AST、symbol graph 或通用 repository index。V1 只实现：

```text
ExpertDocumentAdapter
RequirementsAdapter
OSVSnapshotAdapter
```

Repository adapter 只冻结接口；`rg`、AST、调用图和 GraphRAG 均不进入 walking skeleton。

### 3.4 外部 scanner 是交叉检查，不是独立 evaluator gold

OSV-Scanner 和 Trivy 包含各自的依赖发现、归一化和策略。它们与本系统一致只能增加可信度，不一致也不能自动判定任何一方错误。V1 的主 evaluator 来自冻结公开 OSV 数据、公开 schema、预注册 pair cases 和确定性版本/marker 语义。

## 4. 一手来源

- [Agent Skills specification repository](https://github.com/agentskills/agentskills)
- [Anything2Skill](https://arxiv.org/abs/2606.09316)
- [SPARK / Evidence Over Plans](https://arxiv.org/abs/2605.09192) and [official code](https://github.com/EtaYang10th/spark-skills)
- [COLLEAGUE.SKILL](https://arxiv.org/abs/2605.31264) and [official repository](https://github.com/titanwings/colleague-skill)
- [Trace2Skill](https://arxiv.org/abs/2603.25158) and [official code](https://github.com/Qwen-Applications/Trace2Skill)
- [SkillAudit](https://arxiv.org/abs/2606.14239)
- [SkillHone](https://arxiv.org/abs/2606.08671)
- [SkillsBench](https://arxiv.org/abs/2602.12670) and [official repository](https://github.com/benchflow-ai/skillsbench)
- [SWE-Skills-Bench](https://arxiv.org/abs/2603.15401) and [official repository](https://github.com/GeniusHTX/SWE-Skills-Bench)
- [Harbor](https://github.com/harbor-framework/harbor)
- [Codex CLI](https://github.com/openai/codex)
- [OpenHands](https://github.com/All-Hands-AI/OpenHands)
- [OSV-Scanner](https://github.com/google/osv-scanner)
- [Trivy](https://github.com/aquasecurity/trivy)
