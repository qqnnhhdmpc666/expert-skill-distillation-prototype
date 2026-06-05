# Method Discovery Plan

This document is a planning artifact for the method-discovery loop. It does not claim that the current prototype has already produced a mature method. The stable demo remains the primary two-week deliverable; the items below are scoped probes for mechanisms that may become stronger research contributions.

## Decision Standard

A mechanism candidate is worth keeping only if it has all four pieces below:

- Trigger condition: when the mechanism should run.
- Decision rule: how it decides what to change.
- Alternative or counterfactual: what baseline it must beat or clarify.
- Failure boundary: what result would weaken or falsify the mechanism.

## M1: Failure-to-Patch Mapping

Hypothesis:

Execution failures become more useful when they are attributed to a failure type and mapped to a targeted patch action, rather than treated as generic logs or whole-skill regeneration requests.

Trigger condition:

A verifier or execution report returns a failure type such as `missing_rule` or `output_format_error`, plus an affected rule or contract target.

Decision rule:

- `missing_rule` with affected rules maps to `patch_into_compact_v2`.
- `output_format_error` maps to `rewrite_output_contract`.
- Future types such as `irrelevant_rule_interference` may map to `prune_or_demote_rule`.

Alternative or counterfactual:

Compare compiler patches with `no_patch`, random patches, and wrong-type patches under similar token budgets.

Current artifacts:

- `outputs/mvp_vertical_slice/harbor_api_review_001`
- `outputs/mvp_vertical_slice/harbor_api_review_002`
- `outputs/mvp_vertical_slice/output_format_error_001`
- `outputs/mvp_vertical_slice/counterfactual_patch_utility_001`

Missing evidence:

- More failure types beyond `missing_rule` and `output_format_error`.
- More cases per failure type.
- More realistic attribution errors.

Minimal next experiment:

Add an `irrelevant_rule_interference` toy slice only after M2/M3 are not blocking.

Possible failure condition:

If random or wrong-type patches resolve failures as reliably as type-correct patches under similar budgets, then failure-to-patch mapping is not explaining the improvement.

Priority reason:

This is currently the clearest mechanism in the prototype, but it still needs more diverse failure types before stronger claims.

## M2: Fixed-Budget Compact Skill Compiler

Hypothesis:

A compact skill compiler should improve deployment utility under a fixed token budget by replacing lower-value rules with execution-critical rules, not by simply appending more text.

Trigger condition:

The compact skill has a fixed token budget and execution feedback marks some omitted rules as failure-critical.

Decision rule:

Score candidate rules by material support, priority, estimated token cost, and execution evidence. Select rules greedily under a fixed budget. Execution-critical rules receive higher value, but they must still fit within the same budget.

Alternative or counterfactual:

Compare against:

- priority-only selection,
- risk-cost selection without execution evidence,
- execution-aware risk-cost selection under the same budget.

Current artifacts:

- `outputs/mvp_vertical_slice/policy_comparison_001`
- `outputs/mvp_vertical_slice/baseline_001/rule_ledger.json`
- `outputs/mvp_vertical_slice/baseline_001/cost_summary.json`

Missing evidence:

The existing execution-aware policy improves by exceeding the budget. It does not yet prove that execution-aware selection can make better tradeoffs under a fixed budget.

Minimal next experiment:

Generate `outputs/mvp_vertical_slice/fixed_budget_compiler_001`, where all policies share the same budget. The execution-aware policy must evict lower-value rules if it includes R005/R006.

Possible failure condition:

If execution-aware selection cannot improve coverage or failure-critical recovery without exceeding the budget, the current compiler is mostly an append strategy rather than a budgeted compiler.

Priority reason:

This directly addresses the strongest critique of the current prototype: "maybe compact v2 only works because the prompt got longer."

## M3: Rollback and Validation-Gated Revision

Hypothesis:

Skill patches should be accepted only if they resolve the original failure without unacceptable regressions, budget violations, or loss of failure-critical rules.

Trigger condition:

A patch proposal is generated from execution feedback.

Decision rule:

Run a validation gate:

- original failure resolved,
- no regression on a small holdout/check case,
- token budget not exceeded,
- failure-critical rules preserved.

Alternative or counterfactual:

Compare accepted patches with rejected/rolled-back patches that fix one case but violate budget or regress another case.

