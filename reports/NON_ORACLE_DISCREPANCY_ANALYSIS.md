# Non-Oracle Discrepancy Analysis

Generated at: `2026-06-12T12:43:19.650719+00:00`

## Scope

This analysis separates backend execution from behavior effectiveness. It reads pre-repair and post-repair non-oracle summaries, verifier reports, and agent outputs only. It does not read verifier-only expected findings or evidence spans, does not relax the verifier, and does not expand secure_code_review scope.

## Summary

- Pre-repair evidence: `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\non_oracle_validation_pre_p0_l_repair\non_oracle_validation_summary.json`
- Post-repair evidence: `C:\Users\31552\Documents\New project\expert-skill-distillation-prototype-main\outputs\non_oracle_validation\non_oracle_validation_summary.json`
- Cases analyzed: `6`
- Post-repair verifier pass count: `6`
- Post-repair non-oracle behavior: `pass`
- Repair attempted: task-conditioned active capability filtering, exact-line evidence span normalization, and out-of-scope false-positive suppression.

## Case Analysis

| Case | Task family | Pre result | Pre reason | Pre FP | Failure category | Post result | Post reason | Post FP | Post discrepancy |
|---|---|---|---|---:|---|---|---|---:|---|
| holdout_api_overbroad_schema_001 | api_or_code_review | fail | unsupported_evidence | 0 | evidence_span_formatting_issue | pass | pass | 0 | none |
| holdout_auth_project_ownership_001 | auth_access_control | fail | false_positive_risk | 1 | capability_activation_or_false_positive_issue | pass | pass | 0 | none |
| holdout_clean_tax_math_001 | clean_business_logic_review | fail | false_positive_risk | 1 | capability_activation_or_false_positive_issue | pass | pass | 0 | none |
| holdout_config_prod_secret_001 | config_security | fail | unsupported_evidence | 1 | capability_activation_or_false_positive_issue, evidence_span_formatting_issue | pass | pass | 0 | none |
| holdout_dependency_no_advisory_001 | dependency_version_risk | fail | false_positive_risk | 1 | capability_activation_or_false_positive_issue | pass | pass | 0 | none |
| holdout_upload_double_extension_001 | upload_security | fail | false_positive_risk | 2 | capability_activation_or_false_positive_issue | pass | pass | 0 | none |

## Boundary

- Verifier was not relaxed.
- No verifier-only oracle expected finding, evidence span, or clean/negative label was used for repair generation.
- Dependency/version-risk remains unsupported by secure_code_review core capability.
- If a future non-oracle row fails, it remains discrepancy evidence rather than being deleted.
