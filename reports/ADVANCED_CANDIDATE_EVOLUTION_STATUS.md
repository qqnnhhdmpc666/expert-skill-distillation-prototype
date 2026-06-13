# Advanced Candidate Evolution Status

Generated at: `2026-06-12T11:39:16.948268+00:00`

Candidates are generated from failure reports, verifier feedback summaries, evidence summaries, and limitation summaries only. Verifier-only oracle fields are not read.

| Candidate | Source | Case | Decision | Score delta | FP delta | Scope violation |
|---|---|---|---|---:|---:|---:|
| advanced_config_holdout_realization_001 | holdout_evidence_summary | holdout_config_prod_secret_001 | not_promoted | 0.0 | 0 | False |
| advanced_non_oracle_discrepancy_002 | non_oracle_discrepancy_summary | holdout_api_overbroad_schema_001 | not_promoted | 0.0 | 0 | False |
| advanced_router_boundary_003 | activation_ablation_failure | holdout_clean_tax_math_001 | not_promoted | 0.0 | 0 | False |
| advanced_dependency_scope_expansion_004 | mini_suite_limitation_summary | holdout_dependency_no_advisory_001 | not_promoted | -0.2 | 1 | True |
| advanced_false_positive_stress_005 | ablation_negative_control_stress | holdout_clean_tax_math_001 | not_promoted | -0.2 | 3 | True |

## Summary

- Rejected edits: `5`
- Promotion proposals: `0`