Current artifacts:

- `outputs/mvp_vertical_slice/output_format_error_001`
- `outputs/mvp_vertical_slice/counterfactual_patch_utility_001`
- `integrations/spark/apply_spark_feedback.py`

Missing evidence:

The current validation gates are simple and do not yet demonstrate rollback on a harmful patch.

Minimal next experiment:

Create `outputs/mvp_vertical_slice/rollback_gate_001`, where a toy patch fixes an original failure but is rejected because it exceeds the budget or drops a failure-critical rule.

Possible failure condition:

If all proposed patches trivially pass or the gate cannot detect regressions/budget violations, rollback remains documentation rather than a mechanism.

Priority reason:

This improves system maturity and answers: "will the repair loop make things worse?"

## M4: Evidence-Grounded Expert Distillation

Hypothesis:

Expert-material-first skill generation is more auditable when rules are tied to material evidence and unsupported rules are downgraded or excluded from deployment skill.

Trigger condition:

The distiller proposes rules from expert documents or examples.

Decision rule:

Rules with strong material support can enter full skill and compact candidates. Weak or unsupported rules should be downgraded, deferred, or kept out of compact deployment unless execution evidence later supports them.

Alternative or counterfactual:

Compare evidence-filtered rules against a direct summary baseline that includes unsupported or over-generalized rules.

Current artifacts:

- `outputs/mvp_vertical_slice/baseline_001/evidence_map.json`
- `outputs/mvp_vertical_slice/baseline_001/rule_ledger.json`
- `outputs/mvp_vertical_slice/baseline_001/full_skill.md`

Missing evidence:

- Cases with intentionally unsupported or conflicting expert-material claims.
- Evidence quality judgment beyond deterministic keyword matching.
- Downstream behavior showing evidence filtering prevents bad compact rules.

Minimal next experiment:

Construct a small unsupported-rule slice after M2/M3. Check whether evidence filtering prevents the unsupported rule from entering compact deployment.

Possible failure condition:

If evidence status never changes compact decisions or downstream behavior, then evidence grounding is only an audit feature in this prototype.

Priority reason:

This is closest to "expert knowledge distillation" as a source-side mechanism, but it needs more material diversity than the current two-week demo requires.

## Current Execution Order

1. Implement M2 fixed-budget compiler first.
2. If time allows, implement M3 rollback/validation-gated revision.
3. Keep M1 and M4 documented, but do not broaden them unless M2/M3 are blocked.

## M2.1: Validation-Aware Fixed-Budget Recompilation

Hypothesis:

A fixed-budget compiler should consider validation constraints during recompilation. It should not recover failure-critical rules by silently dropping previously covered rules. If the current budget cannot satisfy all hard constraints, it should report infeasibility or require compression rather than emitting a misleading compact skill.

Trigger condition:

The previous M2 and M3 probes disagree:

```text
fixed-budget compiler recovers R005/R006
rollback gate rejects the same selection because it drops R003
```

Decision rule:

Generate multiple candidates and validate each against hard constraints:

- include failure-critical rules,
- preserve previously covered rules,
- include output-contract rules when applicable,
- stay within token budget.

Alternative or counterfactual:

Compare:

- naive execution-aware fixed-budget selection,
- preserve-covered-rules-first selection,
- compressed-rule selection,
- explicit infeasible report for original wording.

Current artifact:

```text
outputs/mvp_vertical_slice/validation_aware_compiler_001
```

Current observation:

```text
candidate_A_naive_execution_aware: rejects regression, drops R003
candidate_B_preserve_covered_first: rejects over budget, original R001-R006 cost is 281 > budget 237
candidate_C_compressed_required_rules: accepts, covers R001-R006 with compressed wording
candidate_D_infeasible_original_wording: reports infeasible_under_budget
```

Current interpretation:

```text
partially_supported
```

The slice supports validation-aware recompilation only with compressed wording. It does not show that the original selector naturally succeeds under the same budget.

Failure boundary:

If compressed wording harms real agent behavior or loses semantic precision, then the apparent success is only token accounting, not a reliable compiler mechanism.

## M2.2: Semantic-Preserving Compression Audit

Hypothesis:

Compressed wording can make validation-aware fixed-budget recompilation feasible only if the compressed rules preserve executable review semantics. Otherwise, the compiler may be exploiting a verifier contract that only checks rule IDs.

