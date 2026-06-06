# MVP Demo Report

Date: 2026-06-05

## Current Position

Current project positioning:

```text
risk-budgeted traceable skill deployment prototype
```

Equivalent conservative wording:

```text
correctness-constrained expert skill deployment optimization
```

Core method claim:

```text
Skill deployment needs risk-budgeted verification, not just better summarization.
```

Sharper method framing:

```text
The core problem is not budget checking, but constrained post-execution skill revision.
```

Latest method hypothesis:

```text
Posterior skill revision treats a generated skill as a deployable hypothesis. Execution/verifier feedback becomes a posterior signal that decides what to patch, what to reject, what to trace, and when to roll back.
```

Chinese wording:

```text
专家 skill 部署需要按风险分配验证成本，而不是只追求生成阶段的总结质量。
```

This prototype is not a full reproduction of SPARK, not a benchmark, and not a mature universal skill compiler. The demo goal is a controlled vertical loop:

```text
expert material
-> evidence-grounded full skill
-> compact deployment skill
-> agent output
-> verifier feedback
-> patch proposal
-> validation gate
-> compact v2 / rollback
-> selective trace for high-risk rules
```

Related-work delta audit:

```text
docs/RELATED_WORK_DELTA_AUDIT.md
```

Novelty pressure test:

```text
docs/RELATED_WORK_NOVELTY_PRESSURE_TEST.md
```

Component baseline plan:

```text
docs/COMPONENT_BASELINE_PLAN.md
```

Safe relation to SPARK/COLLEAGUE:

```text
We build on COLLEAGUE.SKILL's inspectable skill artifact idea and SPARK-PDI's execution-evidence orientation. Our scoped exploration is correctness-constrained deployment in a controlled API-review family: budgeted compact skill generation, verifier-driven patching, validation gates, rule-application trace, and risk-budgeted selective trace.
```

Do not present this as a full SPARK reproduction, a COLLEAGUE replacement, or a claim that every module is original.

Method synthesis note:

```text
SPARK-PDI's transferable lesson is posterior evidence over prior plans. COLLEAGUE.SKILL's transferable lesson is versioned and correctable skill artifacts. Our current method gap is posterior revision of deployable skill artifacts, not another checklist generator.
```

Repository maturity boundary:

```text
Compared with SPARK-PDI and COLLEAGUE.SKILL, the current repository is a reproducible, artifact-rich demo prototype. It has substantial scripts and evidence artifacts, but it is not yet as mature as an open-source platform: package structure, formal tests, typed schemas, CLI/API, dependency lock, and CI are still limited.
```

## Layer 1: Stable Demo Loop

The stable demo loop demonstrates that expert materials can become deployable skill artifacts and that verifier feedback can repair a compact skill.

Core artifacts:

```text
outputs/mvp_vertical_slice/baseline_001
outputs/mvp_vertical_slice/harbor_api_review_001
outputs/mvp_vertical_slice/harbor_api_review_002
outputs/mvp_vertical_slice/agent_mock_api_review_001
outputs/mvp_vertical_slice/llm_agent_api_review_001
```

Key result:

| Variant | Result |
|---|---|
| no_skill | 0 / 6 |
| full_skill | 6 / 6 |
| compact_v1 | 4 / 6, missing R005/R006 |
| compact_v2 | 6 / 6 |

Real verifier and agent layers:

- Harbor case001/case002: compact_v1 fails on R005/R006; compact_v2 passes.
- Mock agent + Harbor: compact skill content drives `review.json`, not only an oracle solution.
- RightCode `gpt-5.5` matrix: compact_v1 outputs R001-R004; compact_v2 outputs R001-R006 in the controlled case matrix.

Safe claim:

```text
The controlled demo loop shows that verifier feedback can be converted into rule-level patch decisions and produce a corrected compact skill.
```

Boundary:

```text
This is controlled API-review evidence, not broad LLM stability evidence or a benchmark.
```

## Layer 2: Method Discovery

