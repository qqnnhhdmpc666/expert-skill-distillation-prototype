# Second Domain Config Security 001

## Purpose

Minimal second-domain probe for typed posterior revision over deployable expert-skill packages.
This is not a benchmark and not a general proof.

## Domain

Configuration security review: hardcoded secrets, TLS, least privilege, debug mode, resource limits, and audit retention.

## Strategy Results

| Strategy | Avg Coverage | Pass@1 | Gate | Tokens | Missing | Contract Errors | Interpretation |
|---|---:|---:|---|---:|---:|---:|---|
| direct_summary_skill | 0.82 | 2 / 4 | reject_unresolved_failure | 150 / 260 | 2 | 0 | strong prior baseline but misses residual C006 audit-retention cases |
| compact_v1_no_revision | 0.82 | 2 / 4 | reject_unresolved_failure | 150 / 260 | 2 | 0 | shows residual deployment failure before posterior revision |
| always_append_domain_rules | 1.00 | 1 / 4 | reject_unresolved_failure | 152 / 260 | 0 | 27 | recovers domain missing rule but fails output-contract quality |
| always_rewrite_output_contract | 0.82 | 2 / 4 | reject_unresolved_failure | 152 / 260 | 2 | 0 | contract is valid but residual C006 remains missing |
| always_regenerate_full_skill | 1.00 | 4 / 4 | reject_over_budget | 289 / 260 | 0 | 0 | strong high-cost upper bound |
| accept_if_current_failure_fixed | 0.95 | 3 / 4 | reject_regression | 152 / 260 | 1 | 0 | unsafe because it drops previously covered C003 |
| always_full_trace | 1.00 | 4 / 4 | reject_over_budget | 629 / 260 | 0 | 0 | traceable but over budget |
| type_specific_operator_plus_gate_and_selective_trace | 1.00 | 4 / 4 | accept | 166 / 260 | 0 | 0 | best-supported typed revision combination in this second-domain probe |

## Key Findings

- direct_summary_skill remains a strong prior baseline: coverage 0.825 but it misses residual C006 audit-retention cases.
- always_append_domain_rules reaches coverage 1.0 but has 27 output-contract errors.
- always_rewrite_output_contract has valid output contract but leaves 2 missing rule instances.
- accept_if_current_failure_fixed is rejected by gate because regression_detected=True.
- always_full_trace blocks shortcut but is over budget: 629/260.
- always_regenerate_full_skill is a strong upper bound with tokens 289/260.
- type_specific_operator_plus_gate_and_selective_trace passes all 4 cases and is under budget: 166/260.

## Conclusion

- Status: partially_supported
- Finding: The typed posterior revision pattern is not limited to the API-review surface in this minimal probe: a residual domain rule miss, output-contract failure, regression risk, and trace-budget pressure appear in a configuration-security domain.
- Boundary: This is a hand-constructed second-domain probe with deterministic checks. It is not a benchmark, not a cross-domain proof, and not evidence that the strategy beats full regeneration when cost is ignored.
