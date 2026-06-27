# 给老师的阶段进展说明（2026-06-16）

## 一句话概括

项目方向从“材料蒸馏为 Skill，再做 evidence-driven evolution”进一步明确为：

> Knowledge Base / RAG + Skill + Trajectory 的混合型 Agent 知识系统。

这个更新不是推翻前面的 Skill Evolution Runtime，而是给它补上更真实的知识管理边界：稳定流程固化为 Skill，动态知识和案例保留在 RAG / 知识库，执行轨迹同时反哺两者。

## 为什么不能只做 Skill

讨论中形成的关键判断是：把知识固化为 Skill 后，在稳定流程类任务上可能显著优于传统 RAG 或多轮检索，因为 Skill 能固定操作步骤、输出契约、边界条件和失败恢复方式。

但单纯 Skill 也有明显局限：

- 版本、依赖、漏洞公告等事实会变化；
- 长尾异常和真实案例数量太大，不适合全部写进 Skill；
- 过多案例会让 Skill 膨胀成难维护的 prompt 仓库；
- 执行时仍需要检索具体上下文。

因此更合理的结构是 Skill 与 RAG 融合，而不是互相替代。

## 三层关系

### 1. Knowledge Base / RAG

保存动态事实、背景材料、历史案例、异常处理记录和方法论材料。

### 2. Skill

保存稳定、可迁移、可复用的 how-to 指南，例如审计流程、工具顺序、输出格式、边界条件和失败恢复。

### 3. Trajectory

保存 Agent 在真实任务中的执行记录，包括工具调用、读写文件、命令结果、失败原因和最终 verifier 反馈。

轨迹有双向作用：

- 对 Skill：验证是否有效，并生成候选更新；
- 对 RAG：补充真实案例和失败经验。

## 对当前实验的影响

当前 v0.2 teaching-utility pilot 已经开始回答一个核心问题：

> 高 task utility 的轨迹，是否真的等于高 teaching utility 的轨迹？

最新更严格版本已经把 sealed hidden test 从主 pilot 中拆出，由独立脚本在方法和 Skill hash 冻结后首次访问。当前结果是：

- active discriminative selection 尚未证明优于 contrast / diversity；
- sealed hidden utility 暂时是 flat signal；
- 因此不应围绕 active selection 继续扩建工程，除非后续设计能拿到更强证据。

这是一条有价值的负/不确定结果，因为它防止我们把“看起来聪明的轨迹选择”包装成算法成功。

## 对 benchmark 的影响

下一步 benchmark 不应只问“Skill 是否有用”，而应分解比较：

1. RAG-only：只检索知识库；
2. Skill-only：只使用固化 Skill；
3. Skill + RAG：Skill 给流程，RAG 补具体上下文；
4. Skill + RAG + Trajectory feedback：轨迹继续更新 Skill 和知识库。

指标必须来自官方 evaluator、真实环境结果或可审计 verifier。内部 verifier 可以辅助诊断，但不能直接包装成外部有效性。

## 与 SFT / RL 讨论的联系

讨论中关于 SFT 和 RL 的启发可以迁移到 Skill evolution：

- 单个高奖励轨迹不等于可迁移 Skill；
- Skill 更新更像分布控制，而不只是奖励最大化；
- 必须固定任务分布、预算、token、工具调用、hidden test；
- 被拒绝的 candidate 是重要证据，不是失败包装。

因此，当前路线应避免“从最优轨迹直接总结 Skill”的简单方案，继续坚持多轨迹、验证集、门控和 hidden test。

## 场景选择

漏洞挖掘 / 安全审计比普通问答更适合当前阶段，因为它有更清楚的工具调用、文件读写、命令结果和环境反馈。

多智能体轨迹编排是有潜力的后续方向，但当前优先级仍是：

1. 先在垂直场景里建立可靠的单/少量 Agent 轨迹证据；
2. 证明哪些轨迹能教出可迁移 Skill；
3. 再扩展到多智能体非线性轨迹编排。

## 当前可安全汇报的状态

可以说：

- 项目已形成 Skill install / execute / evidence / candidate / gate / rollback 的研究级 runtime；
- bounded open-world distillation 和 bounded evolution improvement 有支持性证据；
- v0.2 teaching-utility pilot 保留了 active selection 未证明优势的真实结果；
- 新方向明确为 Knowledge Base + Skill + Trajectory 混合系统。

不能说：

- 已经证明 Skill+RAG 混合系统优于 RAG-only；
- 已经完成官方 benchmark；
- 已经证明 active trajectory selection 有稳定优势；
- 已经证明 broad stable autonomous Skill evolution；
- 系统已是生产级漏洞挖掘工具。

## 下一步建议

优先推进一个小型但真实的混合 benchmark：

```text
RAG-only
Skill-only
Skill + RAG
Skill + RAG + trajectory feedback
```

先选安全审计 / 漏洞挖掘相关的可执行小样本，验证器成熟前不急着扩大规模。目标不是快速把结论写满，而是证明哪一层在什么任务中真正贡献收益。

