# Metric Exploration

These are diagnostic metrics for method exploration. They are not final proposed metrics and should not be compared to SPARK-PDI as an equivalent theoretical contribution.

## 1. Failure Attribution Quality

Question:

```text
Did the system identify the correct failure type and affected target?
```

Examples:

- `missing_rule` should point to missing domain rules such as R005/R006.
- `output_format_error` should point to `OUTPUT_CONTRACT`, not to a domain rule.

Current status:

Partially supported. We have two vertical slices, but no broad labeled failure set.

## 2. Patch Sufficiency

Question:

```text
Did the patch resolve the failure it was supposed to resolve?
```

For `missing_rule`, sufficiency means the affected rules are present and the verifier coverage is recovered.

For `output_format_error`, sufficiency means the output contract now explicitly requires valid JSON and required fields such as `severity` and `evidence`.

Current status:

Partially supported in toy cases. Needs more failure types.

## 3. Counterfactual Patch Utility Under Budget

Question:

```text
Under a similar token increase, is the type-correct compiler patch more useful than no patch, random patch, or wrong-type patch?
```

This is stronger than just comparing v1 vs v2 because it tests whether the improvement is plausibly caused by correct failure attribution and patch action.

Current status:

Explored in `counterfactual_patch_utility_001`. It is a toy counterfactual, not a statistical benchmark.

Current interpretation:

```text
partially_supported
```

The experiment supports using counterfactual patch utility as a diagnostic lens, especially for `missing_rule`. For `output_format_error`, it shows why diagnostics must separate `failure_resolved` from full `verifier_passed`.

## 4. Token Increase After Patch

Question:

```text
How much extra invocation context does the patch add?
```

This matters because a patch that simply appends the full skill may pass but may not be deployable.

Current status:

Supported as descriptive statistics. It does not alone show method quality.

## 5. Recovery Per Added Token

Question:

```text
How much verifier coverage or failure recovery is gained for the added token cost?
```

This is useful only when paired with counterfactual patch variants. Alone, it can be misleading because token count and verifier coverage are coarse proxies.

Current status:

Diagnostic only. Do not package this as a final metric.

## Conservative Interpretation

The most important metric direction is not a new acronym. It is a three-part decomposition:

```text
failure attribution quality
-> patch sufficiency
-> counterfactual patch utility under budget
```

This helps explain why a compact skill revision works, rather than merely reporting that it worked.
## 6. Fixed-Budget Tradeoff Diagnostics

Question:

```text
Can the compact decision policy improve failure-critical coverage under the same budget, or does it only improve by making the prompt longer?
```

Current artifact:

```text
outputs/mvp_vertical_slice/fixed_budget_compiler_001
```

Diagnostic fields:

- token budget.
- selected rule IDs.
- dropped rule IDs.
- over-budget status.
- failure-critical recovered.
- missed rules.
- checklist coverage.

Current interpretation:

```text
partially_supported
```

The execution-aware fixed-budget policy recovers R005/R006 without exceeding budget, but misses R003. This is useful evidence for rule replacement under budget, not a proof of optimal selection.

## 7. Rollback Gate Diagnostics

Question:

```text
Should a patch be accepted if it resolves the original failure but creates a regression?
```

Current artifact:

```text
outputs/mvp_vertical_slice/rollback_gate_001
```

Diagnostic fields:

- resolves original failure.
- regression detected.
- lost previously covered rules.
- over budget.
- broke failure-critical rules.
- accepted / rejected / rollback decision.

Current interpretation:

```text
toy validation-gate probe
```

The current slice rejects a patch that resolves R005/R006 but drops R003. This supports the need for validation-gated revision, but not a mature rollback system.

## 8. Semantic Preservation Diagnostics

Question:

```text
Did compressed wording preserve executable review semantics, or did it only preserve rule IDs?
```

Current artifacts:

```text
outputs/mvp_vertical_slice/semantic_preservation_audit_001
outputs/mvp_vertical_slice/compressed_candidate_execution_001
outputs/mvp_vertical_slice/semantic_verifier_001
```

Diagnostic fields:

- rule ID present.
- actionable condition.
- expected finding behavior.
- evidence or trigger phrase.
- not rule-ID-only.
- semantic verifier pass/fail.
- semantic errors.

Current interpretation:

```text
partially_supported
```

