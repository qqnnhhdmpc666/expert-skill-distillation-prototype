# Distillation Feedback Loop v1 Status

- distillation_feedback_loop_v1: `pass`
- defect_count: `4`
- promoted_count: `4`
- failure_attribution_types: `["evidence_binding_gap", "knowledge_gap", "skill_missing_rule", "skill_overgeneralized_rule"]`
- revision_targets: `["evidence_binding_plan", "knowledge_access_binding", "knowledge_projection", "runtime_policy", "skill_rule"]`

| defect_id | baseline_pass | revised_pass | attribution | targets | promotion |
|---|---:|---:|---|---|---|
| `D1_skill_missing_rule` | `0` | `4` | `["evidence_binding_gap", "skill_missing_rule"]` | `["skill_rule", "evidence_binding_plan"]` | `promote` |
| `D2_skill_overgeneralized_rule` | `1` | `4` | `["skill_overgeneralized_rule"]` | `["skill_rule", "runtime_policy"]` | `promote` |
| `D3_knowledge_gap` | `0` | `4` | `["knowledge_gap"]` | `["knowledge_projection", "knowledge_access_binding"]` | `promote` |
| `D4_evidence_binding_gap` | `1` | `4` | `["evidence_binding_gap"]` | `["evidence_binding_plan"]` | `promote` |

## Claim Boundary

- compiler_superiority: `not_evaluated`
- mature_agenthost_effectiveness: `not_evaluated`
- general_vulnerability_discovery: `not_claimed`
- official_public_benchmark_performance: `not_claimed`
- production_readiness: `not_claimed`
