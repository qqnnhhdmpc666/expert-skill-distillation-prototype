# MVP Vertical Slice Plan

日期：2026-06-04

## 1. 目标

本 vertical slice 的目标是跑通一个最小但完整的专家 Skill 蒸馏闭环：

```text
API / 代码评审专家材料
-> full_skill.md
-> evidence_map.json
-> evidence_report.md
-> compact_skill_v1.md
-> execution_report_v1.json
-> repair_log.md
-> compact_skill_v2.md
-> cost_summary.json
```

本阶段不追求模型能力最强，而是先让 artifact 流动真实发生。模型生成可以先用 mock、固定模板或人工种子材料替代；系统结构必须先稳定。

## 2. Demo 输入

选择场景：

```text
API / 代码评审专家知识蒸馏
```

输入材料放在：

```text
data/api_review_expert_materials/
```

最小材料集合：

- `api_design_guidelines.md`：API 设计规范。
- `review_checklist.md`：专家评审 checklist。
- `historical_review_comments.md`：历史专家评审意见和正反例。

材料范围只包含公开、合成或脱敏内容，不使用私人聊天记录、真实客户接口或敏感业务数据。

## 3. Skill 要检查什么

MVP 中的 API review skill 先检查 7 类规则：

| Rule ID | 检查项 | 示例 |
|---|---|---|
| R001 | 鉴权与权限边界 | 是否说明认证方式、角色权限、越权风险 |
| R002 | 输入校验 | 必填字段、类型、范围、长度、枚举 |
| R003 | 错误码一致性 | 成功、参数错误、权限错误、资源不存在、服务异常 |
| R004 | 敏感信息保护 | token、手机号、身份证、内部错误栈是否泄露 |
| R005 | 响应格式稳定性 | envelope、字段命名、分页、空值策略 |
| R006 | 幂等性与重复提交 | POST/PUT/PATCH 是否说明幂等键或重复处理 |
| R007 | 可观测性 | request_id、审计日志、关键失败原因 |

初始 full skill 可以包含解释、证据、例子和边界；compact skill 只保留执行时真正需要的 checklist、判定标准和输出格式。

## 4. Artifact 定义

本 vertical slice 的输出目录：

```text
outputs/mvp_vertical_slice/<run_id>/
```

最小 artifact：

- `full_skill.md`
- `evidence_map.json`
- `evidence_report.md`
- `compact_skill_v1.md`
- `execution_report_v1.json`
- `repair_log.md`
- `compact_skill_v2.md`
- `execution_report_v2.json`
- `cost_summary.json`
- `manifest.json`

## 5. Full Skill 生成

输入：

```text
data/api_review_expert_materials/*.md
```

输出：

```text
full_skill.md
```

生成策略：

1. 先从专家材料抽取候选规则。
2. 每条规则分配 `rule_id`、`priority`、`category`。
3. 保留专家材料中的例子、边界、反例。
4. 不确定规则先标记为 `candidate`，不直接进入 compact skill。

MVP 可接受实现：

- 第一版可用固定模板 + 规则 seed。
- 后续再替换为真实 LLM distiller。

## 6. Evidence Map 与 Evidence Report

输出：

```text
evidence_map.json
evidence_report.md
```

`evidence_map.json` 字段：

```json
{
  "rule_id": "R001",
  "rule_text": "接口必须说明鉴权方式和权限边界。",
  "category": "auth",
  "evidence": [
    {
      "source_id": "api_design_guidelines.md",
      "location": "section: Authentication",
      "quote": "Every endpoint must document authentication and authorization boundaries."
    }
  ],
  "status": "supported",
  "risk": "low",
  "suggestion": ""
}
```

状态定义：

- `supported`：材料中有明确证据。
- `weak`：材料相关但表达不够直接，可能过度泛化。
- `unsupported`：未找到材料依据。
- `conflict`：与材料或其他规则冲突。
- `execution_critical`：执行反馈证明该规则影响任务通过。

## 7. Compact Skill v1

输出：

```text
compact_skill_v1.md
```

保留规则：

- `supported` 的高优先级规则。
- 对 verifier / checklist 输出格式关键的规则。
- demo 场景中一定会触发的规则。

删除或降级：

- `unsupported` 规则。
- 仅用于背景解释的长段落。
- 重复例子。
- 与执行任务无关的规则。

最小 compact skill 格式：

```text
# API Review Compact Skill

## Checklist
- [R001] Check authentication and authorization boundaries.
- [R002] Check input validation.
...

## Output Format
Return JSON with:
- passed
- failed_rules
- findings
- suggested_patch
```

## 8. 执行任务

MVP 执行任务不是让 agent 写复杂项目，而是让 agent 基于 compact skill 审查一个合成 API spec。

输入任务：

```text
data/api_review_cases/case_001_openapi.md
```

任务要求：

```text
Read the API spec and produce a review report in the required JSON format.
```

