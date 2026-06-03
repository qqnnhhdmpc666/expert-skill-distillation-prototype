# 导师要求与当前进度对齐

## 1. 导师原始要求摘要

导师希望我们在两周后完成一个项目演示原型，主题是“对专家知识进行蒸馏”，并重点参考两篇近期工作：

- **SPARK-PDI**：来自论文《Evidence Over Plans: Online Trajectory Verification for Skill Distillation》，arXiv:2605.09192，2026 年 5 月 9 日发布。
- **COLLEAGUE.SKILL**：arXiv:2605.31264，2026 年 5 月发布。

导师的核心意思是：

- 第二篇 `COLLEAGUE.SKILL` 有开源实现，可以优先阅读、审查和借鉴。
- 第一篇 `SPARK-PDI` 需要复现或至少做简化复现。
- 现有方向主要解决“正确性验证”，还没有充分考虑“效率”。
- 希望我们能在复现基础上增加效率考量，争取做出一个可开源的原型版本。

## 2. 当前已核验信息

- `SPARK-PDI` 的 arXiv 页面显示该工作提出了 PDI，用于验证蒸馏出的 skill 是否真正来源于环境验证过的执行轨迹，而不是只依赖先验计划。
- `SPARK-PDI` 公开页面关联了代码仓库：`https://github.com/EtaYang10th/spark-skills`。
- `COLLEAGUE.SKILL` 的核心目标是从专家、人物或角色相关材料中蒸馏出 agent skill，强调能力轨道和行为边界。
- 当前识别到的 `COLLEAGUE.SKILL` 代码仓库是：`https://github.com/titanwings/colleague-skill`。

这里有一个需要校正的点：导师原话中说“第一篇需要复现”，但目前看第一篇也有公开仓库。因此后续更稳妥的表述是：**第一篇需要审查仓库并尝试跑通；如果完整复现成本过高，则实现一个忠实于机制的简化复现。**

## 3. 我们当前的任务定位

我们不是只做论文综述，而是要做一个能演示的两周原型系统。

这个系统应尽量展示：

1. 输入专家材料或执行轨迹；
2. 生成可检查的 skill package；
3. 对 skill package 做正确性或证据覆盖验证；
4. 根据反馈进行修正，并产生新版本；
5. 在基础流程稳定后，把效率作为明确优化方向，加入轻量化调用版本和成本指标。

我的当前角色是技术推进者和原型执行者：

- 阅读并拆解两篇论文；
- 审查两个开源仓库；
- 判断哪些机制可以直接复现，哪些需要简化；
- 设计安全 demo 数据；
- 实现专家材料到 skill package 的基础管线；
- 实现验证、反馈修正和版本更新；
- 整理演示脚本、实验记录和最终报告。

## 4. 当前确定的原型主线

当前方案是做一个“基于证据与执行反馈的专家 Skill 蒸馏原型系统”。

英文表述：

```text
Evidence-grounded Expert Skill Distillation with Execution Feedback
```

它不是单纯复现某一篇论文，也不把“效率感知”作为唯一主线。真正主线是：

```text
专家材料
-> 初始 skill package
-> 材料证据验证
-> compact skill
-> 真实任务执行
-> trajectory / judge 反馈
-> skill patch
-> skill v2
-> 成本与效果对比
```

更完整的设计见：

- `D:\solution\docs\MVP_DESIGN.md`
- `D:\solution\docs\DEMO_DESIGN.md`

建议把原型设计成三层：

### 4.1 COLLEAGUE.SKILL 风格的蒸馏层

输入专家材料，例如公开指南、合成专家说明、论文评审规则或代码审查规则。

输出结构化 skill package，包括：

- capability track：这个 skill 能做什么；
- behavior track：它应该如何表现、有哪些边界；
- constraints：不能做什么、需要避免什么；
- examples：示例输入输出或操作轨迹；
- verifier checklist：后续验证用清单。

### 4.2 SPARK-PDI 风格的验证层

不要只相信生成出来的计划或描述，而要检查 skill 中的关键声明是否有证据支持。

可以先做简化版：

- 每条能力声明需要对应 evidence chunk；
- 每条行为规则需要能追溯到材料来源；
- 没有证据的内容标记为 unsupported；
- 有冲突的内容标记为 contradiction；
- 允许用户反馈后生成修正版 skill。

### 4.3 轻量化调用优化层

效率是明确优化方向，但不替代“可验证蒸馏”这条主线。基础 demo 稳定后，增加面向实际调用的轻量化版本和成本指标。

候选方向：

- full skill package 与 compact invocation skill 对比；
- token 数量对比；
- verifier 调用次数对比；
- cheap-first verifier cascade；
- 修正轮数统计；
- 在压缩后检查 checklist pass 是否保持。

## 5. 当前优先级

1. 阅读并总结 `SPARK-PDI`。
2. 审查 `SPARK-PDI` 仓库，判断能否直接跑通或需要简化复现。
3. 阅读并总结 `COLLEAGUE.SKILL`。
4. 审查 `COLLEAGUE.SKILL` 仓库，判断哪些 schema、流程或代码可借用。
5. 选择安全 demo 场景，优先考虑：
   - 论文评审专家 skill；
   - 代码审查专家 skill；
   - 项目管理工作流 skill。
6. 实现最小可跑 pipeline。
7. 实现验证与反馈修正。
8. 添加轻量化调用与成本对比实验。
9. 组装 demo 脚本与最终报告。

## 6. 当前边界与风险

- 不承诺完整复现两篇论文所有实验。
- 不使用私人聊天记录、内部文档或未经授权的专家材料。
- 不把生成出的 skill 宣称为自动正确，只说它是可检查、可追溯、可修正的。
- 不把本任务直接包装成未来主论文，只把它作为“蒸馏是迁移前序环节”的原型探索。

## 7. 下一步产出

下一步应该进入论文和代码审查阶段，优先产出：

- `D:\solution\reports\REPRO_AUDIT.md`
- `D:\solution\reports\SPARK_PDI_REPRO_NOTES.md`
- `D:\solution\reports\COLLEAGUE_SKILL_CODE_AUDIT.md`

这两份报告需要回答：

- 论文输入是什么；
- 论文输出是什么；
- 核心 pipeline 是什么；
- 验证机制是什么；
- 代码是否能运行；
- 两周内哪些部分可复现；
- 哪些部分需要简化；
- 我们可以在哪里加入效率改进。
