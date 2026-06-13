# 场景驱动的专家技能蒸馏与后验修正工作台：详细设计

## 1. 一句话定位

本系统不是把任意文本总结成 prompt，也不是直接根据用户目标生成一套方法；它是在具体任务场景中，将专家材料、任务约束和目标资产蒸馏为可执行、可验证、可后验修正的 Skill Package。

核心链路：

```text
任务场景 + 专家材料包 + 目标资产包 + 任务规格
-> 抽取规则账本
-> Skill Package v1
-> 目标资产执行
-> Verifier 后验反馈
-> Patch / Gate
-> Skill Package v2
-> A2 rerun 验证
```

## 2. 当前 demo 面向的任务范围

当前原型聚焦受控漏洞挖掘 / 安全审查场景，不连接真实网络目标，不执行漏洞利用。内置三个稳定场景：

1. 文件上传漏洞挖掘技能
2. 鉴权与越权审查技能
3. 配置安全检查技能

自定义模式用于新建受控安全审查场景，用户必须提供：

- 任务目标
- 专家材料
- 目标资产
- 输出要求
- 验证标准

系统会尝试从这些输入中抽取规则候选、证据要求和输出契约；严格 verifier 当前支持受控安全审查模板，用于演示 scenario-conditioned skill distillation，而不是通用漏洞扫描。

## 3. 对象模型

### 3.1 任务场景

任务场景定义“为什么蒸馏”和“蒸馏后在哪里使用”。场景卡片展示：

- 场景目标
- 专家材料来源
- 目标资产类型
- 要生成的 Skill Package
- verifier 能检查什么
- 当前版本状态

### 3.2 专家材料包

专家材料包是原始知识来源，不等于规则表。页面和运行产物中表示为：

```text
source_materials/
  security_review_guide.md
  evidence_requirements.md
  output_report_spec.md
  examples.md
  anti_examples.md
  boundary.md
```

### 3.3 抽取规则账本

规则账本是从专家材料中结构化抽取出的中间层，例如：

```text
R002 用户输入校验
R004 敏感信息泄露
R005 文件上传安全
R006 审计日志保留
R008 路径穿越
```

它用于生成 Skill Package 和解释后验修正，但不被称为专家材料本身。

### 3.4 目标资产包

目标资产包是 Skill 的执行对象：

```text
target_asset/
  task_brief.md
  api.yaml
  app.py
  config.yaml
```

### 3.5 任务规格

任务规格定义本次 Skill 的验收边界：

- 场景目标
- 报告格式
- 验证标准
- 禁止行为

### 3.6 Skill Package

成熟 Skill 在 demo 中表示为版本化目录，而不是单段 prompt：

```text
skill_packages/<scenario>/v1/
  manifest.yaml
  SKILL.md
  rules/*.yaml
  contracts/output_schema.json
  contracts/verifier_contract.yaml
  trace_policy.yaml
  examples/*.md
  eval_cases/*.yaml
  changelog.md
```

v2 目录同构，但会体现新增规则、契约强化、trace policy 强化和 changelog。

### 3.7 运行产物

每次执行保存完整证据：

```text
runs/demo_session_<scenario>_<mode>/
  source_materials/
  task_spec/
  target_asset/
  skills/skill_v1/
  skills/skill_v2/
  attempts/
    A0_no_skill_output.json
    A0_no_skill_verifier_report.json
    A1_agent_output.json
    A1_trace.jsonl
    A1_verifier_report.json
    A2_agent_output.json
    A2_trace.jsonl
    A2_verifier_report.json
  revision/
    patch_proposal.json
    gate_decision.json
    rule_ledger.json
    skill_directory_diff.md
  summary/
    before_after_metrics.json
```

## 4. 核心流程

### 4.1 A0：无 Skill baseline

系统先在不加载专家材料包、不加载规则账本的条件下执行目标资产检查。该 baseline 通常无法形成有效 finding，verifier 标记为 FAIL。

目的：展示“没有专家技能”时无法解决任务。

### 4.2 Skill v1：初始蒸馏

系统从专家材料包和任务规格中生成抽取规则账本，再编译为 Skill Package v1。v1 是 compact skill，可能因压缩漏掉部分低显著但关键的规则。

目的：展示“专家材料可以转成可部署技能包”，同时保留真实失败空间。

### 4.3 A1：执行与失败捕捉

Skill v1 在目标资产包上执行，产生：

- agent input
- agent findings
- trace evidence
- verifier report

verifier 不在主流程暴露答案，只展示：

```text
agent observed findings -> verifier computed missing requirements
```

### 4.4 后验修正

系统根据 verifier report 选择 typed repair operator：

