# Demo 设计：基于证据与执行反馈的专家 Skill 蒸馏原型

## 1. 总体目标

本项目目标是做一个“基于证据与执行反馈的专家 Skill 蒸馏原型系统”。

当前更精确的 MVP 设计见：

- `D:\solution\docs\MVP_DESIGN.md`

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
-> Demo 展示与开源原型
```

核心表达：

我们不是从零复现别人系统，而是把 `COLLEAGUE.SKILL` 的专家材料蒸馏能力和 `SPARK-PDI` 的证据 / 轨迹验证机制接起来，做成一个可演示、可检查、可修正、可执行优化的专家知识蒸馏原型。成本不是最后统计，而是通过 compact skill、cheap-first verification 和 execution-feedback patch 进入系统设计。

## 2. 系统三层结构

### 2.1 第一层：可复现审查

先确认两篇开源工作的真实可用程度。

审查问题：

- 仓库能不能安装；
- demo 能不能跑；
- 核心 pipeline 在哪里；
- 输入输出格式是什么；
- 哪些部分依赖 API、数据、Docker 或隐藏配置；
- 两周内哪些部分能直接用于 demo；
- 哪些部分只能作为思想复现或局部复现。

产物：

- `D:\solution\reports\REPRO_AUDIT.md`

审查重点：

- `COLLEAGUE.SKILL` 是否能从专家材料生成 skill package；
- `COLLEAGUE.SKILL` 的 artifact 结构是什么；
- `COLLEAGUE.SKILL` 的输入材料格式是什么；
- `COLLEAGUE.SKILL` 是否适合直接接入 demo；
- `SPARK-PDI` 是否能跑通轨迹验证或证据验证流程；
- `SPARK-PDI` 是否能复用代码或数据；
- `SPARK-PDI` 哪些模块可以抽取；
- 如果完整复现困难，offline fallback 如何设计。

这一层的意义是：先搞清楚别人系统的真实可用程度，避免两周时间耗在环境问题上。

### 2.2 第二层：机制整合

把两篇文章抽象成我们自己的原型主线。

```text
COLLEAGUE.SKILL:
专家材料 -> skill package

SPARK-PDI:
skill / 轨迹 -> evidence verification / trajectory verification

我们的原型:
专家材料 -> skill package -> evidence verification -> repair -> compact invocation skill
```

我们的系统不是简单拼接，而是形成闭环：

```text
生成 skill
-> 检查 skill 是否有证据支撑
-> 发现 unsupported / weak / conflict 规则
-> 反馈给蒸馏模块修正
-> 重新生成或更新 skill
-> 通过验证后生成轻量调用版本
```

### 2.3 第三层：优化方向

效率是本项目的明确优化方向，但不是替代“可验证蒸馏”的主线。

建议表述为：

在可验证 skill 的基础上，补充一个面向实际调用的轻量化部署层，使系统不仅能生成可检查、可修正的 full skill，也能生成更适合实际调用的 compact skill。

这里的逻辑是：

- 主线：专家知识蒸馏与证据验证；
- 优化方向：轻量化调用与工程成本控制；
- 展示方式：用 token、调用次数、修正轮数和 checklist pass 等指标说明部署优势。

## 3. 原型模块设计

### 3.1 Material Ingestion

输入专家材料，例如：

- Markdown 文档；
- PDF 或文档片段；
- 公开指南；
- 合成专家说明；
- 案例记录；
- 少量正反例。

输出：

- 标准化材料片段；
- evidence chunks；
- 来源位置；
- 数据安全记录。

### 3.2 Skill Distiller

生成 full skill package。

Full skill package 包含：

- 能力说明；
- 专家规则；
- 工作流程；
- 行为边界；
- 输出格式；
- 示例；
- verifier checklist；
- evidence 引用字段；
- 修正历史。

### 3.3 Evidence Verifier

检查 skill 规则是否有材料证据或执行轨迹支撑。

每条规则至少给出：

- rule id；
- rule text；
- evidence source；
- evidence location；
- status；
- issue；
- suggestion。

状态类型：

- `supported`：证据明确支持；
- `weak`：有相关证据，但规则可能过度泛化；
- `unsupported`：找不到明确来源；
- `conflict`：与材料或其他规则冲突。

### 3.4 Repair Loop

根据 evidence report 修正 skill。

初版可以半自动：

- `unsupported` 规则删除或降级；
- `weak` 规则改成建议性规则；
- `conflict` 规则标注冲突并请求人工确认；
- 修正后生成新版本 skill；
- 保留 version log。

### 3.5 Compact Skill Builder

验证通过后生成 compact invocation skill。

保留：

- supported 且 high priority 的规则；
- 关键 checklist；
- 输出格式；
- 关键边界条件；
- 少量高价值示例。

删除或压缩：

- 长背景；
- 重复解释；
- 低证据规则；
- 修正历史；
- 仅用于审查维护的元数据。

## 4. Full Skill 与 Compact Skill 分离

系统生成两个版本。

### 4.1 Full Skill Package

用于审查、维护和追溯。

包含：

- 完整专家知识；
- 来源证据；
- 长示例；
- 行为边界；
- 修正历史；
- 解释性内容。

### 4.2 Compact Invocation Skill

用于实际调用、部署和演示。

包含：

- 实际调用时需要的核心规则；
- 简短 checklist；
- 输出格式；
- 关键边界条件；
- 少量高价值示例。

展示价值：

同一个专家 skill，完整版本用于审查、维护和追溯；轻量版本用于实际调用、部署和演示。

## 5. Evidence Coverage Report

Evidence Coverage Report 是系统可信性的核心。

它回答：

- 这条专家规则从哪里来；
- 有没有材料支撑；
- 有没有轨迹支撑；
- 是否过度泛化；
- 是否和材料冲突。

示例：

```text
Rule 1: 所有接口必须说明鉴权方式
Evidence: source_doc_1.md 第 12-18 行
Status: supported

