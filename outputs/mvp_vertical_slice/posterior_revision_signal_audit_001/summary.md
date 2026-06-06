# Posterior Revision Signal Audit 001

## Purpose

This slice asks whether post-execution evidence is doing nontrivial method work beyond prior skill generation.
It does not introduce a new task family or a new model. It audits existing artifacts through a method-level lens.

## Candidate Method Statement

Posterior skill revision treats a generated skill as a deployable hypothesis, not a final artifact. The method question is whether environment/verifier feedback can diagnose residual failure, choose a type-specific revision action, validate against regressions, and allocate trace evidence to high-risk rules under budget.

## Diagnostic Axes

| Axis | Diagnostic Question | Current Evidence | Status |
|---|---|---|---|
| posterior recovery | Does execution feedback recover residual failures that prior skill generation missed? | compact_v1 coverage 0.5834 -> patched_compact 1.0; direct summary 0.9167 -> patched 1.0. | partially_supported |
| attribution specificity | Does the failure type matter, or can any patch work? | missing_rule compiler_patch resolved=True while no/random/wrong-type patches did not; output_format wrong_missing_rule resolved=False vs output_contract_patch resolved=True. | partially_supported |
| revision safety | Can a patch that fixes the observed failure still be unsafe? | rollback gate decision: reject_and_rollback. | supported_in_toy_slice |
| posterior trace allocation | Can failure-critical evidence guide trace budget better than arbitrary allocation? | only 1/15 size-2 trace allocations cover both failure-critical rules; risk policy selects that pair. | partially_supported |

## Key Quantitative Signals

- direct_summary_avg_coverage: 0.9167
- compact_v1_avg_coverage: 0.5834
- patched_compact_avg_coverage: 1.0
- patched_selective_trace_avg_coverage: 1.0
- full_skill_avg_tokens: 1429.75
- direct_summary_avg_tokens: 263.0
- patched_compact_avg_tokens: 438.75
- patched_selective_trace_avg_tokens: 335.0
- posterior_recovery_gain_over_compact_v1: 0.4166
- posterior_recovery_gain_over_direct_summary: 0.0833
- selective_trace_token_saving_vs_full_skill: 0.7657
- missing_rule_type_specificity_margin: 1
- output_format_type_specificity_margin: 1
- risk_trace_unique_full_coverage_pair: {'full_coverage_combinations': 1, 'total_combinations': 15, 'coverage_rate': 0.0667}
- rollback_gate_decision_observed: reject_and_rollback
- revision_matrix_rows: 7

## What This Supports

Existing artifacts support a method-level hypothesis: post-execution evidence can function as a revision signal that changes what gets patched, gated, and traced, rather than merely increasing a token budget. The strongest current evidence is attribution-specific patch utility plus rollback and selective trace diagnostics.

## Boundary

Controlled API-review family only. This audit reuses toy-slice artifacts and does not establish a broad method like PDI. It identifies a promising method gap to test next: posterior revision utility across more task families and failure modes.

## Falsification Pressure

- If larger holdouts show direct summary has no residual misses, posterior recovery is less central.
- If random or wrong-type patches resolve failures as often as targeted patches, attribution specificity is weak.
- If realistic patches rarely cause regressions, rollback becomes a safeguard rather than a method contribution.
- If risk-based trace does not outperform random allocation beyond this rule pool, trace allocation remains a toy result.