Candidate_C appears to be semantic compression in this toy slice and passes mock plus RightCode GPT execution under a lightweight semantic verifier. This is still not a deep semantic guarantee.

## 9. Rule-Application Trace Diagnostics

Question:

```text
Did the agent expose how each rule was applied to the task input?
```

Current artifact:

```text
outputs/mvp_vertical_slice/skill_to_agent_loop_001
```

Diagnostic fields:

- `rule_applications` exists.
- each finding has a supporting rule application.
- `trigger_condition_found` is non-empty and case-related.
- `evidence_span` is non-empty and case-related.
- `finding_id` links trace and finding.
- rule-id shortcut fails stricter trace verification.

Current interpretation:

```text
partially_supported
```

The trace verifier separates protocolized compressed skill from plain compressed or rule-id shortcut outputs in this toy slice. This is a diagnostic for skill invocation quality, not a final correctness metric.

## 10. Traceable Compilation Integration Diagnostics

Question:

```text
Can compact skill compilation produce not only rules, but also an invocation protocol and trace verifier contract that survive validation?
```

Current artifact:

```text
outputs/mvp_vertical_slice/traceable_compiler_integration_001
```

Diagnostic fields:

- skill token cost.
- protocol token cost.
- total token cost.
- simple verifier result.
- semantic verifier result.
- trace verifier result.
- regression detected.
- accepted by validation gate.
- generated findings.
- generated rule applications.

Current interpretation:

```text
partially_supported_with_protocol_overhead
```

The protocolized variant passes trace verification and blocks shallow rule-id-only behavior, but its protocol overhead currently pushes the total prompt above the fixed token budget. The validation gate correctly rejects that candidate under the current constraint.

This should be read as a diagnostic result:

- Traceability improves verifier contract strength.
- Traceability has a real deployment cost.
- A mature compact compiler must optimize both rule wording and protocol wording.
- Passing trace verification is not sufficient if the compiled artifact exceeds budget.

## 11. Real Effect Evaluation Fields

Question:

```text
Does the deployed expert skill improve controlled task behavior?
```

Current artifact:

```text
outputs/mvp_vertical_slice/real_effect_eval_001
```

Evaluation fields:

- checklist coverage.
- critical missed rules.
- false-positive rules.
- pass@1.
- input tokens.
- output tokens.
- trace tokens.
- total tokens.
- regression detected.
- failure recurrence.

Current interpretation:

```text
partially_supported
```

The 4-case controlled holdout suggests patched compact skills improve coverage over compact_v1 while avoiding critical misses. This remains a small controlled family, not a benchmark.

## 12. Selective Trace Diagnostics

Question:

```text
Where should traceability cost be spent under a fixed budget?
```

Current artifact:

```text
outputs/mvp_vertical_slice/selective_trace_compiler_001
outputs/mvp_vertical_slice/risk_trace_policy_baseline_001
```

Diagnostic fields:

- traced rule IDs.
- untraced rule IDs.
- skill tokens.
- protocol tokens.
- output trace tokens.
- over budget.
- partial trace verifier pass.
- shortcut blocked.
- trace-required rules missing trace.
- semantic-only rules weak.
- validation gate decision.

Current interpretation:

```text
partially_supported
```

Selective trace keeps traceability for failure-critical rules while reducing protocol overhead compared with full trace in this toy slice. This is a diagnostic for risk-budgeted deployment, not a final tracing metric.

## 13. Risk Trace Policy Baseline Diagnostics

Question:

```text
Is selective trace doing more than randomly choosing a small set of rules to trace?
```

Diagnostic fields:

- traced rule IDs.
- random seed.
- sampled rule IDs.
- whether random trace hit failure-critical rules.
- failure-critical trace coverage.
- trace tokens.
- total tokens.
- over budget.
- shortcut blocked.
- semantic verifier pass.
- partial trace verifier pass.
- gate decision.

Current artifact:

```text
outputs/mvp_vertical_slice/risk_trace_policy_baseline_001
outputs/mvp_vertical_slice/risk_trace_policy_robustness_001
```

Current observation:

```text
random_selective_trace:
  traced R002/R003
  total tokens 183 / 237
  failure-critical trace coverage 0.00
  shortcut_blocked true
  gate accept

risk_based_selective_trace:
  traced R005/R006
  total tokens 183 / 237
  failure-critical trace coverage 1.00
  shortcut_blocked true
  gate accept
```

