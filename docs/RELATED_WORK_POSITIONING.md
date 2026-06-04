# Related Work Positioning

日期：2026-06-04

## 1. 当前结论

当前项目不应 claim：

- 提出通用 skill lifecycle。
- 提出 skill 自演化框架。
- 提出 rollback / versioned skill package。
- 提出 execution feedback 修正 skill。
- 提出一般意义上的 cost-aware skill evaluation。

这些方向已经被近期 skill ecosystem 工作大量覆盖。当前更稳的定位是：

```text
我们实现一个 expert-material-first 的最小蒸馏闭环；
把 SPARK-compatible execution feedback 回写到 rule-level compact decision；
把成本约束放到 deployment skill generation，而不是只做事后统计。
```

## 2. Related Work 压力

| 类别 | 代表工作 | 已覆盖方向 | 对当前项目的影响 |
|---|---|---|---|
| Skill 生命周期 / 自演化 | MemSkill, AutoSkill, SkillRL, EvoSkill, Audited Skill-Graph | 从经验生成 skill、维护 skill、失败分析、验证后提升、skill bank 演化 | 不应把 lifecycle / self-evolution 当作核心新意 |
| Skill 标准 / 生态 | SoK: Agentic Skills, SkillNet | skill taxonomy、repository、evaluation、cost-awareness、maintainability | 不应把 manifest、schema、cost_summary 当作核心贡献 |
| Skill 评测 / 组合能力 | SkillCraft | skill abstraction、tool composition、reuse benchmark | 后续需要多 case 评估，当前 MVP 只做 vertical slice |
| Skill 检索 / 路由 | SkillRouter | large-scale skill selection、body-aware retrieval、rerank | 多 skill 阶段可借鉴，但不是当前主线 |

## 3. 稳健表述

推荐表述：

```text
当前系统是一个专家材料蒸馏到 compact deployment skill 的最小原型。
它用 rule-level ledger 作为内部决策骨架，把材料证据、执行反馈和成本约束统一到部署版本生成中。
```

不推荐表述：

```text
我们提出新的 skill lifecycle。
我们提出新的 skill self-evolution 方法。
我们提出新的 rollback / audit / cost-aware skill framework。
```

## 4. 当前差异点

当前 MVP 的差异点不是“大而全”，而是收缩在一个具体场景：

```text
expert materials
-> full skill
-> rule-level deployment decisions
-> compact skill
-> SPARK-compatible feedback
-> ledger patch
-> compact skill v2
```

也就是说，重点问题是：

```text
专家材料蒸馏后的 skill，如何在执行反馈和成本约束下生成部署版本？
```

## 5. 需要吸收的评估维度

当前 demo report 应保留以下维度：

- Completeness：checklist coverage / missed rules。
- Executability：pass / reward / verifier result。
- Maintainability：rule-level repair log / patched ledger。
- Cost-awareness：input tokens / compact ratio / patch token increase。
- Auditability：evidence_map / rule_ledger / source execution report。

这些维度借鉴 skill ecosystem 的成熟评估语言，但当前只用于 MVP 汇报，不 claim 已完成大规模评测。

## 6. Validation Gate 入口

Patch 不应无条件接受。当前先实现一个最小 gate：

```text
if affected rules exist
and compact_v2 contains affected rules
and token increase is below threshold
then accept patch
else reject / rollback to compact_v1
```

这个 gate 不是完整 EvoSkill / Audited Skill-Graph 式验证，只是 MVP 的 promotion check。

## 7. References To Track

- [MemSkill: Learning and Evolving Memory Skills for Self-Evolving Agents](https://arxiv.org/abs/2602.02474)
- [AutoSkill: Experience-Driven Lifelong Learning via Skill Self-Evolution](https://arxiv.org/abs/2603.01145)
- [SkillRL: Evolving Agents via Recursive Skill-Augmented Reinforcement Learning](https://arxiv.org/abs/2602.08234)
- [EvoSkill: Automated Skill Discovery for Multi-Agent Systems](https://arxiv.org/abs/2603.02766)
- [SoK: Agentic Skills -- Beyond Tool Use in LLM Agents](https://arxiv.org/abs/2602.20867)
- [SkillNet: Create, Evaluate, and Connect AI Skills](https://arxiv.org/abs/2603.04448)
- [SkillCraft: Can LLM Agents Learn to Use Tools Skillfully?](https://arxiv.org/abs/2603.00718)
- [SkillRouter: Retrieve-and-Rerank Skill Selection for LLM Agents at Scale](https://arxiv.org/abs/2603.22455)

以上条目用于 related work 定位。后续如果进入论文写作，需要逐篇细读原文，不应只依赖摘要。