- `missing_rule -> patch_rule`
- `output_contract_error -> rewrite_output_contract`
- `failure_critical_rule -> add_trace_requirement`
- `regression_observed -> reject_and_rollback`

### 4.5 Gate

Gate 检查：

- v2 verifier 是否 PASS
- 是否丢失 v1 已覆盖规则
- token cost 是否在预算内
- trace / contract 是否满足要求

### 4.6 Skill v2 与 A2 rerun

v2 是后验修正后的 Skill Package。A2 使用 v2 重新执行目标资产，预期达到 PASS。

## 5. 对 SPARK-PDI 与 COLLEAGUE.SKILL 的借鉴边界

本原型借鉴机制，不宣称完整复现。

SPARK-PDI 风格：

- 关注 evidence-first trajectory verification。
- 将 trace、attempt output、verifier report、posterior feedback 作为一等产物。
- 不只相信 prior plan，而用执行证据修正 skill。

COLLEAGUE.SKILL 风格：

- Skill 是版本化、可检查、可修正的对象。
- 用 package directory 展示技能本体。
- 保留 manifest、rules、contracts、examples、eval cases、changelog。

未宣称内容：

- 不宣称完整复现两篇论文实验。
- 不宣称通用漏洞扫描器。
- 不宣称生成 Skill 自动正确。
- 不执行真实漏洞利用。

## 6. 评审建议关注点

外部评审可以重点看：

1. 场景驱动定位是否清楚。
2. 专家材料包、规则账本、Skill Package、目标资产包、运行产物是否边界清楚。
3. 无 Skill baseline / Skill v1 / Skill v2 的对比是否说明了 Skill 的作用。
4. verifier feedback 是否像后验反馈，而不是提前暴露答案。
5. Skill Package 目录是否足够像可部署对象。
6. 当前简化规则库是否能支撑两周原型目标。
7. 下一步是否需要接入更真实的安全审查数据或更强的 evaluator。

## 7. 演示脚本

推荐演示文件上传场景：

1. 说明系统定位：场景驱动，不是文本总结器。
2. 展示三类输入：专家材料包、目标资产包、任务规格。
3. 展示 A0 无 Skill baseline：FAIL。
4. 点击生成 Skill v1，展示 package directory。
5. 运行 A1，展示 observed findings 和 verifier computed missing requirements。
6. 生成 patch / gate，展示修正算子。
7. 生成 Skill v2，展示目录级 diff。
8. 运行 A2，展示 PASS。
9. 打开运行产物目录，说明可追溯证据。

## 8. 黄金演示样例：文件上传漏洞挖掘技能

当前主演示优先打磨文件上传场景，其它两个场景先作为场景库存在。黄金路径强调：

1. 专家材料包足够厚：`security_review_guide.md` 不只是 checklist，而包含上传类型校验、路径处理、公开访问、错误响应、审计链路和输出要求。
2. A0 是 naive agent baseline：只给任务目标和目标资产，不给专家材料包、不加载 Skill；它会产生泛泛发现，但缺少 `rule_id`、`evidence_span`、`recommended_fix`，因此 verifier FAIL。
3. Skill v1 是 compact package：页面展示目录和 compact decision ledger，解释哪些规则因预算/显著性被暂时省略。
4. A1 失败有过程：展示 observed findings、trace、verifier report 和 missing requirements。
5. v1 -> v2 是目录级 diff：新增 rule 文件，修改 output schema、trace policy 和 changelog。
6. A2 改进直观：报告 diff 展示新增 finding、evidence_span、recommended_fix，并最终 PASS。

页面第一入口现在是“价值链总览”，集中展示四个强对比视图：

1. 材料到 Skill 的来源对齐：专家材料原文片段 -> 抽取规则账本 -> Skill Package 文件。
2. Skill v1 -> Skill v2 目录级变化：新增/修改文件及其来源反馈。
3. A0 / A1 / A2 效果差异：verifier 结果、结构化 finding 数、覆盖/缺失规则、字段完整率。
4. 系统设计厚度：六个模块的输入输出，说明它不是 checklist。

## 9. LLM 与本地模块边界

真实模型模式下：

LLM 可用于：

- 从专家材料中抽取规则候选、证据要求和输出契约预览。
- 根据 Skill Package 执行目标资产审查，生成 agent findings。
- 生成 patch proposal 的自然语言解释。

本地确定性模块用于：

- verifier 覆盖率、schema、evidence_span 检查。
- gate 决策和回归保护。
- artifact 落盘、目录级 diff。
- 离线演示模式下的可复现执行。

这样划分可以避免“到底哪里用了模型、哪里是规则程序”的混淆。
