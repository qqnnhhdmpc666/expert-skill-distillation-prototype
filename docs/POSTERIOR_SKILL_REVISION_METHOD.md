# Posterior Skill Revision Method Hypothesis

Date: 2026-06-06

## Why This Document Exists

The project should not be framed as:

```text
add a token budget to compact skill generation
```

That is only an engineering constraint. A stronger method question is:

```text
When a generated expert skill enters execution, can posterior evidence guide how the skill should be revised, validated, and traced?
```

This document is a method hypothesis, not a final contribution claim.

## Related-Work Pressure

SPARK-PDI's important move is methodological: it argues that posterior execution evidence is more reliable than prior plans for skill distillation. The transferable lesson is not just "run a verifier"; it is that the timing and grounding of evidence matter.

COLLEAGUE.SKILL's important move is artifact-oriented: it treats generated skills as inspectable, versioned, correctable packages rather than one-off prompts.

Our current gap is between these two ideas:

```text
versioned skill artifact
+ posterior execution/verifier evidence
-> principled deployment revision
```

The current prototype does not yet propose a broad PDI-like metric. The most promising method direction is narrower but still transferable:

```text
Posterior Skill Revision:
a generated skill is treated as a deployable hypothesis; after execution, posterior feedback determines what to patch, what to reject, what to trace, and when to roll back.
```

API review is only the measurement probe in the current implementation. The method claim should be stated over expert-skill deployment generally.

## Method Chain

The candidate method chain is:

```text
prior expert materials
-> initial/full skill
-> compact deployment skill
-> agent execution
-> posterior verifier/trajectory feedback
-> failure attribution
-> type-specific patch proposal
-> validation and regression gate
-> selective trace allocation for high-risk rules
-> revised deployment skill or rollback
```

This is different from a simple `if over budget then reject` rule. Budget is only one constraint. The method decision is over:

- residual failure recovery;
- failure attribution quality;
- patch sufficiency;
- regression risk;
- semantic preservation after compression;
- trace evidence allocation;
- posterior-vs-prior evidence value.

## Diagnostic Questions

### D1: Posterior Recovery

Question:

```text
Does post-execution feedback recover residual failures that prior skill generation or direct summarization missed?
```

Current evidence:

```text
outputs/mvp_vertical_slice/posterior_revision_signal_audit_001
```

Observed in current controlled slice:

```text
compact_v1 coverage: 0.5834
patched_compact coverage: 1.0000
direct_summary coverage: 0.9167
posterior gain over compact_v1: +0.4166
posterior gain over direct_summary: +0.0833
```

Interpretation:

Direct summary is strong. The method value is not "summary is bad"; it is residual deployment failure recovery.

### D2: Attribution Specificity

Question:

```text
Does the failure type determine the useful revision action?
```

Current evidence:

```text
outputs/mvp_vertical_slice/counterfactual_patch_utility_001
```

Observed:

```text
missing_rule:
  compiler_patch resolves failure
  no_patch/random_patch/wrong_type_patch fail

output_format_error:
  output_contract_patch resolves the format failure
  wrong_missing_rule_patch does not
```

Interpretation:

The current evidence supports the diagnostic value of failure-to-action mapping in toy slices.

### D3: Revision Safety

Question:

```text
Can a patch fix the observed failure while making the deployment skill worse?
```

Current evidence:

```text
outputs/mvp_vertical_slice/rollback_gate_001
```

Observed:

```text
patch recovers R005/R006 but drops R003
gate decision: reject_and_rollback
```

Interpretation:

The revision problem is global, not local. Fixing the visible failure is not enough.

### D4: Trace Allocation

Question:

```text
Can posterior risk signals guide where to spend trace evidence budget?
```

Current evidence:

```text
outputs/mvp_vertical_slice/risk_trace_policy_robustness_001
```

Observed:

```text
15 possible size-2 trace allocations
only R005/R006 covers both failure-critical rules
risk-based allocation selects R005/R006
```

Interpretation:

This is a toy rule-pool result, but it starts to look like a general allocation problem: trace evidence is a limited verification resource.

## What Would Make This More Like A Strong Method

The next stronger version should not merely add cases. It should test whether the method chain remains meaningful when the surface task changes.

Minimum next evidence:

- a second expert-skill domain where prior skill generation leaves a residual deployment failure;
- at least two failure types beyond missing rule and output format;
- counterfactual patch actions that are budget-matched;
- a validation gate example where a plausible patch causes regression;
- trace allocation comparison against random and priority-only policies;
- a clear posterior-vs-prior distinction: which signals were known before execution, which only appear after execution.

The goal is not a large benchmark yet. The goal is to see whether "posterior skill revision" survives outside the current API-review probe.

## Current Safe Claim

Use:

```text
The current prototype supports a method hypothesis: posterior execution/verifier evidence can act as a revision signal for expert skill deployment, guiding failure attribution, patch selection, regression gating, and trace allocation under constraints.
```

Avoid:

```text
We propose a mature general skill compiler.
```

Avoid:

```text
We prove posterior revision is broadly better than prior skill generation.
```

Avoid:

```text
Our current metric is analogous in scope to SPARK-PDI.
```

## Open Method Gap

The missing PDI-like abstraction would need to answer:

```text
How much of a deployed skill's later success is explained by posterior evidence-grounded revision, rather than by prior material summarization or generic model capability?
```

Current diagnostic approximation:

```text
posterior_revision_utility =
  recovery_gain
  + attribution_specificity
  + regression_avoidance
  + trace_allocation_utility
```

This is not yet a final metric. It is a research direction that can be falsified by broader evidence.
