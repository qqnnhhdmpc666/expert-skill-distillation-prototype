# Constrained Post-Execution Skill Revision

Date: 2026-06-06

## Core Reframing

Weak framing:

```text
Add a token budget; accept if under budget, reject if over budget.
```

This is only an engineering constraint.

Current stronger framing:

```text
The core problem is not budget checking, but constrained post-execution skill revision.
```

Chinese wording:

```text
核心不是检查预算，而是在执行反馈之后，对 skill 进行受约束修正。
```

## Problem

Expert skill distillation does not end when a skill is generated. After deployment, verifier and agent feedback can reveal:

- missing rules;
- output-contract failures;
- local patches that cause regressions;
- compressed rules that preserve rule IDs but lose behavior;
- trace outputs that look structured but contain weak or fake evidence;
- traceability needs that exceed deployment budget.

The system must then decide:

```text
what failed
-> what should be changed
-> whether the change is safe
-> which rules need trace evidence
-> whether to accept, reject, or roll back
```

## Why Budget Alone Is Not Enough

Budget checking only answers:

```text
Can this artifact fit?
```

Constrained post-execution revision asks:

```text
Is this the right repair for this failure type?
Does it preserve existing behavior?
Does it avoid semantic collapse?
Does it allocate trace evidence to the right rules?
Does it expose enough evidence to reject shallow outputs?
```

## Decision Chain

Current prototype decision chain:

```text
execution/verifier feedback
-> failure attribution
-> candidate repair action
-> counterfactual comparison
-> validation gate
-> trace allocation
-> semantic / trace sanity checks
-> accept / reject / rollback
```

## Mechanism Matrix

| Feedback / Risk | Naive Action | Constrained Decision | Supporting Artifact | Current Status |
|---|---|---|---|---|
| `missing_rule` | append more rules | patch affected rules only; compare no/random/wrong-type patch | `counterfactual_patch_utility_001` | partially_supported |
| `output_format_error` | append domain rules | rewrite output contract instead of adding domain rules | `output_format_error_001` | partially_supported |
| `regression_observed` | accept if original failure fixed | reject and rollback if existing coverage regresses | `rollback_gate_001` | supported in toy slice |
| `semantic_compressed` | trust shorter wording | audit trigger/action/output semantics and execute candidate | `semantic_preservation_audit_001` | partially_supported |
| `rule_id_shortcut` | trust rule ID coverage | require rule-application trace evidence | `skill_to_agent_loop_001` | partially_supported |
| `fake_trace_evidence` | trust trace fields | reject fake span, generic trigger, mismatched finding, rule-ID-only trace | `adversarial_trace_verifier_001` | partially_supported |
| `trace_budget_pressure` | trace everything or nothing | allocate trace to failure-critical / newly patched rules | `risk_trace_policy_robustness_001` | partially_supported |

## Current Safe Claim

Use:

```text
The prototype explores constrained post-execution skill revision: verifier feedback is attributed to failure types, candidate repairs are checked against regression, budget, semantic preservation, and traceability constraints, and unsafe revisions can be rejected or rolled back.
```

Avoid:

```text
We propose a mature skill revision algorithm.
```

Avoid:

```text
The innovation is simply adding a cost budget.
```

Avoid:

```text
The system can already predict all risky rules before execution.
```

## Current Limitation

The current evidence is still toy-slice level:

- failure taxonomy is small;
- trace verifier is lightweight;
- risk signals are mostly post-execution;
- holdout remains controlled and small;
- many decisions are deterministic prototypes rather than learned policies.

## Next Evidence

The most valuable next evidence is not another broad feature. It is stronger decision contrast:

1. More failure types where wrong repair action fails.
2. More regression examples where blind patch is rejected.
3. More trace allocations where risk-based policy differs from random/priority-only.
4. More adversarial trace cases where verifier catches shallow evidence.
5. A small expanded holdout only after the above remains stable.
