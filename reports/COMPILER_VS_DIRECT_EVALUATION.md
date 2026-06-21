# Compiler vs Direct-to-Skill-IR Evaluation

Date: 2026-06-21

```text
compiler_superiority = evaluated_on_dev_only
comparison_result = inconclusive
```

Fresh command:

```powershell
eskill --state-dir .tmp/goal-evidence-state evaluate-compiler `
  --data-dir data/v1_walking_skeleton
```

Four conditions ran over the same six predeclared dev cases and frozen OSV snapshot:

| Condition | Correctness | False-safe | Evidence completeness | Build ms |
|---|---:|---:|---:|---:|
| no_skill | 1.00 | 0.00 | 1.00 | n/a |
| full_material | 1.00 | 0.00 | 1.00 | n/a |
| direct_to_skill_ir | 1.00 | 0.00 | 1.00 | 24.465 |
| compiler_distilled_skill | 1.00 | 0.00 | 1.00 | 71.548 |

Both automated Skill IR paths had zero deterministic unsupported-claim, scope-overreach, and missing-exception findings. Token/API cost is null because both builders and the evaluator are deterministic.

Artifact: `sha256:759310cc7519b0305b67bd28dd553ad79de73df2300d3c56ab9e87d2f7b1b379`.

## Interpretation

The shared `ReferenceDecisionBackend` does not consume condition-specific Agent artifacts. Therefore the task-level tie proves evaluator plumbing and source-safe dev instrumentation, not compiler superiority. This V1 result validates staged architecture only; it does not prove open-world extraction or a benefit under a mature AgentHost.