The method-discovery layer explores how compact skills should be patched, selected, validated, compressed, and invoked.

Core artifacts:

```text
outputs/mvp_vertical_slice/output_format_error_001
outputs/mvp_vertical_slice/counterfactual_patch_utility_001
outputs/mvp_vertical_slice/fixed_budget_compiler_001
outputs/mvp_vertical_slice/rollback_gate_001
outputs/mvp_vertical_slice/validation_aware_compiler_001
outputs/mvp_vertical_slice/semantic_preservation_audit_001
outputs/mvp_vertical_slice/skill_to_agent_loop_001
outputs/mvp_vertical_slice/traceable_compiler_integration_001
```

Main observations:

- `output_format_error` maps to output-contract repair, not missing-rule repair.
- Counterfactual patch utility supports the idea that correct failure attribution plus correct patch action has explanatory value in toy slices.
- Fixed-budget selection can recover R005/R006 without simple append, but may drop R003.
- Rollback gate rejects a patch that fixes R005/R006 but regresses R003.
- Validation-aware compression can fit R001-R006 only with compressed wording.
- Semantic audit checks that compressed wording is not only a rule-ID shortcut.
- Skill-to-agent protocol asks the agent to expose `rule_applications`, not only findings.
- Traceable compiler integration shows full protocol passes trace verification but is over budget: `300 / 237`.

Safe claim:

```text
The prototype has a traceable decision chain for patching and deploying compact skills, including rollback and over-budget rejection.
```

Boundary:

```text
These are method-discovery slices. They do not prove a general compiler or superiority over related work.
```

## Layer 3: Effect and Deployment Evaluation

The latest layer checks whether the skill deployment affects controlled task behavior and whether traceability cost can be allocated selectively.

Core artifacts:

```text
outputs/mvp_vertical_slice/real_effect_eval_001
outputs/mvp_vertical_slice/selective_trace_compiler_001
outputs/mvp_vertical_slice/artifact_claim_audit_001
outputs/mvp_vertical_slice/component_baseline_direct_summary_001
outputs/mvp_vertical_slice/risk_trace_policy_baseline_001
outputs/mvp_vertical_slice/risk_trace_policy_robustness_001
outputs/mvp_vertical_slice/direct_summary_miss_analysis_001
outputs/mvp_vertical_slice/adversarial_trace_verifier_001
outputs/mvp_vertical_slice/revision_decision_matrix_001
outputs/mvp_vertical_slice/posterior_revision_signal_audit_001
outputs/mvp_vertical_slice/naive_revision_ablation_001
outputs/mvp_vertical_slice/second_domain_config_security_001
outputs/mvp_vertical_slice/operator_transfer_audit_001
outputs/mvp_vertical_slice/prior_posterior_split_001
```

4-case controlled holdout:

| Variant | Avg Coverage | Pass@1 | Critical Misses | Avg Total Tokens |
|---|---:|---:|---:|---:|
| no_skill | 0.25 | 1 / 4 | 5 | 4.0 |
| full_skill | 1.00 | 4 / 4 | 0 | 1429.8 |
| compact_v1 | 0.58 | 1 / 4 | 1 | 323.5 |
| patched_compact | 1.00 | 4 / 4 | 0 | 438.8 |
| patched_compact_selective_trace | 1.00 | 4 / 4 | 0 | 335.0 |

Selective trace result:

| Trace Policy | Tokens | Shortcut Blocked | Gate |
|---|---:|---|---|
| no_trace | 140 / 237 | false | accept |
| full_trace | 300 / 237 | true | reject_over_budget |
| selective_trace_failure_critical | 183 / 237 | true | accept |
| selective_trace_high_risk_or_patched | 186 / 237 | true | accept |

Safe claim:

```text
Small controlled holdout evidence suggests patched compact skill improves API-review behavior, and toy selective trace reduces protocol overhead while preserving traceability for failure-critical rules.
```

Boundary:

```text
The holdout set has 4 cases and is not a benchmark. Selective trace is a toy policy, not a mature tracing strategy.
```

