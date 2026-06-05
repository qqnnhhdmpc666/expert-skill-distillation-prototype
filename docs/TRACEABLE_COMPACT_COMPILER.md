# Traceable Compact Compiler

This document defines the integrated deployment concept:

```text
Validation-aware, traceable compact skill compiler
```

It is not a new mechanism candidate. It integrates the already explored M2, M3, and M5 slices into one compact skill compilation loop.

## Deployment Artifact

The deployment artifact is not just `compact_skill.md`. It has three parts:

1. Compact skill rules.
2. Invocation protocol.
3. Trace verifier contract.

Together they define not only what the agent should check, but also how the agent must expose rule use and how that use is validated.

## Integrated Roles

### M2: Fixed-Budget Rule Selection / Compression

M2 decides which rules enter the compact deployment artifact under a token budget.

Current lesson:

```text
Original R001-R006 wording is infeasible under the current budget.
Compressed wording can fit R001-R006, but compression must be semantically audited.
```

### M3: Patch Accept / Reject / Rollback

M3 decides whether a candidate compact artifact is safe to deploy.

Current lesson:

```text
A patch that recovers R005/R006 but drops R003 should be rejected.
Validation constraints must check regression, budget, and failure-critical preservation.
```

### M5: Skill-to-Agent Execution Protocol

M5 decides whether the agent actually applies compact rules to task evidence.

Current lesson:

```text
Rule-ID coverage is not enough.
The agent should output rule_applications linked to findings and evidence spans.
```

## Integrated Loop

```text
failure feedback
-> fixed-budget rule selection / compression
-> candidate compact rules
-> invocation protocol attachment
-> agent execution
-> simple / semantic / trace verification
-> validation gate
-> accept / reject / rollback
```

## Integration Slice

Current artifact:

```text
outputs/mvp_vertical_slice/traceable_compiler_integration_001
```

Variants:

- A: plain compact skill.
- B: compressed compact skill.
- C: compressed compact skill + invocation protocol.
- D: compressed compact skill + invocation protocol + validation gate.

Core questions:

1. Is protocol token overhead acceptable?
2. Does trace verification block rule-id shortcut or shallow output?

## Conservative Claim Boundary

If the protocolized variant passes trace verification but exceeds budget, the conclusion is:

```text
partially_supported_with_protocol_overhead
```

If it stays within budget and passes trace verification:

```text
partially_supported: traceable compact compilation is feasible in this toy slice.
```

Do not claim:

- general task correctness,
- a universal compiler,
- or superiority over related work.

## Next Integration: Real Effect and Selective Trace

The traceable compiler integration exposed a useful tradeoff:

```text
traceability improves verifier strength, but it is not free.
```

Two follow-up slices now connect this mechanism back to the original expert-skill deployment goal.

### Real Effect Evaluation

Artifact:

```text
outputs/mvp_vertical_slice/real_effect_eval_001
```

Purpose:

```text
Check whether skill-conditioned deployment improves API-review behavior on a small controlled holdout set.
```

Current result:

```text
partially_supported
```

In the 4-case controlled holdout, `patched_compact` improves average coverage over `compact_v1` and removes the observed critical misses. This is small holdout evidence, not a benchmark.

### Selective Trace Compiler

Artifact:

```text
outputs/mvp_vertical_slice/selective_trace_compiler_001
```

Purpose:

```text
Spend traceability cost only on failure-critical / high-risk / newly patched rules.
```

Current result:

```text
partially_supported
```

Full trace passes trace checks but exceeds the fixed budget. Selective trace for R005/R006 stays under budget and still blocks shortcut behavior for the failure-critical rules in this toy slice.

Conservative interpretation:

```text
risk-budgeted traceable skill deployment prototype
```

This is still not a mature compiler. It is a more precise framing of the current direction: expert skill deployment should optimize cost under correctness, regression, and traceability constraints.
