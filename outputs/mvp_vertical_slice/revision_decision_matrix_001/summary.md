# Revision Decision Matrix 001

## Purpose

Show that the current prototype is not merely checking token budget. It makes different constrained revision decisions for different post-execution feedback/risk types.

| Feedback / Risk | Naive Action | Constrained Decision | Key Result | Claim Strength |
|---|---|---|---|---|
| missing_rule | append_more_rules | patch affected missing rules; compare against no/random/wrong-type patches | compiler_patch resolves missing_rule while no/random/wrong-type variants do not in the toy slice. | partially_supported |
| output_format_error | append_domain_rules | rewrite output contract instead of patching domain rules | format failure maps to OUTPUT_CONTRACT rather than R005/R006 domain-rule patch. | partially_supported |
| regression_observed | accept_if_original_failure_fixed | reject and rollback if patch loses previously covered rules | gate rejects a patch that resolves original failure but regresses holdout coverage. | supported_in_toy_slice |
| semantic_compressed | trust_shorter_rule_text | audit trigger/action/output semantics and execute compressed candidate | candidate_C is judged preserved in the toy audit and passes mock/GPT execution checks. | partially_supported |
| rule_id_shortcut | trust_rule_id_coverage | require rule_application trace evidence | protocolized compressed skill passes trace verifier; shortcut/plain variants fail strict trace. | partially_supported |
| fake_trace_evidence | trust_trace_fields | reject fake span, generic trigger, mismatched finding_id, and rule-id-only trace | valid control passes; four obvious fake/weak trace cases are rejected. | partially_supported |
| trace_budget_pressure | trace_all_or_trace_none | allocate trace to failure-critical / newly patched rules | risk-based trace selects R005/R006 at 183/237 tokens; full trace is 300/237 and over budget. | partially_supported |

## Conservative Conclusion

- Status: partially_supported
- Finding: Existing toy slices support a nontrivial decision-chain framing: different feedback types trigger different repair, gate, trace, or rollback decisions instead of simple budget-based append/reject.
- Boundary: Mechanism matrix over existing toy artifacts only. This is not a mature revision algorithm or benchmark.
