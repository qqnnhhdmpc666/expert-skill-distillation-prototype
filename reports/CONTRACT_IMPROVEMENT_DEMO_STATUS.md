# Contract Improvement Demo Status

Generated at: `2026-06-12T16:25:30.191756+00:00`

- Candidate generation: `pass`
- Evolution safety gate: `pass`
- Evolution improvement: `not_yet_demonstrated`
- Evolution maturity: `safety_gate_pass`
- Promotion decision: `not_promoted`
- Score delta: `-0.0055`

## Validation Rows

| Case | Variant | Status | Verifier | FP | Unsupported evidence | Scope violation | Score |
|---|---|---|---|---:|---:|---:|---:|
| independent_upload_clean_001 | active | completed | pass:pass | 0 | 0 | False | 1.0 |
| independent_upload_clean_001 | candidate | completed | pass:pass | 0 | 0 | False | 1.0 |
| independent_config_prod_audit_001 | active | completed | fail:missing_capability | 0 | 0 | False | 0.7 |
| independent_config_prod_audit_001 | candidate | completed | fail:missing_capability | 0 | 0 | False | 0.7 |
| independent_auth_invoice_scope_001 | active | completed | fail:missing_capability | 0 | 0 | False | 0.7333 |
| independent_auth_invoice_scope_001 | candidate | completed | pass:pass | 0 | 0 | False | 1.0 |
| independent_api_schema_001 | active | completed | fail:missing_capability | 0 | 0 | False | 0.6 |
| independent_api_schema_001 | candidate | completed | fail:missing_capability | 0 | 0 | False | 0.7 |
| independent_dependency_unsupported_001 | active | completed | pass:pass | 0 | 0 | False | 1.0 |
| independent_dependency_unsupported_001 | candidate | completed | pass:pass | 0 | 0 | False | 1.0 |
| independent_ambiguous_debug_001 | active | completed | pass:pass | 0 | 0 | False | 1.0 |
| independent_ambiguous_debug_001 | candidate | completed | fail:false_positive_risk | 1 | 0 | False | 0.6 |

## Boundary

- Candidate was generated from failure reports, verifier feedback, evidence summaries, and normalization traces.
- Verifier-only oracle fields were not read.
- The candidate was not auto-installed.
- A staged promotion proposal is not a production deployment claim.
