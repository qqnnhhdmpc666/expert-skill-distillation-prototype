# Expert Skill Distillation System

这是一个面向 Agent 的专家知识蒸馏与 Skill 生命周期研究原型。系统目标不是把专家文档简单塞进提示词，而是把专家材料、动态知识和执行证据编译成可验证、可发布、可回滚的运行时工件。

当前 V1 主线可以概括为：

```text
Expert Skill Distillation System
= Knowledge Compiler
+ Skill Runtime
+ Pluggable Knowledge Provider
+ External Verification
+ Safe Evolution
```

## 系统能做什么

V1 已实现一个公开可复现的 Python 依赖安全公告适用性切片。给定专家规范、冻结 OSV 公告和 pinned requirements，系统可以构建 `Knowledge IR`、`Skill IR`、`Knowledge Projection` 和不可变 `ReleaseBundle`，再通过运行时判断某条公告是否适用于当前依赖版本，并输出 verdict、reason code、证据摘要和 artifact digest。

这条切片用于验证一种更通用的机制：稳定的 how-to 流程进入 Skill，动态事实和证据进入 Knowledge Projection，真实运行结果进入 Evidence，再由 promotion/rejection/rollback 保护 active Bundle。

## 当前真实状态

- Core local implementation: `pass`
- Skill 与 Knowledge Projection 分离: `pass_local`
- Independent DeepSeek Judge: `pass`
- Public OSV pilot v2 reference runtime: `33/33`, false-safe `0`
- Harbor public OSV parity: `public_task_parity_subset_pass`, 当前 6 个 subset case 通过
- `direct_to_skill_ir`: 真实一阶段 DeepSeek 生成，已与 compiler-distilled artifacts 区分
- Compiler-vs-Direct: `prepared_condition_sensitive_eval_no_agenthost`
- AgentHost: `hard_blocked_no_compatible_mature_host`
- Safe evolution: promotion/rejection/full-bundle rollback 已通过本地门控

关键边界：当前还不能声明成熟 Agent 已稳定消费 Bundle，也不能声明 Compiler 优于 Direct baseline。

## 快速开始

需要 Python 3.11+。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .[dev]

eskill --state-dir .eskill demo --data-dir data/v1_walking_skeleton
```

成功后会得到真实的 `bundle_digest`、`session_id`、verdict、reason code，以及 OSV snapshot/query/result digest。

更多命令见 [docs/QUICKSTART.md](docs/QUICKSTART.md)。

## 推荐阅读路径

外部 reviewer 或老师可以按这个顺序阅读：

1. [reports/PUBLIC_VALIDATION_AND_AGENT_USABILITY_STATUS.md](reports/PUBLIC_VALIDATION_AND_AGENT_USABILITY_STATUS.md)
2. [docs/design_v03/SYSTEM_ARCHITECTURE_FREEZE_V1.md](docs/design_v03/SYSTEM_ARCHITECTURE_FREEZE_V1.md)
3. [docs/design_v03/EXECUTABLE_ARCHITECTURE_REVIEW.md](docs/design_v03/EXECUTABLE_ARCHITECTURE_REVIEW.md)
4. [reports/COMPILER_VS_DIRECT_EVALUATION.md](reports/COMPILER_VS_DIRECT_EVALUATION.md)
5. [reports/AGENT_HOST_ROUTE_DECISION.md](reports/AGENT_HOST_ROUTE_DECISION.md)
6. [reports/HARBOR_EXTERNAL_EVAL_STATUS.md](reports/HARBOR_EXTERNAL_EVAL_STATUS.md)
7. [docs/CLAIM_BOUNDARY.md](docs/CLAIM_BOUNDARY.md)

## 为什么 Skill 和 Knowledge 分开

Skill 保存稳定流程、约束、异常处理和工具使用方法。Knowledge Projection 保存会变化的公告、版本范围、环境事实和证据。这样同一套 how-to 可以在不同知识快照下重新发布，来源变化也可以通过显式 provenance 触发保守重建，而不是把所有事实固化进 Skill。

## 仓库结构

```text
src/expert_skill_system/   V1 compiler, registry, runtime, deployment, evaluation
data/v1_walking_skeleton/  V1 expert spec, OSV snapshot, dev/runtime cases
data/public_osv_pilot/     public OSV pilot v2 inputs, gold and snapshots
data/harbor_tasks/         Harbor oracle/verifier parity tasks
tests/v1/                  V1 contract, integration and transaction tests
docs/design_v03/           Architecture Freeze v1 docs
reports/                  Evidence reports and claim boundary status
src/skill_deployment/      legacy controlled Skill deployment prototype
```

## 不能据此声明什么

- 不能声明通用 open-world 自动蒸馏已经成立。
- 不能声明 Compiler 已经优于 direct baseline。
- 不能声明 evolution 会稳定自主产生更优 Skill。
- 不能声明成熟 AgentHost 已经通过。
- 不能把 OSV applicability 说成 exploitability、reachability 或真实项目已受影响。
- 不能把 Harbor oracle/verifier parity 说成非 oracle Agent usefulness。

项目采用 [MIT License](LICENSE)。本仓库只处理防御性分析和验证，不生成 exploit，不执行攻击链，不访问未授权目标。
