# Component Baseline Plan

Date: 2026-06-06

## Purpose

This plan defines small component-level baselines for explaining where the observed gains come from.

It is not a benchmark plan. It is a controlled ablation plan for the API-review family.

Core question:

```text
Which improvement comes from expert rules, which from patching, which from validation gate, which from trace protocol, and which from selective trace policy?
```

## Baselines

| Baseline | Description | Component Isolated | Expected Use |
|---|---|---|---|
| `direct_summary_skill` | Directly summarize expert materials into a skill prompt without rule ledger, evidence map, or patch structure | value of structured expert-rule distillation | Shows whether structure matters beyond summarization |
| `full_skill_no_compiler` | Use full skill directly for agent invocation | value/cost of full expert context | Upper bound for coverage, high-cost baseline |
| `compact_no_feedback` | Use compact_v1 without verifier-driven patch | cost reduction without execution feedback | Shows what compacting loses |
| `patched_no_gate` | Add failed rules after feedback but skip regression/budget validation | value of validation gate | Shows whether blind patching can create regressions/over-budget artifacts |
| `patched_no_trace` | Use patched compact skill without rule-application trace | value of trace protocol | Shows task behavior without observability of rule application |
| `patched_selective_trace` | Use patched compact skill and trace only selected high-risk/failure-critical rules | value of selective trace | Tests risk-budgeted trace as a deployment compromise |

## Current Artifact Mapping

| Baseline | Existing Approximation | Status |
|---|---|---|
| `direct_summary_skill` | Not implemented yet | planned |
| `full_skill_no_compiler` | `real_effect_eval_001` / `full_skill` | available |
| `compact_no_feedback` | `baseline_001` compact_v1; `real_effect_eval_001` compact_v1 | available |
| `patched_no_gate` | Fixed-budget and counterfactual patch variants approximate this | partial |
| `patched_no_trace` | `real_effect_eval_001` patched_compact | available |
| `patched_selective_trace` | `real_effect_eval_001` patched_compact_selective_trace; `selective_trace_compiler_001` | available |

## Evaluation Fields

Use the same fields as `real_effect_eval_001` and `selective_trace_compiler_001`:

- checklist coverage;
- critical missed rules;
- false-positive rules;
- pass@1;
- input tokens;
- output tokens;
- trace tokens;
- total tokens;
- regression detected;
- failure recurrence;
- simple verifier result;
- semantic verifier result;
- trace verifier result when applicable;
- gate decision.

## Attribution Questions

### Expert Rules

Compare:

```text
direct_summary_skill
vs
full_skill_no_compiler
```

Question:

```text
Does structured expert-rule extraction help beyond direct summarization?
```

Expected output:

- coverage difference;
- false-positive difference;
- evidence/rule audit quality.

### Compact Compiler

Compare:

```text
full_skill_no_compiler
vs
compact_no_feedback
```

Question:

```text
What does compacting save, and which rules does it lose?
```

Expected output:

- token reduction;
- missed rules;
- critical missed rules.

### Patch

Compare:

```text
compact_no_feedback
vs
patched_no_trace
```

Question:

```text
Does verifier-driven patching restore task behavior?
```

Current evidence:

```text
compact_v1 avg coverage: 0.58
patched_compact avg coverage: 1.00
```

### Validation Gate

Compare:

```text
patched_no_gate
vs
gated_patch
```

Question:

```text
Does the gate prevent regression or over-budget deployment?
```

Current evidence:

- `rollback_gate_001`: rejects patch that fixes R005/R006 but drops R003.
- `traceable_compiler_integration_001`: rejects full protocolized artifact at 300/237 tokens.

### Trace Protocol

Compare:

```text
patched_no_trace
vs
full_trace
```

Question:

```text
Does trace prevent shortcut behavior, and what does it cost?
```

Current evidence:

```text
full_trace: shortcut_blocked=true, but 300/237 tokens
```

### Selective Trace

Compare:

```text
full_trace
vs
patched_selective_trace
```

Question:

```text
Can trace cost be allocated to high-risk/failure-critical rules while preserving shortcut protection for those rules?
```

Current evidence:

```text
selective_trace R005/R006: 183/237, accepted, shortcut_blocked=true
```

## Minimal Next Experiment

If time allows, implement only one missing baseline:

```text
direct_summary_skill
```

Keep it small:

- use the same 4 holdout cases;
- do not call it a benchmark;
- compare against `full_skill_no_compiler` and `compact_no_feedback`;
- record whether direct summary misses rule IDs, creates false positives, or lacks evidence grounding.

## Claim Boundary

Do not use this plan to claim:

- broad superiority over SPARK-PDI or COLLEAGUE.SKILL;
- large-scale benchmark results;
- a mature compiler;
- general tracing policy.

Safe use:

```text
This baseline plan explains which prototype components are responsible for observed controlled-family improvements.
```

## Engineering Baseline Audit

Component-level baselines should eventually include implementation maturity, not only task metrics.

### Repository-Level Baselines

| Baseline Repository | What It Represents | What To Compare |
|---|---|---|
| SPARK-PDI | research pipeline with package modules, task generation, trajectory/eval scripts, uv config | pipeline cohesion, environment reproducibility, eval assets, package boundaries |
| COLLEAGUE.SKILL | skill artifact tool with install lifecycle and tests | artifact schema, install docs, version/correction lifecycle, test coverage |
| current prototype | demo-oriented artifact lab for controlled API-review deployment | vertical loop completeness, artifact traceability, claim discipline |

### Implementation Maturity Fields

Track these fields when comparing components:

- entrypoint clarity;
- reusable module boundary;
- schema enforcement;
- test coverage;
- error handling;
- configuration/dependency management;
- artifact reproducibility;
- documentation quality;
- extensibility beyond the controlled API-review family.

### Current Honest Assessment

Current prototype strengths:

- strong artifact discipline;
- many reproducible vertical slices;
- clear claim audit;
- controlled loop covers material, skill, compacting, agent, verifier, patch, gate, trace, and effect evaluation.

Current prototype gaps:

- script-first implementation;
- limited formal tests;
- no packaged CLI/API;
- no typed schemas;
- no CI/lint/type gate;
- standards are documented more than enforced.

Safe maturity claim:

```text
The repository is currently a reproducible research/demo prototype, not yet a mature open-source platform.
```

Near-term maturation baseline:

```text
Before claiming platform maturity, match at least the basics visible in related repos:
package config, dependency strategy, unit tests, install/run docs, stable CLI entrypoint, and schema validation.
```
