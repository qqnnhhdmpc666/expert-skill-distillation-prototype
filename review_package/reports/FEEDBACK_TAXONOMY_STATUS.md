# Feedback Taxonomy Status

更新时间：2026-06-08 04:13 CST

## Artifacts

```text
revision/feedback_taxonomy.json
revision/repair_policy.json
revision/intervention_scores.json
revision/intervention_decision.json
runs/generalization/*/revision/gate_decision.json
```

## Feedback Types

The taxonomy includes missing capability, weak evidence, output contract error, false positive risk, unsafe action risk, regression observed, high cost low gain, trace missing, target context missing, ownership boundary missing, config path missing, and overbroad finding.

## Repair Actions

The repair policy maps feedback to typed actions:

- `missing_capability -> patch_capability`
- `weak_evidence -> strengthen_evidence_requirement`
- `output_contract_error -> rewrite_output_contract`
- `false_positive_risk -> reduce_false_positive_risk`
- `ownership_boundary_missing -> patch_boundary`
- `regression_observed -> reject_and_rollback`

## Intervention Scores

Gate decisions use:

- capability coverage
- evidence binding
- output contract
- regression safety
- cost budget
- trace observability
- safety boundary

## Soft vs Hard Intervention

Soft intervention covers evidence/report/trace/context issues that can be repaired without blocking the whole skill if scores remain acceptable.

Hard intervention covers missing critical capability, schema error, unsafe action risk, regression, and ownership boundary failure. These block pass until repaired.

## Connection To Runs

`scripts/run_generalization_suite.py` writes gate decisions that reference:

```text
taxonomy_ref: revision/feedback_taxonomy.json
repair_policy_ref: revision/repair_policy.json
intervention_scores_ref: revision/intervention_scores.json
```

This keeps the taxonomy connected to artifacts rather than only described in prose.
