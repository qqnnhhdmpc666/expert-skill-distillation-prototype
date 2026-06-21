# Benchmark and Verifier Protocol V1

状态：`normative_protocol`

## 1. 证据层级

| Lane | 回答的问题 | 可支持的主张 |
|---|---|---|
| deterministic contract | 工件、证据、版本和结果是否满足明确定义 | plumbing/correctness |
| automated source-grounded evaluation | 编译产物是否受来源支持并保持范围/模态 | compiler fidelity |
| public held-out evaluator | 下游任务是否真实完成 | task effectiveness |
| cross-check tools | 不同实现在哪里一致或分歧 | diagnostic only |

LLM Judge 不得称为人工评价；OSV-Scanner/Trivy 不得称为唯一 gold；内部 deterministic pass 不得称为真实世界安全有效。

## 2. 公开 OSV 领域轨

数据集必须由公开 OSV records 和公开 schema 确定性生成，并发布：

```text
source URLs and capture timestamp
raw record digests
schema digest
generator version and command
case manifest
build/dev/held-out split manifest
deterministic evaluator version
exclusion and unresolved reasons
```

划分在模型/方法选择前冻结。任何方法不得读取 held-out verdict、expected evidence 或另一方法中间工件。

主指标至少包括：pair verdict accuracy、justified unresolved、false-safe count、evidence completeness、scope violation 和 runtime failure。`runtime_failure` 不计作 `unresolved`。

## 3. Compiler 五条件

```text
no_skill
full_material
direct_to_skill_ir
compiler_distilled_skill
human_authored_reference_skill (optional)
```

五者共享 Agent/model、domain primitives、snapshot、权限、任务预算、Runtime compiler 和 evaluator。`direct_to_skill_ir` 直接输出相同 Skill IR schema，不通过 Knowledge IR；人工参考 Skill 不是理论上界。

同时报告：

- effectiveness configuration；
- pre-registered resource-envelope comparison；
- compile/rebuild/runtime/evaluation 成本；
- 随任务复用次数与来源更新次数变化的 amortized cost；
- 无有限 break-even 时明确报告不存在。

## 4. Automated Source-Grounded Compiler Evaluation

固定包含：

1. schema、lineage、provenance、span、digest 和 dependency closure 的确定性检查；
2. 独立固定 LLM Judge 对 entailment、unsupported claim、scope overreach、modality mismatch、missing exception 的盲评；
3. conflict、over-broad scope、missing evidence、stale rule、broken reference 自动扰动；
4. public held-out 上 `direct_to_skill_ir` 与 `compiler_distilled_skill` 的下游比较。

Judge 只看到匿名候选和允许的来源，不看到方法名、promotion 结果和 held-out 分数。Judge 配置在 held-out 前固定。

## 5. Agent/Skill 配对运行

同一任务至少比较 `no_skill` 与目标 Skill 条件。保持 commit、AgentHost、model、环境、知识快照、权限、预算、测试不变。除最终结果外记录：工具调用、检索、无效步骤、token/time、false-safe、scope mismatch 和 harmful/neutral/helpful 分类。

这类轨迹用于归因，不能替代公开 evaluator。

## 6. Harbor parity

公开 task 进入 Harbor 前，先用 oracle 验证原环境，再比较原 harness 与 Harbor adapter：任务输入、镜像/依赖、测试、timeout、exit semantics 和 verifier result。全部一致或差异被预注册接受后，才可标记 `external_official_harness`。

adapter 能启动容器只证明 plumbing。

## 7. 结果状态

```text
pass
partial
fail
blocked
infra_failed
invalid_for_comparison
```

报告必须保留失败行、blocked 原因、原始 evaluator artifact 和 claim boundary。不得通过删除失败、放宽 verifier、补看 held-out 或改变预算获得 pass。

