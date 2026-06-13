# Skill Lifecycle Evidence Status

- Updated: `2026-06-09T07:38:50.242983+00:00`
- Generalization cases with standardized distillation + trajectory bundles: `5`
- Live repair loops with standardized trajectory bundles: `4`
- Average v1->v2 gain (controlled verifier coverage): `0.1333`

## What was added

- A standardized distillation bundle for each controlled task case.
- A standardized trajectory bundle for each controlled generalization run.
- A standardized trajectory bundle for Harbor/local live repair loops where A1, revision, and A2 already exist.
- A verifier-scored no-skill / skill-v1 / skill-v2 net-effect matrix.

## Why this matters

- The mainline is now easier to audit as `expert material -> normalized capabilities -> skill_v1 -> execution -> verifier feedback -> repair -> skill_v2`.
- Provenance is no longer only implied by scattered files; it is exposed as capability-level provenance rows with explicit source spans and repair attribution.
- Trajectory evidence is no longer only a directory tree; it is normalized into bundle files that make A1/A2 comparison easier to inspect and export.

## Controlled boundaries

- Provenance extraction is still controlled keyword projection over curated task-case expert notes, not broad open-world expert-material induction.
- Offline trajectory bundles are standardized artifact bundles, not full SPARK-style live command/stdout trajectories.
- Harbor/local live bundles are still narrow scenario evidence rather than broad multi-task autonomous proof.

## Generalization bundle index

| Case | Family | Feedback | Repair | A2 | Bundle |
|---|---|---|---|---|---|
| api_review_001 | api_or_code_review | output_contract_error | rewrite_output_contract | True | `outputs/skill_lifecycle_evidence/generalization/api_review_001` |
| auth_access_control_001 | auth_access_control | ownership_boundary_missing | patch_boundary | True | `outputs/skill_lifecycle_evidence/generalization/auth_access_control_001` |
| config_security_001 | config_security | false_positive_risk | reduce_false_positive_risk | True | `outputs/skill_lifecycle_evidence/generalization/config_security_001` |
| data_quality_review_001 | data_quality_review | target_context_missing | add_observation_step | True | `outputs/skill_lifecycle_evidence/generalization/data_quality_review_001` |
| upload_security_001 | upload_security | missing_capability | patch_capability | True | `outputs/skill_lifecycle_evidence/generalization/upload_security_001` |

## Live loop bundle index

| Run | Kind | Feedback | Repair | A2 | Bundle |
|---|---|---|---|---|---|
| harbor_llm_repair_loop_upload_001 | harbor_llm_repair_loop | missing_capability | patch_capability | True | `outputs/skill_lifecycle_evidence/live_loops/harbor_llm_repair_loop_upload_001/trajectory_bundle` |
| harbor_llm_repair_loop_config_001 | harbor_llm_repair_loop | output_contract_error | rewrite_output_contract | True | `outputs/skill_lifecycle_evidence/live_loops/harbor_llm_repair_loop_config_001/trajectory_bundle` |
| live_llm_repair_loop_upload_001 | local_live_llm_repair_loop | missing_capability | patch_capability | True | `outputs/skill_lifecycle_evidence/live_loops/live_llm_repair_loop_upload_001/trajectory_bundle` |
| live_llm_repair_loop_data_quality_001 | local_live_llm_repair_loop | output_contract_error | rewrite_output_contract | True | `outputs/skill_lifecycle_evidence/live_loops/live_llm_repair_loop_data_quality_001/trajectory_bundle` |

## Net-effect reading

- All controlled A2 reruns pass: `True`
- Average no-skill -> v2 gain: `1.0`
- Matrix artifact: `outputs/validation/skill_net_effect_matrix.json`
