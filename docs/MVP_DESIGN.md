# MVP 设计：基于证据与执行反馈的专家 Skill 蒸馏原型系统

## 1. 系统目标

本项目的 MVP 目标是构建一个 **基于证据与执行反馈的专家 Skill 蒸馏原型系统**。

英文表述：

```text
Evidence-grounded Expert Skill Distillation with Execution Feedback
```

中文表述：

```text
基于证据与执行反馈的专家 Skill 蒸馏原型系统
```

核心目标不是只生成一个看起来合理的 skill，也不是单纯做成本统计，而是展示一个最小闭环：

```text
专家材料
-> 初始 full skill package
-> 材料证据验证
-> compact skill v1
-> 真实任务执行
-> trajectory / judge 反馈
-> skill patch
-> skill v2
-> 成本与效果对比
```

一句话定位：

> 生成要可信，执行要有效，调用要尽量轻。

## 2. 两篇论文分别提供什么机制

### 2.1 COLLEAGUE.SKILL 提供的机制

`COLLEAGUE.SKILL` 的价值不在于我们要复刻它的人格模拟场景，而在于它提供了一种可工程化的 skill package 生命周期。

可借鉴机制：

- 异构材料整理为 skill package；
- versioned skill package；
- capability track；
- bounded behavior track；
- correction lifecycle；
- artifact writer；
- manifest / metadata；
- update / rollback。

在我们的 MVP 中，对应为：

```text
专家材料
-> full_skill.md
-> manifest.json
-> repair_log.md
-> skill version update
```

### 2.2 SPARK-PDI 提供的机制

`SPARK-PDI` 的价值在于强调 skill 不能只来自 prior plan，而应该 grounded in posterior execution evidence。

可借鉴机制：

- trajectory-level verification；
- execution evidence；
- judge / verifier signal；
- PDI diagnostic；
- online intervention；
- successful trajectory distillation；
- evidence blocks。

在我们的 MVP 中，对应为：

```text
compact skill
-> task execution
-> execution_report.json
-> failure analysis
-> skill patch
```

### 2.3 我们的整合点

我们不是简单拼接两篇工作，而是把它们放进同一个闭环：

```text
COLLEAGUE.SKILL: 专家材料 -> skill package
SPARK-PDI: execution trajectory -> evidence / verifier feedback
Our MVP: 专家材料 -> verified skill -> compact skill -> execution feedback -> patched skill
```

## 3. 统一 Skill Package 结构

MVP 输出一个统一目录，每次 demo 至少包含：

```text
outputs/<run_id>/
  full_skill.md
  compact_skill_v1.md
  compact_skill_v2.md
  evidence_map.json
  evidence_report.md
  execution_report_v1.json
  execution_report_v2.json
  repair_log.md
  cost_summary.json
  manifest.json
```

### 3.1 full_skill.md

用途：

- 审查；
- 维护；
- 追溯；
- 人类读懂专家知识从哪里来。

包含：

- 专家任务范围；
- capability track；
- bounded behavior track；
- workflow；
- rules；
- constraints；
- examples；
- output format；
- evidence references；
- version notes。

### 3.2 compact_skill.md

用途：

- 实际调用；
- 执行任务；
- 降低上下文长度；
- 减少无效规则干扰。

保留：

- 有专家材料证据的规则；
- 真实执行中触发过的规则；
- 失败后修正得到的规则；
- 对 verifier / judge 关键的输出格式要求；
- 高优先级 checklist。

压缩或删除：

- 重复解释；
- 弱证据规则；
- 背景性文本；
- 执行中从未触发的冗余步骤；
- 仅用于审查维护的历史说明。

### 3.3 evidence_map.json

用途：

- 记录每条 skill rule 对应哪些来源证据。

建议字段：

```json
{
  "rule_id": "R001",
  "rule_text": "所有接口必须说明鉴权方式。",
  "evidence_ids": ["E001", "E004"],
  "status": "supported",
  "risk": "low",
  "suggestion": ""
}
```

状态：

- `supported`：证据明确支持；
- `weak`：有相关证据，但可能过度泛化；
- `unsupported`：没有找到明确来源；
- `conflict`：与材料或其他规则冲突；
- `execution_critical`：执行或 judge 反馈表明该规则关键。

### 3.4 execution_report.json

用途：

- 记录 compact skill 在真实或模拟任务中的执行结果。

建议字段：

```json
{
  "variant": "compact_skill_v1",
  "task_id": "api_review_case_001",
  "passed": false,
  "checklist_passed": 5,
  "checklist_total": 7,
  "failure_types": ["missing_error_code_check"],
  "retry_count": 2,
  "verifier_calls": 3,
  "input_tokens": 3200,
  "output_tokens": 900,
  "latency_ms": 12000
}
```

### 3.5 repair_log.md

用途：

- 把材料验证或执行反馈转成 skill patch。

示例：

```text
## Patch P001

Source:
- execution_report_v1.json

Problem:
- compact_skill_v1 没有要求检查错误码一致性。

Patch:
- 在 compact_skill_v2 中新增规则：
  检查错误码是否覆盖成功、参数错误、权限错误、服务异常。

Expected effect:
- 减少 API review 中遗漏异常路径的问题。
```

### 3.6 cost_summary.json

用途：

- 记录成本不是为了事后统计，而是为了说明系统机制如何减少无效上下文、重复验证和重试。

建议字段：

