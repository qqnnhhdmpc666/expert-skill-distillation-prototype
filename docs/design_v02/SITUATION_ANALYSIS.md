# v0.2 Situation Analysis

更新日期：2026-06-19
审查范围：当前仓库的 Runtime、Agent、脚本、数据、产物、报告和 Harbor/Docker 相关实现。
本轮性质：只读审计与设计预研，不代表下述目标已经实现。

## 1. 总体判断

当前仓库已经不是单纯的 prompt demo。最值得保留的是一条可运行的 Skill 生命周期骨架：

```text
材料 -> Skill Package -> 安装/激活 -> Agent 执行 -> Evidence Bundle
-> Verifier -> Candidate -> Promote/Reject/Rollback
```

这条链在受控任务中有真实代码、状态文件和证据产物。但它仍是一个以固定 capability registry 和本地 verifier 为中心的研究原型，而不是开放知识系统。新的“Knowledge Base - Skill - Trajectory”方向尚停留在文档层：仓库中没有统一 Knowledge Store、Knowledge Atom、Retrieval Receipt、知识形态决策器或运行时检索接口。

最准确的成熟度判断是：

| 能力 | 当前状态 | 结论 |
|---|---|---|
| Skill 安装、版本、active pointer、回滚 | 已有真实路径 | 保留并收敛接口 |
| 受控执行与 Evidence Bundle | 已有共享骨架 | 保留，但区分真实轨迹与合成摘要 |
| task-conditioned capability activation | 已有本地证据 | 可作为通用路由机制的早期原型 |
| 开放材料蒸馏 | 有 bounded evidence | 仍被预定义 capability universe 限制 |
| Skill evolution gate | 能拒绝坏候选，也有一条有界提升线 | 不能宣称稳定自动改进 |
| Knowledge/RAG runtime | 基本不存在 | v0.2 最大结构性缺口 |
| 工具型 Agent 与真实沙箱 | 有窄切片、Harbor replay 和独立脚本 | 尚未成为统一主干 |
| 外部 benchmark | 多数 blocked/scaffold/local approximation | 不能作为外部有效性结论 |

## 2. 仓库规模与结构信号

审计时观察到：

- `src/skill_deployment/` 有 22 个 Python 模块；其中 `distillation.py` 约 956 行、`teaching_utility_v02.py` 约 808 行、`cli.py` 约 661 行。
- `scripts/` 有约 110 个 Python 脚本，共约 26,739 行。
- `outputs/` 下约有 17,878 个文件，其中 7,387 个已被 Git 跟踪。
- CLI 已包含大量实验命令，主要通过 `run_script(...)` 转发到独立脚本。
- 核心包、实验编排、报告生成和历史证据共同存在于一个仓库层级中。

这不是单纯的“文件多”，而是边界信号：实验代码正在承担产品 Runtime 的部分职责，生成产物也在参与测试和 replay。若直接加入 RAG，会进一步扩大职责混合。

## 3. 核心模块审计

### 3.1 `src/skill_deployment`

| 模块 | 当前价值 | 主要问题 | 建议 |
|---|---|---|---|
| `schemas.py` | 已统一 Skill、Execution、Verifier、Patch、Gate、Trace 的基本对象 | 对知识访问、检索、来源、权限和时间有效性没有建模；大量字段仍藏在 `metadata` | 保留概念，v0.2 增加独立契约，不继续向 `metadata` 塞结构化核心字段 |
| `install_state.py` | install/rollback/active pointer 真正驱动 runtime | 状态路径硬绑 `outputs/installed_skills`；缺并发、事务和环境隔离 | 作为 prototype adapter 保留；核心接口不得依赖具体文件布局 |
| `runner.py` | 有 `RunnerContext`、`BackendRunner` 和多个 backend | 安全能力、task activation、子进程 agent 和 Harbor replay 混在一处；`frozen` context 内部仍修改可变 `metadata` | 拆成通用 runner contract、router、backend adapter；security activation 移到领域 adapter |
| `distillation.py` | 有来源记录、能力投影、Skill 渲染和 provenance | 直接依赖 `CAPABILITY_SPECS` 与 task-family capability map；“open world”仍是闭集选择 | 保留来源与 provenance 逻辑；将能力发现、知识形态判断、Skill 编译分开 |
| `capability_registry.py` | 受控实验的稳定词汇表 | 检测词、evidence hint、fix hint 和领域能力绑死在核心包 | 迁移到 security adapter；核心只保留 capability schema |
| `evidence.py` | Evidence Bundle 纪律较强 | 其中 `trajectory.jsonl` 常由最终 findings 合成，不一定是真实工具轨迹 | 保留 bundle；增加 `trajectory_kind=observed/synthesized/replay` 和 retrieval receipt |
| `verifier.py` | 能检查 coverage、schema、evidence span、false positive | 依赖 expected capability oracle；适合作为内部诊断，不适合作为最终外部裁判 | 保留为 diagnostic checker；最终结果必须由环境测试或第三方 evaluator 提供 |
| `repair.py` / `gate.py` | typed operator 与 reject/rollback 思路清楚 | repair 仍能访问 expected capabilities；通用 gate 与领域 policy 未完全分离 | 保留 gate 框架；输入改为公开 feedback/evidence，不允许读取隐藏答案 |
| `teaching_utility_v02.py` | 已认真处理 matched budget 和 sealed hidden | 是研究实验实现，不应进入长期 Runtime 核心 | 移到 experiments 层，保留数据契约和结果 |
| `harbor_adapter.py` | 能把已有 Harbor 证据映射回共享报告 | 目前本质是 replay reader，不是通用 live sandbox backend | 保留为 adapter；不得把 replay 写成 live execution |

### 3.2 `agents/` 与 `backends/`

当前至少存在两套 backend 抽象：