Component attribution result:

| Variant | Avg Coverage | Pass@1 | Critical Misses | Avg Total Tokens |
|---|---:|---:|---:|---:|
| direct_summary_skill | 0.92 | 3 / 4 | 0 | 263.0 |
| full_skill | 1.00 | 4 / 4 | 0 | 1429.8 |
| compact_v1 | 0.58 | 1 / 4 | 1 | 323.5 |
| patched_compact | 1.00 | 4 / 4 | 0 | 438.8 |
| patched_compact_selective_trace | 1.00 | 4 / 4 | 0 | 335.0 |

Interpretation:

```text
Direct summarization is a strong baseline in this small controlled family. The prototype's safer value claim is not "summaries cannot make useful checklists"; it is that verifier feedback, patching, validation gates, and selective trace can recover and control missed deployment-critical rules.
```

Posterior revision signal audit:

| Diagnostic Axis | Current Observation | Status |
|---|---|---|
| posterior recovery | compact_v1 0.5834 -> patched_compact 1.0000; direct_summary 0.9167 -> patched_compact 1.0000 | partially_supported |
| attribution specificity | type-correct missing-rule and output-contract patches beat wrong-type counterfactuals | partially_supported |
| revision safety | rollback gate rejects a patch that recovers R005/R006 but drops R003 | supported_in_toy_slice |
| trace allocation | only 1/15 size-2 trace allocations covers both failure-critical rules; risk policy selects it | partially_supported |

Safe interpretation:

```text
The current evidence is best understood as a posterior-revision method hypothesis: post-execution evidence changes deployment decisions. This is more method-like than simple budget checking, but still far from a broad PDI-style result.
```

Naive revision ablation:

| Strategy | Observation |
|---|---|
| always_append_domain_rules | fixes missing_rule but not output_format_error |
| always_rewrite_output_contract | fixes output_format_error but not missing_rule |
| always_regenerate_full_skill | fixes tested failures but costs 1429.75 avg tokens as an upper bound |
| accept_if_current_failure_fixed | unsafe because rollback gate observes reject_and_rollback |
| always_full_trace | blocks shortcut but is 300/237 and over budget |
| type_specific_operator_plus_gate_and_selective_trace | resolves tested axes with selective trace 183/237 in the toy slice |

Safe interpretation:

```text
The current method gap is not "posterior feedback exists". It is typed posterior revision over deployable expert-skill packages, with promotion gates and selective trace. This remains a narrow method prototype, not a broad new paradigm.
```

Second-domain config-security probe:

| Strategy | Avg Coverage | Pass@1 | Gate | Tokens |
|---|---:|---:|---|---:|
| direct_summary_skill | 0.825 | 2 / 4 | reject_unresolved_failure | 150 / 260 |
| always_append_domain_rules | 1.000 | 1 / 4 | reject_unresolved_failure | 152 / 260 |
| always_rewrite_output_contract | 0.825 | 2 / 4 | reject_unresolved_failure | 152 / 260 |
| always_regenerate_full_skill | 1.000 | 4 / 4 | reject_over_budget | 289 / 260 |
| accept_if_current_failure_fixed | 0.950 | 3 / 4 | reject_regression | 152 / 260 |
| always_full_trace | 1.000 | 4 / 4 | reject_over_budget | 629 / 260 |
| type_specific_operator_plus_gate_and_selective_trace | 1.000 | 4 / 4 | accept | 166 / 260 |

Safe interpretation:

```text
The second-domain probe strengthens the method seed because the same typed-revision pressure appears in configuration-security: residual domain-rule miss, output-contract failure, regression risk, and trace-budget pressure. It is still hand-constructed and not a benchmark.
```

Operator transfer audit:

```text
Config-security reuses the frozen API-review skeleton for missing_rule, output_contract_error,
regression_observed, and trace_budget_pressure. Domain-specific adapters are rule semantics,
config_path, and the residual trace target C006.
```

Prior/posterior split:

