# Naive Revision Ablation 001

## Purpose

Pressure-test whether the proposed expert-skill deployment revision story is more than generic feedback repair.
This is a diagnostic ablation over existing artifacts, not a benchmark.

## Strategy Comparison

| Strategy | Missing Rule | Output Format | Regression Safety | Trace Budget | Main Cost / Failure | Interpretation |
|---|---|---|---|---|---|---|
| no_revision | resolved=False | resolved=False | not_applicable | not_applicable | keeps observed deployment failures | useful as lower bound only |
| always_append_domain_rules | resolved=True | resolved=False | not_checked | not_checked | fixes missing rules but does not fix output-contract failures | too generic; failure type matters |
| always_rewrite_output_contract | resolved=False | resolved=True | not_checked | not_checked | fixes format failure but does not recover missing domain rules | too generic; failure type matters |
| always_regenerate_full_skill | resolved=True | resolved=True | not_targeted | not_targeted | works as upper bound but avg tokens=1429.75 | strong but expensive and weakly diagnostic |
| accept_if_current_failure_fixed | can_resolve_current_failure | not_targeted | unsafe; gate observed reject_and_rollback | not_checked | can promote a patch that regresses previously covered rules | current-failure success is insufficient for deployment promotion |
| always_full_trace | not_a_patch_strategy | not_a_patch_strategy | traceable | over_budget=True total=300/237 | blocks shortcut but exceeds the trace budget | useful upper bound; not deployable under current budget |
| type_specific_operator_plus_gate_and_selective_trace | resolved=True | resolved=True | safe_gate=True | selective_trace over_budget=False shortcut_blocked=True total=183/237 | avg tokens with selective trace=335.0; still toy and rule-family-specific | currently best-supported narrow mechanism combination |

## Diagnostic Scores

- no_revision: resolved_axes=0/4, hard_failures=2, notes=useful as lower bound only
- always_append_domain_rules: resolved_axes=1/4, hard_failures=1, notes=too generic; failure type matters
- always_rewrite_output_contract: resolved_axes=1/4, hard_failures=1, notes=too generic; failure type matters
- always_regenerate_full_skill: resolved_axes=2/4, hard_failures=0, notes=strong but expensive and weakly diagnostic
- accept_if_current_failure_fixed: resolved_axes=1/4, hard_failures=1, notes=current-failure success is insufficient for deployment promotion
- always_full_trace: resolved_axes=1/4, hard_failures=1, notes=useful upper bound; not deployable under current budget
- type_specific_operator_plus_gate_and_selective_trace: resolved_axes=4/4, hard_failures=0, notes=currently best-supported narrow mechanism combination

## Conclusion

- Status: partially_supported
- Finding: Existing toy artifacts support the claim that generic revision strategies are not enough to explain all observed constraints: always-append and always-contract each fail one failure type, current-failure-only acceptance can regress, and full trace is over budget. The best current narrow mechanism is type-specific revision plus deployment promotion gate plus selective trace.
- Boundary: This reuses existing controlled artifacts and is not a statistically valid ablation. Full regeneration remains a strong upper bound, so future work must show the targeted strategy transfers beyond this rule family.
