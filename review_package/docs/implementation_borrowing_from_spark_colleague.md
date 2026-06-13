# 实现借鉴与差距收束

本轮目标不是继续堆内部文档，而是把 Demo 改成用户能感知价值的产品形态：用户输入任务材料，系统生成 Skill，随后用无 Skill、初始 Skill、优化后 Skill 三次运行证明它是否真的帮助解决任务。

## 本项目自己的通俗链路

```text
专家材料 / 任务资产
-> full / compact deployment skill
-> agent execution
-> posterior verifier / trajectory feedback
-> failure attribution
-> type-specific patch / gate / rollback / selective trace
-> revised deployment skill or infeasible report
```

更直白地说，本项目不是只做“专家材料总结”，也不是只做“规则列表生成”。它把生成的 Skill 当作一个可部署假设：只有放到任务里执行之后，后验反馈才决定这个 Skill 应该补、拒绝、回滚、加 trace，还是报告预算下不可行。

当前需要诚实说明：网页默认链路里的“执行”是受控 API-review agent/output 层，不是 SPARK 那种 WSL2 / Harbor / Docker 中的真实 agent sandbox。仓库已经有 mock agent、OpenAI-compatible LLM agent、Harbor/SPARK 转换器和 WSL runbook，但还没有把 WSL2 真实 agent 运行作为网页默认后端接进去。

## 本项目自己的创新点

1. 后验 Skill 修正  
   生成的 Skill 不是最终答案，而是 deployment hypothesis。执行后的 verifier / trajectory 反馈决定 patch、reject、trace、rollback 或 infeasible。

2. 正确性约束下的 compact skill 部署  
   问题不是单纯压缩 prompt，而是在 token budget、验证成本、输出契约、回归风险和 traceability 约束下生成 deployment skill package。

3. 类型化后验决策矩阵  
   不同失败类型对应不同动作：`missing_rule -> patch`，`output_format_error -> rewrite output contract`，`regression_observed -> reject_and_rollback`，`rule_id_shortcut / fake_trace_evidence -> strengthen trace verifier`。

4. Validation-aware compiler / gate  
   修补当前失败不等于可以部署。候选 Skill 需要检查预算、已覆盖能力是否回归、failure-critical 能力是否保留、semantic / trace verifier 是否通过；不满足时应 reject、rollback 或报告 infeasible。

5. 风险预算下的 selective trace  
   full trace 能增强验证但会增加 token / protocol 成本。本项目探索把 trace 预算分给 failure-critical、高风险、新 patch 的能力，而不是全量 trace。

6. Artifact-backed 证据链  
   关键结论不是页面静态解释，而是能追到运行产物：attempt output、verifier feedback、patch/gate、Skill manifest、纠错报告和最终报告。

## 已拉取/落地的外部实现

- COLLEAGUE.SKILL 已完整浅克隆到 `external_repos/colleague-skill`。
- SPARK-PDI 对应仓库 `EtaYang10th/spark-skills` 的完整 clone 多次因网络传输中断未完成。已确认远端 HEAD 可访问；`git clone --depth 1 --single-branch` 最终失败信息为 `RPC failed; curl 56 Recv failure: Connection was reset` / `early EOF`，因此不是本地路径或仓库地址错误。为继续推进实现对比，已通过 raw snapshot 拉取核心源码到 `external_repos/spark_raw_snapshot`：
  - `spark_skills_gen/pipeline.py`
  - `spark_skills_gen/evaluator.py`
  - `spark_skills_gen/executor.py`
  - `spark_skills_gen/judge.py`
  - `spark_skills_gen/skill_evidence.py`
  - `spark_skills_gen/trajectory.py`
  - `spark_skills_gen/dashboard/app.py`

## 从 SPARK-PDI 借鉴的实现思想

SPARK-PDI 的强项不是“展示了很多规则”，而是把任务尝试、失败、反馈、重试和最终 Skill 蒸馏组织成可复查轨迹。对应到本项目，前端不再把规则表作为主内容，而是展示：

- A0 无 Skill baseline：用户只看任务本身时的输出。
- A1 初始 Skill：专家材料转成 Skill 后的首次执行结果。
- Verifier feedback：A1 具体漏了什么能力、证据是否足够。
- A2 优化后 Skill：后验修正后是否通过、是否新增有效 findings。
- token 成本和证据字段完整性：让用户看到“有用”和“代价”。

当前已落地在 `demo/streamlit_app.py`：

- `attempt_output(...)` 生成 A0/A1/A2 三阶段输出。
- `verify(...)` 计算 coverage、missing capabilities 和 PASS/FAIL。
- `write_run_artifacts(...)` 写入报告、manifest、verifier feedback。
- 前端首屏只显示任务是否解决、成功率、token、报告入口。

## 当前执行层边界

| 层次 | 当前状态 |
|---|---|
| 网页默认执行 | 受控安全审查任务，mock / OpenAI-compatible API-review agent 输出，本地 verifier，A0/A1/A2 对比 |
| 仓库已有支撑 | `agents/api_review_mock_agent.py`、`agents/api_review_llm_agent.py`、`integrations/spark/*`、`docs/RUNBOOK.md` 中的 WSL2/Harbor 命令 |
| 尚未做到 | SPARK 式 WSL2/Harbor/Docker 现场运行真实 agent，记录 agent commands、stdout、测试、失败重试和完整 trajectory |
| 下一步 | 把 WSL2/Harbor agent run 接成可选执行后端，让网页显示真实 job 状态、stdout tail、`attempts.json`、`trajectory.jsonl` |

## 从 COLLEAGUE.SKILL 借鉴的实现思想

COLLEAGUE.SKILL 更像一个成熟 Skill 项目：它强调 schema、manifest、版本、artifact writer、version manager 和 rollback。对应到本项目，Skill 不应只是页面文本，而应有可落盘产物和生命周期入口。

当前已落地：

- `skill_package_v2_manifest.json` 记录 Skill 名称、版本、能力、输出契约和外部借鉴来源。
- `correction_report.md` 记录 v1 为什么失败、v2 补了什么。
- `final_report.md` 作为外部评审可读报告入口。
- 页面“证据入口”中可以预览每个产物，而不是把所有文档铺在首屏。

## 仍需弥补的差距

1. SPARK 的真实多任务评估矩阵还没有完全移植。本项目目前是受控安全审查样例，下一步应加入 5-10 个安全任务 case，展示平均成功率和失败类型分布。
2. COLLEAGUE.SKILL 的版本回滚工具还没有接入本项目 CLI。下一步可把 Skill v1/v2 存成标准版本目录，并加入 rollback/list 命令。
3. 当前 verifier 是轻量本地检查器。下一步应把验证契约拆成独立 YAML/JSON schema，并让每个 case 复用。
4. 真实模型模式已经预留 OpenAI-compatible 接口，但现场是否调用取决于环境变量，不会硬编码密钥。

## 展示口径

面向用户时不要讲“规则账本优先”，而是讲：

> 你给任务材料，系统生成一个可执行 Skill。我们用无 Skill、初始 Skill、优化后 Skill 三次运行证明它有没有帮助：成功率是否提升、漏检是否减少、报告是否更可执行、token 成本是多少。
