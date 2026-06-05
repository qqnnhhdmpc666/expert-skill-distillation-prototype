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
