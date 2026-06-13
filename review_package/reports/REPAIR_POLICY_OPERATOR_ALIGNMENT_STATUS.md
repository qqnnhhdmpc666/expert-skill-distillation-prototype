# Repair Policy / Operator Alignment Status

## Result

- Feedback mappings: `14`
- Typed operators: `10`
- Fully aligned: `YES`
- Fallback risk feedback types: `none`

| Feedback Type | Preferred Action | Status | Matched Operators |
|---|---|---|---|
| config_path_missing | add_observation_step | aligned | op_add_observation_step_generic |
| false_positive_risk | reduce_false_positive_risk | aligned | op_reduce_false_positive_generic |
| high_cost_low_gain | reduce_or_select_trace | aligned | op_reduce_select_trace_generic |
| missing_capability | patch_capability | aligned | op_patch_capability_generic |
| output_contract_error | rewrite_output_contract | aligned | op_rewrite_output_contract_generic |
| overbroad_finding | reduce_false_positive_risk | aligned | op_reduce_false_positive_generic |
| ownership_boundary_missing | patch_boundary | aligned | op_patch_boundary_auth |
| pass | no_op | aligned | op_noop_pass |
| regression_observed | reject_and_rollback | aligned | op_reject_and_rollback_generic |
| target_context_missing | add_observation_step | aligned | op_add_observation_step_generic |
| trace_missing | reduce_or_select_trace | aligned | op_reduce_select_trace_generic |
| unsafe_action_risk | add_safety_boundary | aligned | op_add_safety_boundary_generic |
| unsupported_evidence | add_observation_step | aligned | op_add_observation_step_generic |
| weak_evidence | strengthen_evidence_requirement | aligned | op_strengthen_evidence_generic |

## What this means

1. The repair policy and typed operator registry now use one consistent action vocabulary for the currently known feedback types.
2. This reduces the chance of silent fallback behavior when a verifier emits a known feedback type.
3. It does not prove the chosen operator is the best possible repair; it only proves the mapping is explicit and typed.

## Boundary

This is a naming-and-coverage audit. It is not a semantic optimality proof for the repair strategies themselves.

