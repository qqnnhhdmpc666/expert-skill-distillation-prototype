# Falsification And Next Evidence

Date: 2026-06-06

## Purpose

This document states how the current core claim could fail, and what evidence should be collected next.

Core claim:

```text
Skill deployment needs risk-budgeted verification, not just better summarization.
```

This document is deliberately conservative. It is meant to prevent the prototype from turning toy-slice evidence into broad claims.

## Current Claim Status

Current status:

```text
partially_supported
```

Current supporting evidence:

- Direct summary is strong but misses one residual rule: `R006`.
- Patched compact recovers that rule in the controlled holdout.
- Risk-based selective trace selects `R005/R006`, the failure-critical rules.
- All size=2 trace combinations show only `R005/R006` covers both failure-critical rules under the same trace size.
- Validation gate rejects known regression and over-budget candidates in toy slices.
- Adversarial trace verifier sanity check rejects obvious fake/weak evidence cases after adding an `evidence_span` relevance check.
- Revision decision matrix shows different feedback/risk types currently map to different constrained actions rather than one budget check.
- Posterior revision signal audit connects recovery gain, attribution specificity, rollback, and trace allocation into a method-level diagnostic.
- Naive revision ablation pressure-tests always-append, always-contract, always-regenerate, accept-if-fixed, and always-full-trace baselines.

## Falsification Conditions

### F1: Direct Summary Has No Residual Misses

If direct summary reaches stable `1.00` coverage on a larger controlled holdout, then the claim that structured deployment recovers residual misses becomes weaker.

Impact:

```text
The system should shift from coverage recovery to patchability, traceability, auditability, and versioned deployment control.
```

Next evidence:

- Expand holdout to 6-8 cases only after current demo is stable.
- Include long-tail rules and false-positive controls.
- Compare direct summary, compact, patched compact, and selective trace.

### F2: Random Trace Performs Like Risk-Based Trace

If random selective trace matches risk-based trace across many settings, then the risk-budgeted trace policy claim becomes weak.

Impact:

```text
Risk signals are insufficient and the trace policy needs redesign.
```

Next evidence:

- Enumerate small rule pools when feasible.
- Use multiple seeds when enumeration is infeasible.
- Report random hit rate for failure-critical rules.

### F3: Trace Verifier Cannot Detect Fake Evidence

If the trace verifier accepts shallow or fake evidence spans, then the traceability claim should be downgraded.

Impact:

```text
Trace protocol is only a formatting constraint, not reliable evidence of rule application.
```

Next evidence:

- Add adversarial trace examples.
- Check whether evidence spans actually appear in the case text.
- Add stronger verifier contracts before making larger claims.

Current progress:

```text
outputs/mvp_vertical_slice/adversarial_trace_verifier_001
```

Current observation:

```text
valid control passes
fake_evidence_span rejected
generic_trigger rejected
mismatched_finding_id rejected
rule_id_only_trace rejected
```

Boundary:

```text
This is a basic adversarial sanity check, not deep semantic verification.
```

### F4: Validation Gate Only Catches Toy Regressions

If the validation gate only catches hand-constructed regressions and misses realistic regressions, then the gate claim remains an engineering check.

Impact:

```text
The gate should be described as a prototype safeguard, not a robust deployment validator.
```

Next evidence:

- Add more regression cases.
- Test patches that fix one rule while degrading another.
- Track accept/reject decisions with explicit rollback evidence.

### F5: Selective Trace Cost Remains Too High

If selective trace remains over budget or expensive in more complex tasks, the deployment feasibility claim must be weakened.

Impact:

```text
Trace remains useful for audit/debug but may not be feasible for compact deployment.
```

Next evidence:

- Compress protocol wording.
- Trace only failure-critical or newly patched rules.
- Measure overhead across more task cases.

### F6: Failure-Critical Labels Are Too Retrospective

If failure-critical labels only work after manually inspecting outcomes, the method risks being post-hoc.

Impact:

```text
Risk-budgeting becomes explanatory rather than predictive.
```

Next evidence:

- Separate pre-execution risk signals from post-execution failure signals.
- Track which rules were high-risk before the verifier failure.
- Evaluate whether pre-execution risk predicts later failures.

### F7: Revision Matrix Is Only Documentation

If future slices show that all failure types can be handled equally well by the same append-more-rules strategy, then the constrained revision framing becomes weak.

Impact:

```text
The revision decision matrix becomes a taxonomy document rather than evidence for a method.
```

Next evidence:

- Add more failure types where wrong repair actions fail.
- Add counterfactuals for patch-rule vs output-contract vs rollback actions.
- Track whether each constrained action improves over naive append or blind accept.

### F8: Posterior Revision Adds No Signal Beyond Prior Skill Generation

If direct summary or initial full/compact skill generation already solves the deployment cases without residual failures, then posterior revision is less important as a correctness mechanism.

Impact:

```text
The method should shift toward auditability, version control, and traceability rather than recovery gain.
```

Next evidence:

- Compare posterior-revised skills against direct summary and full-skill baselines on a larger controlled holdout.
- Separate prior signals from posterior signals.
- Report posterior gain over direct summary, not only over compact_v1.

Current progress:

```text
outputs/mvp_vertical_slice/posterior_revision_signal_audit_001
```

Current observation:

```text
posterior gain over compact_v1: +0.4166
posterior gain over direct_summary: +0.0833
```

Boundary:

```text
This is a small controlled-family diagnostic, not evidence that posterior revision is broadly superior to prior generation.
```

### F9: Naive Revision Strategies Are Sufficient

If always-append, always-regenerate, or always-full-trace strategies solve the same failures with acceptable cost and safety, then typed posterior revision becomes unnecessary.

Impact:

```text
The method claim should be downgraded to engineering organization around known repair strategies.
```

Next evidence:

- Compare simple revision policies against type-specific operators.
- Treat full regeneration as a strong upper bound, not a weak baseline.
- Measure whether generic policies also pass regression, semantic, budget, and trace gates.

Current progress:

```text
outputs/mvp_vertical_slice/naive_revision_ablation_001
```

Current observation:

```text
always_append_domain_rules fixes missing_rule but fails output_format_error
always_rewrite_output_contract fixes output_format_error but fails missing_rule
always_full_trace blocks shortcut but is over budget
always_regenerate_full_skill fixes tested failures but is high-cost and weakly diagnostic
```

Boundary:

```text
This is a diagnostic ablation over existing toy artifacts, not statistical evidence.
```

## Next Evidence Priority

Priority order:

1. `risk_trace_policy_robustness_001`: done. Enumerates all size=2 trace combinations in the current rule pool.
2. `direct_summary_miss_analysis_001`: done. Explains the only direct-summary miss.
3. `adversarial_trace_verifier_001`: done. Checks obvious fake/weak trace evidence.
4. `revision_decision_matrix_001`: done. Consolidates constrained post-execution revision decisions.
5. `posterior_revision_signal_audit_001`: done. Audits whether posterior evidence changes patch/gate/trace decisions beyond prior skill generation.
6. `naive_revision_ablation_001`: done. Pressure-tests simple revision policies against type-specific operators and gates.
7. Expand to 6-8 holdout cases only after demo stability is preserved.
8. Separate pre-execution risk and post-execution failure signals before claiming predictive risk allocation.

## Safe Wording

Use:

```text
Current toy evidence supports the diagnostic value of risk-budgeted verification in a controlled API-review family.
```

Avoid:

```text
We have proven a general risk-budgeted skill deployment method.
```

Avoid:

```text
Risk-based trace is statistically validated.
```

Avoid:

```text
Direct summary is weak.
```
