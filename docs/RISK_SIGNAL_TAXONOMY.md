# Risk Signal Taxonomy

Date: 2026-06-06

## Purpose

This document separates pre-execution and post-execution risk signals so the current prototype does not overclaim predictive risk allocation.

Core claim remains:

```text
Skill deployment needs risk-budgeted verification, not just better summarization.
```

## Why This Taxonomy Matters

The current strongest evidence is post-execution:

```text
verifier failure -> affected rules -> patch/gate/trace budget allocation
```

That is different from claiming:

```text
before execution, the system can perfectly predict which rules will fail
```

The current safe claim is about post-execution risk-budgeted verification and redeployment. Pre-execution risk prediction is a future research direction.

## Pre-Execution Risk Signals

These are available before running a task:

| Signal | Meaning | Current Status |
|---|---|---|
| `high_priority` | Expert or policy marks the rule as important | available |
| `output_contract_sensitive` | Rule affects output schema, required fields, or verifier contract | available in toy slices |
| `semantic_compressed` | Rule wording was shortened and may lose executable semantics | available in compiler/audit slices |
| `low_evidence_support` | Rule has weak or missing material support | planned / partially represented |
| `ambiguous_rule_wording` | Rule wording is broad, vague, or hard to operationalize | planned |
| `rule_length_or_complexity` | Long or multi-clause rule may be expensive or error-prone | planned |

Safe statement:

```text
The prototype records some pre-execution risk signals, but has not proven predictive risk selection before execution.
```

## Post-Execution Risk Signals

These are produced after verifier feedback or execution evidence:

| Signal | Meaning | Current Status |
|---|---|---|
| `failure_critical` | Rule was implicated in a verifier failure | supported in toy slices |
| `previously_missed` | Rule was absent from a prior compact skill or agent output | supported |
| `newly_patched` | Rule was added by a patch after feedback | supported |
| `verifier_missing_rule` | Verifier directly reports a missing rule | supported |
| `regression_observed` | Candidate patch fixes one issue but loses prior coverage | supported in rollback slice |
| `over_budget_observed` | Candidate exceeds deployment budget | supported |

Safe statement:

```text
The current system mainly supports post-execution risk-budgeted verification: once verifier feedback exposes residual failure, patch/gate/trace budget is concentrated on failure-critical or newly patched rules.
```

## Current Claim Boundary

Do say:

```text
After verifier feedback exposes residual failures, the prototype can allocate patch, gate, and trace attention to failure-critical rules in a controlled API-review family.
```

Do not say:

```text
The prototype has proven it can predict all risky rules before execution.
```

Do not say:

```text
Risk-based trace is a mature general policy.
```

## Relation To Current Artifacts

| Artifact | Risk Signal Type | What It Supports |
|---|---|---|
| `harbor_api_review_001/002` | post-execution | verifier exposes missing R005/R006 |
| `counterfactual_patch_utility_001` | post-execution | correct failure attribution helps patch choice |
| `rollback_gate_001` | post-execution | regression signal can reject unsafe patch |
| `risk_trace_policy_baseline_001` | post-execution | failure-critical rules get trace budget |
| `risk_trace_policy_robustness_001` | post-execution | R005/R006 is the only size=2 full failure-critical trace allocation |
| `semantic_preservation_audit_001` | pre-execution / compilation | compressed wording requires semantic audit |

## Next Evidence

If we later want a stronger pre-execution claim, collect:

- larger holdout with rule-level pre-execution risk scores;
- separation between risk scores assigned before execution and labels observed after failure;
- comparison of pre-execution risk trace vs random trace vs post-execution failure-critical trace;
- adversarial cases where obvious high-priority rules are not the failure-critical rules.
