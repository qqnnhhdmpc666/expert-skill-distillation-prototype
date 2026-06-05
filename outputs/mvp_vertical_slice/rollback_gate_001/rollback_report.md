# Rollback Gate 001

## Positioning

This is a toy validation-gated revision slice. It checks whether a patch that resolves the original affected rules should still be rejected when it creates a regression.

It is not a mature rollback system or a benchmark.

## Patch Proposal

- Patch action: patch_failure_rules_under_budget
- Proposed rules: R001, R002, R004, R005, R006
- Token count: 223 / budget 237

## Gate Result

- Resolves original affected rules: True
- Regression detected: True
- Lost previously covered rules: R003
- Over budget: False
- Broke failure-critical rules: False

## Rollback Decision

- Decision: reject_and_rollback
- Reason: Patch resolves R005/R006 but drops R003, causing a holdout regression; rollback keeps the previous compact skill.

## Conservative Takeaway

The proposed patch correctly includes R005/R006, but it drops R003, which had been covered by compact v1 and is treated as a holdout regression in this toy gate. This supports the need for a validation gate, but only as a small mechanism probe.