Rule 2: 所有接口都必须使用 JWT
Evidence: 未找到明确来源
Status: unsupported
Suggestion: 降级为“需要说明认证方式”，不要强行指定 JWT
```

## 6. 轻量化调用优化与工程指标

轻量化是系统验证通过后的优化步骤。

它不替代 evidence verification，而是在 verified skill 的基础上生成更适合实际使用的调用版本。

可展示指标：

- Full skill token 数；
- Compact skill token 数；
- 压缩比例；
- 验证调用次数；
- 修正轮数；
- 任务 checklist pass；
- 延迟；
- 一次成功调用的平均成本。

推荐表述：

我们在保证 skill 可验证的前提下，生成更适合实际调用的轻量版本，并用 token、调用次数、修正轮数等指标展示系统部署优势。

不推荐表述：

```text
我们提出效率感知蒸馏方法。
```

更准确的表述是：

```text
我们把效率作为可验证 skill 之后的优化方向，重点探索 full skill 到 compact invocation skill 的转换与部署成本对比。
```

## 7. 推荐 Demo 场景

建议选择 **API / 代码评审专家知识蒸馏**。

输入材料：

- API 设计规范；
- 接口评审 checklist；
- 几条专家历史评审意见；
- 几个正反例。

输出 skill 用来检查：

- 鉴权是否说明；
- 输入校验是否完整；
- 错误码是否规范；
- 是否有敏感信息泄露；
- 接口返回格式是否一致；
- 异常情况是否覆盖。

选择原因：

- 规则明确；
- 容易构造测试样例；
- 容易做 evidence coverage；
- 容易展示 compact skill；
- 不涉及敏感隐私。

## 8. 最终 Demo 展示内容

最终 demo 页面或命令行输出应展示四个结果：

- Full Skill Package；
- Evidence Coverage Report；
- Repair Log；
- Compact Skill + Cost Summary。

推荐演示流程：

```text
1. 上传或读取专家材料
2. 系统生成 full skill package
3. 展示 evidence coverage report
4. 发现若干 unsupported / weak rules
5. 系统反馈修正
6. 重新生成 verified skill
7. 编译 compact invocation skill
8. 对比 full skill 和 compact skill 的 token、调用次数、pass 情况
```
