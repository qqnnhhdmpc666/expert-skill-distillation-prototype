# Core Method Spec

Date: 2026-06-06

## Core Claim

Current concise claim:

```text
Skill deployment needs risk-budgeted verification, not just better summarization.
```

Revision framing:

```text
The core problem is not budget checking, but constrained post-execution skill revision.
```

Chinese wording:

```text
专家 skill 部署需要按风险分配验证成本，而不是只追求生成阶段的总结质量。
```

This spec is not a new experiment. It consolidates the current method logic after the direct-summary baseline showed that plain summarization is already strong for salient API-review checklist items.

## Problem Definition

Expert skill deployment is not simply:

```text
expert materials -> better prompt
```

It is a constrained deployment problem:

```text
expert materials
+ task cases
+ verifier feedback
+ token budget
+ validation cost
+ traceability requirements
-> deployment skill package
```

Direct summaries can cover high-salience rules. The harder deployment problem is recovering and controlling residual failures:

- long-tail rules missed by summarization;
- failure-critical rules discovered by execution feedback;
- local patches that may introduce regressions;
- compressed rules that may lose executable semantics;
- trace protocols that strengthen verification but add overhead.

## Inputs

The deployment loop consumes:

- `expert_materials`: source documents, checklists, historical comments, examples.
- `task_case`: the target task or API-review case family.
- `verifier`: local verifier, Harbor verifier, semantic verifier, or trace verifier.
- `token_budget`: fixed or relative prompt/protocol budget.
- `execution_feedback`: failure type, affected rules, reward, missing rules, verifier diagnostics.
- `risk_signals`: rule-level signals used for deployment decisions.

## Output

The output is not only a compact prompt.

It is a deployment skill package:

```text
deployment_skill_package =
  compact_rules
  + trace_policy
  + verifier_contract
  + patch_gate_record
```

Current concrete artifacts include:

- compact skill rules;
- selected traced rule IDs;
- JSON output contract;
- rule application trace contract;
- validation gate result;
- patch/rollback record;
- claim and boundary metadata.

## Core Decisions

The deployment loop makes rule-level and package-level decisions:

- `keep`: preserve a rule in the deployment skill.
- `drop`: remove a rule from the deployment skill.
- `compress`: shorten wording while preserving executable semantics.
- `patch`: add or revise a rule based on verifier feedback.
- `trace`: require rule-application evidence for selected rules.
- `accept`: promote a candidate deployment skill.
- `reject`: block an unsafe, regressive, or over-budget candidate.
- `rollback`: return to the last accepted deployment skill.

Current decision-matrix artifact:

```text
outputs/mvp_vertical_slice/revision_decision_matrix_001
```

This matrix maps feedback/risk types to constrained decisions:

```text
missing_rule -> patch affected rules
output_format_error -> rewrite output contract
regression_observed -> reject and rollback
semantic_compressed -> audit semantic preservation
rule_id_shortcut -> require rule_application trace
fake_trace_evidence -> strengthen trace verifier contract
trace_budget_pressure -> allocate trace to failure-critical rules
```

## Risk Signals

Current risk signals:

- `failure_critical`: rule was implicated in execution failure.
- `previously_missed`: rule was absent from an earlier compact skill or output.
- `newly_patched`: rule was added by a patch proposal.
- `high_priority`: domain expert priority is high.
- `output_contract_sensitive`: failure affects output schema or required fields.
- `semantic_compressed`: rule wording was compressed and needs semantic audit.

These are diagnostic signals, not a mature universal scoring system.

## Acceptance Conditions

A candidate deployment skill should only be accepted when:

- it is within the configured token budget;
- it does not regress on previously covered required rules;
- failure-critical rules are preserved or explicitly marked infeasible;
- selected high-risk rules have required `rule_application` evidence;
- semantic verifier passes for generated findings;
- trace verifier passes for traced rules;
- trace evidence spans pass basic case/rule relevance checks;
- patch and gate records explain why the candidate was accepted or rejected.

If constraints cannot be satisfied under budget, the mature behavior is to report infeasible rather than silently drop critical requirements.

## Core Hypotheses

### H1: Direct Summary Boundary

Direct summary can cover salient rules, but a structured deployment loop helps recover residual failure-critical rules.

Current supporting artifact:

```text
outputs/mvp_vertical_slice/component_baseline_direct_summary_001
```

Current observation:

```text
direct_summary_skill avg coverage: 0.92
patched_compact avg coverage: 1.00
```

Claim strength:

```text
partially_supported
```

### H2: Validation Gate

Validation gate prevents local repair from becoming deployment regression.

Current supporting artifact:

```text
outputs/mvp_vertical_slice/rollback_gate_001
```

Current observation:

```text
patch recovers R005/R006 but drops R003 -> reject_and_rollback
```

Claim strength:

```text
supported in toy slice
```

### H3: Risk-Based Selective Trace

Risk-based selective trace can preserve observability for critical rules with lower overhead than full trace.

Current supporting artifacts:

```text
outputs/mvp_vertical_slice/selective_trace_compiler_001
outputs/mvp_vertical_slice/risk_trace_policy_baseline_001
outputs/mvp_vertical_slice/risk_trace_policy_robustness_001
```

Claim strength:

```text
partially_supported in toy slices
```

Current robustness observation:

```text
Among all 15 size=2 trace allocations over R001-R006, only R005/R006 covers both failure-critical rules. The risk-based policy selects R005/R006 under the same 183/237 token cost.
```

### H4: Joint Deployment Optimization

Compact deployment must optimize correctness, cost, and traceability together.

Current supporting artifacts:

```text
outputs/mvp_vertical_slice/traceable_compiler_integration_001
outputs/mvp_vertical_slice/validation_aware_compiler_001
outputs/mvp_vertical_slice/semantic_preservation_audit_001
outputs/mvp_vertical_slice/adversarial_trace_verifier_001
```

Claim strength:

```text
partially_supported_with_protocol_overhead
```

Current adversarial trace observation:

```text
valid control passes; fake evidence span, generic trigger, mismatched finding_id, and rule-id-only trace are rejected in the toy API-review case.
```

## Claim Boundary

Do not claim:

- this is a benchmark;
- this is a universal compiler;
- broad task correctness has been proven;
- this is a full SPARK-PDI reproduction;
- this replaces COLLEAGUE.SKILL;
- direct summary is generally weak;
- every component is original;
- the repository is already a mature open-source platform.
- the innovation is simply adding a token budget.
- the current prototype is a mature post-execution revision algorithm.

Safe claim:

```text
In a controlled API-review family, the prototype explores expert skill deployment under correctness, budget, and traceability constraints. Direct summaries can cover salient rules, while verifier feedback, patch gates, and risk-budgeted trace help recover and control residual deployment failures.
```

Falsification plan:

```text
docs/FALSIFICATION_AND_NEXT_EVIDENCE.md
```