Trigger condition:

`candidate_C_compressed_required_rules` is accepted by the validation-aware compiler.

Decision rule:

Audit each compressed rule for:

- rule ID presence,
- actionable condition,
- expected finding behavior,
- evidence or trigger phrase,
- not being rule-ID-only.

Then run the candidate through mock and available OpenAI-compatible LLM execution with both the original local verifier and a stricter semantic verifier.

Alternative or counterfactual:

If a candidate only contains rule IDs or generic text, downgrade the conclusion to:

```text
inconclusive: current verifier contract is too weak to validate semantic compression
```

Current artifacts:

- `outputs/mvp_vertical_slice/semantic_preservation_audit_001`
- `outputs/mvp_vertical_slice/compressed_candidate_execution_001`
- `outputs/mvp_vertical_slice/semantic_verifier_001`

Current observation:

```text
semantic audit: preserved
mock execution: semantic verifier pass on case001/case002
RightCode gpt-5.5 execution: semantic verifier pass on case001/case002
```

Current interpretation:

```text
partially_supported
```

The compressed candidate is not a rule-ID shortcut in this toy slice. It preserves enough trigger/action semantics to drive available agents under the lightweight semantic verifier.

Failure boundary:

If a stricter verifier or human review finds that compressed wording causes shallow, template-like, or case-unrelated findings, then M2.2 should be downgraded to `partially_supported_for_artifact_compilation, not yet supported for LLM execution` or `inconclusive`.

## M5: Skill-to-Agent Execution Protocol

Hypothesis:

Compact skill may still fail in complex tasks if it is used as a plain prompt. A structured skill invocation protocol can make the agent expose a rule-application trace, helping distinguish real rule use from mechanical rule-id output.

Trigger condition:

- Compact skill has been compressed.
- The verifier may only check rule-id coverage.
- Agent output lacks evidence linkage.
- Or semantic verification detects template-like or case-unrelated findings.

Decision rule:

Require the agent to output:

- `rule_applications`,
- `trigger_condition_found`,
- `evidence_span`,
- `finding_id`,
- confidence,
- and findings linked to rule applications.

Alternative or counterfactual:

Compare:

- candidate_C compressed skill without protocol,
- rule-id shortcut skill,
- protocolized compressed skill.

Current artifact:

```text
outputs/mvp_vertical_slice/skill_to_agent_loop_001
```

Current observation:

```text
mock:
  candidate_C and shortcut pass simple/semantic verification but fail trace verification.
  protocolized compressed skill passes trace verification.

RightCode gpt-5.5:
  candidate_C and shortcut fail strict trace verification.
  protocolized compressed skill passes trace verification on case001/case002.
```

Current interpretation:

```text
partially_supported
```

Structured skill-to-agent protocol helps distinguish semantic rule use from rule-id shortcut in this toy case.

Failure boundary:

If the protocol only adds output fields without reducing false positives/shortcut behavior, or if token overhead becomes too high, M5 remains an engineering constraint rather than a useful mechanism.

## M2/M3/M5 Integration: Traceable Compact Compiler

Current integration artifact:

```text
outputs/mvp_vertical_slice/traceable_compiler_integration_001
```

The integration step does not introduce another mechanism candidate. It combines the already explored parts into one compilation loop:

```text
M2 fixed-budget selection/compression
-> M5 invocation protocol and trace contract
-> M3 validation gate
-> accept / reject / rollback / over-budget decision
```

Compared variants:

- A: plain compact skill.
- B: compressed compact skill.
- C: compressed compact skill + invocation protocol.
- D: compressed compact skill + invocation protocol + validation gate.

Current observation:

```text
A fails coverage and trace verification.
B passes simple and semantic verification, but fails trace verification.
C passes simple, semantic, and trace verification, but exceeds the fixed token budget.
D correctly rejects the protocolized candidate because it is over budget.
```

Current interpretation:

```text
partially_supported_with_protocol_overhead
```

The trace verifier can block shallow output and rule-id shortcut behavior in this toy integration slice. However, the current invocation protocol adds substantial token overhead, so the validation gate should reject it under the fixed budget.

Failure boundary:

If future protocol compression cannot reduce overhead, this remains a useful diagnostic layer rather than a deployable compact compiler. Do not claim general correctness or a mature compiler.

