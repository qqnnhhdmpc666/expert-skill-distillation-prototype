# Evidence Type Consistency Audit

Generated at: `2026-06-12T11:09:10.174126+00:00`

Allowed evidence types: `fresh_run`, `derived_summary`, `scaffold`, `infra_blocked`, `replay`, `external_official_harness`.

## Representative Matrix Rows

| Lane | Claim | Evidence type | Allowed | Evidence |
|---|---|---|---:|---|
| Runtime-general | Installed package registry drives runtime execution | fresh_run | True | C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\installed_skills\registry.json |
| Runtime-general | Installed package variants support marginal utility comparison | fresh_run | True | C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\validation\skill_marginal_utility\installed_package_marginal_utility.json |
| Runtime-general | Small candidate evolution records promotion/rejection evidence | fresh_run | True | C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\skill_evolution_lab\secure_code_review\evolution_summary.json |
| Secure-code-review | Installed secure_code_review covers controlled upload/config/API/auth families | derived_summary | True | C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\reports\MULTI_CAPABILITY_GENERALIZATION_STATUS.md |
| Secure-code-review | Local defensive mini-suite provides bounded representative security evidence | fresh_run | True | C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\external_security_mini_suite\mini_suite_summary.json |
| Software-patch-review | software_patch_review has internal smoke only | fresh_run | True | C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\installed_skills\active_skill_pointers\software_patch_review.json |
| Software-patch-review | SWE-bench official harness readiness is tracked honestly | infra_blocked | True | C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\reports\SWEBENCH_OFFICIAL_HARNESS_INFRA_UNBLOCK_STATUS.md |
| External-security | Official external security benchmarks are not claimed | fresh_run | True | C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\reports\DEFENSIVE_SECURITY_MINI_SUITE_STATUS.md |

## Main Report Scan

| Report | Exists | Allowed mentions | Legacy/disallowed mentions |
|---|---:|---|---|
| C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\reports\REPRESENTATIVE_VALIDATION_MATRIX.md | True | derived_summary, fresh_run, infra_blocked, replay, scaffold | none |
| C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\reports\FRAMEWORK_MATURITY_EVIDENCE_LEDGER.md | True | derived_summary, fresh_run, infra_blocked | none |
| C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\reports\DEFENSIVE_SECURITY_MINI_SUITE_STATUS.md | True | none | none |
| C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\reports\SMALL_CANDIDATE_EVOLUTION_STATUS.md | True | none | none |
| C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\reports\SWEBENCH_OFFICIAL_HARNESS_INFRA_UNBLOCK_STATUS.md | True | infra_blocked | none |
| C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\reports\RAPID_ADVANCEMENT_SPRINT_STATUS.md | True | infra_blocked | none |

## Boundary Checks

- `infra_blocked_not_pass`: `True`
- `scaffold_not_fresh_run`: `True`
- `swebench_not_used_for_secure_code_review`: `True`
- `internal_deterministic_not_real_world_validity`: `True`
- `local_mini_suite_not_official_benchmark`: `True`

## Decision

- Overall status: `pass`