Verifier / judge 检查：

- 是否指出缺少鉴权说明。
- 是否指出缺少错误码覆盖。
- 是否指出敏感字段返回风险。
- 是否按指定 JSON 格式输出。

第一版可以不用真实 LLM agent，先用 deterministic runner / simulated execution report。后续再接 Harbor task。

## 9. Compact Skill 如何注入执行上下文

注入方式：

```text
instruction.md
+ compact_skill_v1.md
+ target_api_spec.md
+ required_output_format.md
```

如果使用 Harbor：

- 将 `compact_skill_v1.md` 复制到 task 目录，例如 `/root/skill.md` 或任务目录下 `skills/API_REVIEW_SKILL.md`。
- 在 `instruction.md` 中明确要求 agent 先阅读 skill，再输出 review JSON。
- verifier 只检查最终输出，不直接读取 skill。

如果使用本地 simulated runner：

- runner 读取 `compact_skill_v1.md` 和 case 文件。
- 输出 `execution_report_v1.json`。

## 10. Trajectory / Judge Result 如何回写

SPARK 接口目标：

```text
trajectory.jsonl / attempts.json
-> execution_report_v1.json
-> repair_log.md
-> compact_skill_v2.md
```

`execution_report_v1.json` 字段：

```json
{
  "variant": "compact_skill_v1",
  "task_id": "api_review_case_001",
  "passed": false,
  "checklist_passed": 5,
  "checklist_total": 7,
  "failure_types": ["missing_error_code_check"],
  "retry_count": 1,
  "verifier_calls": 1,
  "input_tokens": 1800,
  "output_tokens": 500,
  "latency_ms": 3000,
  "trajectory_source": "simulated"
}
```

SPARK adapter 需要做两件事：

1. 将 `attempts.json` / `trajectory.jsonl` 转成统一 `execution_report.json`。
2. 将失败类型映射成 rule-level patch。

示例：

```text
failure: missing_error_code_check
-> affected_rule: R003
-> patch: Promote R003 from optional note to must-check item.
```

## 11. Repair Log 与 Compact Skill v2

`repair_log.md` 记录：

- failure source
- affected rule
- evidence status
- patch action
- expected effect

示例：

```text
## Patch P001

Source:
- execution_report_v1.json

Problem:
- Agent did not check whether error codes cover auth, validation, not found, and server failure.

Affected rule:
- R003

Patch:
- Move R003 into the top-level mandatory checklist.
- Add required output field `error_code_findings`.

Expected effect:
- Reduce missed API reliability findings in compact skill execution.
```

`compact_skill_v2.md` 必须只做最小必要修改，方便对比 v1/v2。

## 12. 成本优化机制

成本不能只做事后统计。本 slice 先实现一个最小机制：

```text
full_skill.md
-> evidence-guided filtering
-> compact_skill_v1.md
-> execution feedback patch
-> compact_skill_v2.md
```

对比组：

- `full_skill`
- `compact_skill_v1`
- `compact_skill_v2_after_repair`

指标：

- `input_tokens`
- `output_tokens`
- `retry_count`
- `verifier_calls`
- `latency_ms`
- `passed`
- `checklist_pass`

最低目标：

- `compact_skill_v1` 比 `full_skill` 输入 token 更少。
- `compact_skill_v2` 相比 v1 不显著增加 token，但修复至少一个失败类型。
- 如果使用 simulated runner，先保证指标结构真实存在；后续替换为真实 LLM/Harbor 执行数据。

## 13. 与 SPARK 的接口边界

SPARK 当前已经验证：

- WSL2 + Docker + uv + Harbor 可用。
- Harbor smoke task 可执行并产生 reward。
- SPARK pipeline smoke test 可生成 `trajectory.jsonl`、`attempts.json`、`SKILL.md`、`pipeline_summary.json`。
- 离线 PDI probe 可复算已有 artifact 的 PDI signal。

本 vertical slice 暂不追求复现 SPARK 全实验。

需要打通的两个接口：

1. `compact_skill_v1.md` 如何进入 Harbor task instruction / skill context。
2. `trajectory.jsonl` / `attempts.json` 如何转换为 `execution_report.json` 和 `repair_log.md`。

## 14. 两天内交付边界

Day 1：

- 准备 demo 专家材料。
- 生成 `full_skill.md`。
- 生成 `evidence_map.json` 和 `evidence_report.md`。
- 生成 `compact_skill_v1.md`。

Day 2：

- 跑 simulated execution。
- 生成 `execution_report_v1.json`。
- 生成 `repair_log.md`。
- 生成 `compact_skill_v2.md`。
- 生成 `cost_summary.json`。

完成标准：

- `outputs/mvp_vertical_slice/<run_id>/` 下 artifact 齐全。
- 能用一条命令重新生成或至少重新校验 artifact。
- 文档能解释 v1 为什么压缩、v2 为什么修复、成本指标怎么算。