- `src/skill_deployment/runner.py::BackendRunner`
- `backends/execution_backend.py::ExecutionBackend`

同时，多个 agent 重复实现 OpenAI-compatible HTTP 调用、JSON 提取、文件读取和输出归一化。`live_tool_case_agent.py` 已经有工具循环和轨迹记录，是更接近未来主干的原型；`llm_security_agent.py` 主要把整个目标文本塞入 prompt，工具能力较弱。

建议：

- 保留一个 `AgentBackend` 契约；
- 把模型调用、工具注册、沙箱、输出 contract 分开；
- Agent 只接收 task-visible 输入、Skill resolution 和 Knowledge Access API；
- security-specific prompt、capability 和工具放入 adapter；
- 不继续新增平行 agent 脚本。

### 3.3 `scripts/`

脚本层保存了大量有价值的实验历史，但目前承担四种不同职责：

1. Runtime 命令实现；
2. 一次性实验编排；
3. 报告生成；
4. artifact 迁移、审计和修复。

这导致新贡献者很难判断 canonical path。例如 open-world、live-contract、improvement、teaching-utility 和 Harbor 都有独立编排器。建议先做分类清单，不立即搬迁：

```text
scripts/runtime/       未来只保留 CLI 的窄适配器
experiments/           研究实验与 ablation
tools/                 artifact migration / audit / report build
legacy/                已被共享 Runtime 取代但仍需复现实验的脚本
```

在设计冻结前不应进行物理重排，以免破坏现有复现路径。

### 3.4 `data/`

优点：

- 受控 task case 已有 `case.yaml`、target、source materials、expected behavior、verifier contract 的分离；
- 部分 mini-suite 已注意 agent-visible 与 verifier-only 字段隔离；
- negative control 和 unsupported limitation 有明确位置。

问题：

- `expected_capabilities` 同时出现在多个文件；
- task schema、holdout schema、Harbor task schema 和 teaching-utility case schema 不统一；
- 没有 Source Record、Knowledge Atom、retrieval corpus 或 temporal validity；
- 领域标签与核心 capability id 耦合。

### 3.5 `outputs/` 与 `reports/`

`reports/` 的优势是 claim boundary、negative result 和 artifact type 意识较强。问题是报告数量巨大，部分报告由旧 artifact 派生，读者很难判断最新 canonical evidence。

`outputs/` 同时承担 runtime state、fresh run、replay source、测试 fixture 和对外证据。7,000 余个已跟踪文件会放大以下风险：

- 测试意外依赖历史产物；
- fresh run 与旧结果混淆；
- clean clone 成本上升；
- 真实 Runtime state 与 reviewer artifact 相互覆盖。

v0.2 应冻结 artifact taxonomy，至少分开：

```text
runtime_state/    可变安装状态，不作为实验真值
runs/             append-only fresh execution
fixtures/         小型、明确版本的测试输入
evidence/         经选择并哈希的可发布证据
reports/          只读派生结论
```

### 3.6 Harbor / Docker / SWE-bench

- 当前 Harbor 在核心包中主要是 replay adapter；live Docker/WSL 逻辑仍在独立脚本和 integration 目录。
- SWE-bench 官方 harness 线保持 `infra_blocked`，不能作为 framework effectiveness。
- benchmark-native sandbox 比自建统一 sandbox 更值得优先：外部 evaluator 的可信度高于自建 verifier。
- Harbor 适合作为一个 `SandboxBackend`，不应成为 Runtime 的领域中心。

## 4. 当前最重要的耦合

1. **知识发现与固定 registry 耦合**：材料只能被投影到已知 capability。
2. **task routing 与 security capability group 耦合**：当前 router 是安全任务标签匹配，不是通用知识形态决策。
3. **Agent 与输出 verifier contract 耦合**：prompt 直接暴露 capability id 和固定 schema，利于受控验证但限制开放发现。
4. **内部诊断与最终评价耦合**：expected capability verifier 被过度用作最终 reward。
5. **Runtime 与实验脚本耦合**：CLI 是大型脚本分发器，canonical path 不清晰。
6. **证据与历史 outputs 耦合**：replay、fresh run、runtime state 和 fixture 混在一起。

## 5. 应保留、扩展、重构、淘汰什么

### 保留

- Skill Package、版本、安装、active pointer、rollback 的可审计思想；
- Evidence Bundle、hash/provenance、negative result 保留；
- task-conditioned activation 与 out-of-scope guard；
- Candidate、rejected buffer、strict held-out gate；
- task-visible / verifier-only 隔离原则。

### 扩展

- `SkillPackage` 旁新增知识访问与轨迹契约；
- Agent backend 增加工具和知识访问能力；
- Evidence Bundle 增加 retrieval plan/receipt、source citation、knowledge snapshot；
- evaluator 分成内部诊断和外部结果。

### 重构

- 固定 capability registry 从核心移到 security adapter；
- 两套 backend protocol 合并；
- CLI 与 110 个脚本的职责分层；
- 轨迹区分 observed、synthesized、replay；
- Runtime state 与发布证据目录分离。

### 暂停或淘汰

- 新增与现有 agent 重复的单文件 Agent；
- 把 GraphRAG、向量数据库或多 Agent 当作默认架构；
- 用更多自建 expected-capability case 替代外部 evaluator；
- 把单次成功轨迹直接写入 Skill；
- 把所有知识都编译进 `SKILL.md`。

## 6. 审计结论

当前方案最值得保留的是“可审计 Skill 生命周期控制平面”。最大缺口不是缺一个 retriever，而是缺少统一的知识对象、知识形态决策和运行时知识访问契约。正式编码前必须先冻结这些契约，否则 RAG 会变成附加在现有 prompt 前的另一条实验脚本，而不是系统能力。