## Real Effect Evaluation Line

Current artifact:

```text
outputs/mvp_vertical_slice/real_effect_eval_001
```

Hypothesis:

Expert skill deployment should improve real task behavior, not only produce cleaner artifacts. In a small controlled API-review holdout set, patched compact skills should reduce critical misses compared with compact_v1.

Current setup:

- 4 holdout cases.
- Mixed expected rules instead of only R005/R006.
- Includes a false-positive control case.
- Uses deterministic mock case-aware execution first; no LLM result is fabricated.

Current observation:

```text
compact_v1 avg coverage: 0.58
patched_compact avg coverage: 1.00
patched_compact_selective_trace avg coverage: 1.00
```

Current interpretation:

```text
partially_supported
```

Small holdout evidence suggests patched compact skill improves controlled API-review task behavior. This is not a benchmark and does not prove real-world generalization.

## Selective / Risk-Budgeted Trace Line

Current artifact:

```text
outputs/mvp_vertical_slice/selective_trace_compiler_001
outputs/mvp_vertical_slice/risk_trace_policy_baseline_001
outputs/mvp_vertical_slice/risk_trace_policy_robustness_001
```

Hypothesis:

Traceability has a cost, so the compiler should allocate trace requirements to failure-critical, high-risk, or newly patched rules instead of always tracing every rule.

Current observation:

```text
no_trace: 140 / 237 tokens, accepted, but shortcut_blocked=false
full_trace: 300 / 237 tokens, shortcut_blocked=true, rejected_over_budget
selective_trace_failure_critical: 183 / 237 tokens, shortcut_blocked=true, accepted
selective_trace_high_risk_or_patched: 186 / 237 tokens, shortcut_blocked=true, accepted
```

Current interpretation:

```text
partially_supported
```

Selective trace reduces protocol overhead while preserving traceability for failure-critical rules in this toy slice.

Risk-vs-random baseline:

```text
no_trace: 140 / 237 tokens, failure-critical trace coverage 0.00, shortcut_blocked=false
full_trace: 300 / 237 tokens, failure-critical trace coverage 1.00, reject_over_budget
random_selective_trace: R002/R003, 183 / 237 tokens, failure-critical trace coverage 0.00
risk_based_selective_trace: R005/R006, 183 / 237 tokens, failure-critical trace coverage 1.00
```

Current interpretation:

```text
partially_supported
```

With the same selective-trace size and token cost, risk-based selection allocates trace to failure-critical rules while the fixed-seed random baseline does not. This supports the narrow diagnostic claim that risk signals can guide trace budget allocation in this toy slice.

Robustness enumeration:

```text
all size=2 trace combinations over R001-R006: 15
full failure-critical coverage count: 1
partial failure-critical coverage count: 8
zero failure-critical coverage count: 6
risk-based selection: R005/R006, coverage 1.00
```

Current interpretation:

```text
partially_supported
```

The result no longer depends only on one random seed. It shows that, in the current toy rule pool, the risk-based choice is the only size=2 allocation that covers both failure-critical rules.

Failure boundary:

If future cases show that untraced rules produce shortcut errors or semantic drift, the trace selection policy should be tightened. The random baseline uses one seed in a tiny rule pool; random hits are possible, so this is not statistical evidence. Do not claim a mature tracing policy yet.

Falsification plan:

```text
docs/FALSIFICATION_AND_NEXT_EVIDENCE.md
```

## Adversarial Trace Verifier Sanity Check

Current artifact:

```text
outputs/mvp_vertical_slice/adversarial_trace_verifier_001
```

Hypothesis:

Trace verifier should reject obvious fake or weak rule-application evidence, not only check that fields exist.

Adversarial cases:

```text
fake_evidence_span
generic_trigger
mismatched_finding_id
rule_id_only_trace
```

Current observation:

```text
valid control: pass
fake_evidence_span: reject
generic_trigger: reject
mismatched_finding_id: reject
rule_id_only_trace: reject
```

Implementation note:

```text
verify_api_review_trace_json.py now checks evidence_span case/rule relevance separately, so fake spans cannot pass only because trigger_condition_found contains relevant keywords.
```

Current interpretation:

```text
partially_supported
```

Boundary:

This is a basic adversarial sanity check for the toy API-review family, not a deep semantic verifier.
