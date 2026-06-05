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