Current interpretation:

```text
partially_supported
```

Risk signals help allocate the same trace budget to failure-critical rules in this toy slice. This remains a diagnostic metric, not a final policy metric or statistical claim.

## 14. Risk Trace Robustness Diagnostics

Question:

```text
Does the risk-trace result depend on one random seed?
```

Diagnostic fields:

- all size=2 trace combinations.
- failure-critical trace coverage per combination.
- trace tokens.
- total tokens.
- shortcut blocked.
- partial trace verifier pass.
- gate decision.
- risk score sum.

Current artifact:

```text
outputs/mvp_vertical_slice/risk_trace_policy_robustness_001
```

Current observation:

```text
total combinations: 15
full failure-critical coverage: 1
partial failure-critical coverage: 8
zero failure-critical coverage: 6
risk-based selected R005/R006, the only full-coverage size=2 combination
```

Current interpretation:

```text
partially_supported
```

This strengthens the diagnostic relative to a single random seed, but it is still a toy rule-pool enumeration rather than statistical validation.

## 15. Direct Summary Miss Diagnostics

Question:

```text
If direct summary is strong, what exactly does it miss?
```

Current artifact:

```text
outputs/mvp_vertical_slice/direct_summary_miss_analysis_001
```

Current observation:

```text
failed case: case004_validation_sensitive_idempotency
missed rule: R006 idempotency
direct summary available rules: R001-R005
patched compact recovers R006 and passes
```

Current interpretation:

```text
partially_supported
```

The miss analysis supports the narrow residual-failure story: direct summary covers salient rules but can omit medium-priority deployment-critical rules such as idempotency.

## 16. Adversarial Trace Verifier Diagnostics

Question:

```text
Does the trace verifier reject obvious fake or weak evidence?
```

Current artifact:

```text
outputs/mvp_vertical_slice/adversarial_trace_verifier_001
```

Diagnostic fields:

- adversarial case name.
- expected reject reason.
- verifier decision.
- trace errors.
- rejected as expected.
- valid control pass.

Current observation:

```text
valid control: pass
fake_evidence_span: reject
generic_trigger: reject
mismatched_finding_id: reject
rule_id_only_trace: reject
```

Current interpretation:

```text
partially_supported
```

The trace verifier now has basic adversarial sanity checks. This is still a lightweight verifier, not a deep semantic judge.

## 17. Revision Decision Matrix Diagnostics

Question:

```text
Does the prototype make different decisions for different feedback/risk types, or only check token budget?
```

Current artifact:

```text
outputs/mvp_vertical_slice/revision_decision_matrix_001
```

Diagnostic fields:

- feedback or risk type.
- naive action.
- constrained decision.
- primary action.
- counterfactual.
- supporting artifacts.
- claim strength.
- limitation.

Current observation:

```text
missing_rule -> patch_rule
output_format_error -> rewrite_output_contract
regression_observed -> reject_and_rollback
semantic_compressed -> semantic_preservation_audit
rule_id_shortcut -> add trace contract
fake_trace_evidence -> strengthen trace verifier
trace_budget_pressure -> risk_based_selective_trace
```

Current interpretation:

```text
partially_supported
```

This diagnostic supports the reframing from budget checking to constrained post-execution revision, while preserving the boundary that this is not a mature algorithm.

## 18. Posterior Revision Signal Diagnostics

Question:

```text
Does post-execution evidence add a useful revision signal beyond prior skill generation?
```

Current artifact:

```text
outputs/mvp_vertical_slice/posterior_revision_signal_audit_001
```

Diagnostic axes:

- posterior recovery;
- attribution specificity;
- revision safety;
- posterior trace allocation.

Current observation:

```text
posterior_recovery_gain_over_compact_v1: 0.4166
posterior_recovery_gain_over_direct_summary: 0.0833
missing_rule_type_specificity_margin: 1
output_format_type_specificity_margin: 1
risk_trace_unique_full_coverage_pair: 1 / 15
rollback_gate_decision_observed: reject_and_rollback
```

Current interpretation:

```text
partially_supported
```

This is the closest current diagnostic to a method-level abstraction. It should not be described as a final metric. Its value is that it asks whether posterior execution/verifier evidence changes revision decisions in ways that prior skill generation alone did not.
