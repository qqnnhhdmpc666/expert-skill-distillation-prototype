# Real Expert Material Pilot Status

- pilot_protocol_status: `pass`
- baseline_comparison_status: `pass`
- four_baseline_comparison: `pass`
- osv_lane_status: `pass`
- repo_level_lane_status: `partial`
- anti_leakage_status: `pass`
- claim_boundary_status: `pass`
- no_skill_reference_backend_contains_default_triage_logic: `True`
- repo_level_public_excerpt_count: `1`
- full_public_repo_level_evaluation: `not_claimed`

## Lane Summary

| lane | status | cases/tasks | note |
|---|---|---:|---|
| `osv_advisory_version` | `pass` | `7` | frozen public OSV held-out cases |
| `repo_level_dependency_use` | `partial` | `1` | public repo excerpt lane is partial unless two clean excerpts are frozen |

## Baseline Validity

| baseline | status | invalid_reason |
|---|---|---|
| `no_skill` | `valid` | `None` |
| `full_material` | `valid` | `None` |
| `direct_to_skill_ir` | `valid` | `None` |
| `distillation_loop_v1` | `valid` | `None` |

## Interpretation Caveat

`no_skill` does not read expert material, Skill IR, ReleaseBundle, BundleRuntimePolicy, distillation outputs, or revision artifacts. However, the deterministic reference backend contains default dependency/advisory triage logic, so `no_skill` should be interpreted as reference-backend capability, not as an uninformed agent.

## Claim Boundary

- compiler_superiority: `not_evaluated`
- mature_agenthost_effectiveness: `not_evaluated`
- general_vulnerability_discovery: `not_claimed`
- official_public_benchmark_performance: `not_claimed`
- production_readiness: `not_claimed`