```json
{
  "variants": [
    {
      "name": "no_skill",
      "input_tokens": 0,
      "verifier_calls": 0,
      "retry_count": 0,
      "passed": false
    },
    {
      "name": "full_skill",
      "input_tokens": 5200,
      "verifier_calls": 3,
      "retry_count": 2,
      "passed": true
    },
    {
      "name": "compact_skill_v1",
      "input_tokens": 2100,
      "verifier_calls": 2,
      "retry_count": 2,
      "passed": false
    },
    {
      "name": "compact_skill_v2",
      "input_tokens": 2400,
      "verifier_calls": 2,
      "retry_count": 1,
      "passed": true
    }
  ]
}
```

## 4. 最小 Demo 场景

推荐场景：

```text
API / 代码评审专家知识蒸馏
```

输入专家材料：

- API 设计规范；
- 接口评审 checklist；
- 合成专家历史评审意见；
- 正反例 API 设计片段。

skill 需要检查：

- 鉴权是否说明；
- 输入校验是否完整；
- 错误码是否规范；
- 是否有敏感信息泄露；
- 接口返回格式是否一致；
- 异常情况是否覆盖；
- 是否说明分页、幂等、限流等边界。

选择原因：

- 规则明确；
- 数据容易合成；
- 不涉及隐私；
- 可做 evidence coverage；
- 可做真实或模拟执行；
- 可做 compact skill 对比。

## 5. MVP 闭环流程

### Step 1: Material Ingestion

输入安全专家材料，切分为 evidence chunks。

输出：

- `materials_index.json`
- evidence chunks。

### Step 2: Skill Distillation

从专家材料生成 full skill。

输出：

- `full_skill.md`
- 初始 rule list。

### Step 3: Evidence Verification

对每条 rule 做证据覆盖检查。

输出：

- `evidence_map.json`
- `evidence_report.md`

### Step 4: Evidence-guided Compact Skill

根据 evidence status 生成 compact skill v1。

保留：

- supported rules；
- high priority rules；
- output format；
- verifier-critical checklist。

输出：

- `compact_skill_v1.md`

### Step 5: Real Task Execution

用 no skill、full skill、compact skill v1 分别执行同一组小任务。

输出：

- `execution_report_no_skill.json`
- `execution_report_full_skill.json`
- `execution_report_v1.json`

### Step 6: Execution-feedback Patch

把失败类型转成 skill patch。

输出：

- `repair_log.md`
- `compact_skill_v2.md`

### Step 7: Re-run and Compare

用 patched compact skill v2 再执行任务。

输出：

- `execution_report_v2.json`
- `cost_summary.json`

## 6. 成本优化机制

成本不是最后统计，而是进入系统设计本身。

### 6.1 Evidence-guided Compact Skill

目标：

- 减少上下文长度；
- 减少弱证据规则干扰；
- 保留被证据或执行反馈证明有用的规则。

机制：

```text
full skill
-> evidence status filtering
-> execution-critical rule retention
-> compact skill
```

### 6.2 Cheap-first Verification

目标：

- 不让所有验证都调用大模型；
- 降低 verifier 调用成本；
- 提前发现格式、schema、证据缺失问题。

验证 cascade：

```text
第一层：schema / 格式检查
第二层：规则证据覆盖检查
第三层：小任务 checklist 验证
第四层：必要时才调用 LLM verifier
```

优化指标：

- verifier calls；
- repair rounds；
- failed LLM calls；
- total latency。

### 6.3 Execution-feedback Patch

目标：

- 让执行轨迹不只是日志，而是能回写 skill。

机制：

```text
execution failure
-> failure type
-> missing / weak rule diagnosis
-> compact skill patch
-> rerun
```

示例：

```text
失败原因：
agent 没有检查 API 错误码一致性。

patch：
在 compact_skill_v2 中新增：
- 检查错误码是否覆盖成功、参数错误、权限错误、服务异常。
```

## 7. 指标与对比组

### 7.1 最小对比组

```text
A. no skill
B. full skill
C. compact skill v1
D. compact skill v2 after execution feedback
```

### 7.2 评估问题

```text
skill 有没有帮助？
compact skill 是否更省？
execution feedback 是否让 skill 变好？
```

### 7.3 指标

核心指标：

- 是否完成任务；
- checklist pass；
- failure types；
- retry count；
- verifier calls；
- input tokens；
- output tokens；
- latency；
- repair rounds。

谨慎使用：

- 小样本成功率；
- 单次运行正确率提升；
- LLM 主观评分。

推荐表述：

> 在保持验证通过或 checklist 覆盖不下降的前提下，降低上下文长度、验证调用次数和重试成本。

## 8. 两周交付边界

必须完成：

- 安全 demo 数据；
- full skill 生成；
- evidence report；
- compact skill v1；
- 至少一个执行任务；
- execution report；
- repair log；
- compact skill v2；
- cost/effect comparison；
- demo script；
- prototype report。

尽量完成：

- WSL2 + Docker + Harbor 跑通 SPARK 的一个小任务；
- cheap-first verifier cascade；
- 多个 API review case；
- 简单命令行 demo。

不承诺：

- 完整复现两篇论文所有实验；
- 大规模 benchmark；
- 稳定显著的成功率提升；
- 自动生成完全正确的专家 skill；
- 使用真实私人专家数据。

## 9. 当前优先级

1. 准备 WSL2 / Docker / uv / Harbor 环境，用于尝试完整 SPARK 最小任务。
2. 同时推进无 Docker 的 MVP pipeline，避免环境阻塞主线。
3. 定义 `SKILL_PACKAGE_SCHEMA.md`。
4. 构造 API / 代码评审 demo 数据。
5. 实现最小闭环：

```text
materials -> full_skill -> evidence_report -> compact_v1 -> execution_report -> repair_log -> compact_v2 -> cost_summary
```