```text
Prior signals build the initial full/compact skills and cover salient rules.
Posterior signals identify residual deployment-critical misses, wrong repair type,
regression, and trace-budget pressure. This is the current closest bridge to
SPARK's posterior-evidence motivation, but it is still diagnostic rather than causal proof.
```

Risk trace policy baseline:

| Trace Variant | Traced Rules | Tokens | Failure-Critical Trace Coverage | Shortcut Blocked | Gate |
|---|---|---:|---:|---|---|
| no_trace | none | 140 / 237 | 0.00 | false | accept |
| full_trace | R001-R006 | 300 / 237 | 1.00 | true | reject_over_budget |
| random_selective_trace | R002/R003 | 183 / 237 | 0.00 | true | accept |
| risk_based_selective_trace | R005/R006 | 183 / 237 | 1.00 | true | accept |

Interpretation:

```text
At the same selective-trace size and token cost, risk-based selection traces failure-critical rules while the fixed-seed random baseline does not. This supports risk-budgeted verification as a toy-slice diagnostic, not as a mature tracing policy.
```

Risk trace robustness:

```text
all size=2 trace combinations: 15
full failure-critical coverage count: 1
risk-based selected R005/R006, the only full-coverage size=2 allocation
```

Direct summary miss analysis:

```text
failed case: case004_validation_sensitive_idempotency
missed rule: R006 idempotency
meaning: direct summary is strong, but can omit a medium-priority deployment-critical rule
```

Adversarial trace sanity check:

```text
valid control: pass
fake_evidence_span: reject
generic_trigger: reject
mismatched_finding_id: reject
rule_id_only_trace: reject
```

Boundary:

```text
Trace verifier has basic adversarial checks, but it is not a deep semantic judge.
```

Revision decision matrix:

| Feedback / Risk | Naive Action | Constrained Decision |
|---|---|---|
| missing_rule | append more rules | patch affected rules and compare no/random/wrong-type repairs |
| output_format_error | append domain rules | rewrite output contract |
| regression_observed | accept if original failure fixed | reject and rollback |
| semantic_compressed | trust shorter wording | audit semantic preservation |
| rule_id_shortcut | trust rule ID coverage | require rule-application trace |
| fake_trace_evidence | trust trace fields | strengthen trace verifier |
| trace_budget_pressure | trace all or none | allocate trace to failure-critical rules |

Interpretation:

```text
The nontrivial part is not the budget check itself. The prototype studies how post-execution feedback changes skill revision decisions under correctness, regression, budget, semantic, and traceability constraints.
```

## Claim Audit Summary

Claim audit artifact:

```text
outputs/mvp_vertical_slice/artifact_claim_audit_001
```

Safe main claim:

```text
The prototype demonstrates a risk-budgeted traceable skill deployment loop in a controlled API-review family: expert materials become evidence-grounded skills, verifier feedback drives patch proposals, validation gates prevent regression or over-budget deployment, and selective trace focuses rule-application evidence on high-risk rules.
```

Do not claim:

- General task correctness is proven.
- This is a benchmark.
- This outperforms related work.
- This is a mature skill compiler.
- The trace protocol applies to all agents or tasks.

## Component Baseline Direction

The next baseline plan should explain which component is responsible for which gain:

| Baseline | What It Tests |
|---|---|
| `direct_summary_skill` | available: plain summary reaches 0.92 avg coverage but misses one long-tail/failure-critical rule |
| `full_skill_no_compiler` | full expert context coverage and cost |
| `compact_no_feedback` | what compacting saves and loses |
| `patched_no_gate` | whether blind patching creates regression or over-budget artifacts |
| `patched_no_trace` | task behavior without rule-application observability |
| `patched_selective_trace` | whether trace cost can be allocated to high-risk rules |

This is a component attribution plan, not a benchmark plan.

Engineering baseline direction:

```text
Future maturity work should compare not only task effect, but also implementation quality: entrypoints, package boundaries, schema enforcement, test coverage, dependency management, and docs/install experience.
```
