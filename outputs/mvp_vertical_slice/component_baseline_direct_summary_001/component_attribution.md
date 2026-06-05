# Component Attribution Notes

## What This Baseline Tests

`direct_summary_skill` checks whether a normal summary of expert materials is already enough for the controlled API-review family.

## Observations

- Direct summary coverage: 0.92, pass@1: 3 / 4, avg tokens: 263.0.
- Full skill coverage: 1.00, avg tokens: 1429.8.
- Compact v1 coverage: 0.58, avg tokens: 323.5.
- Patched compact coverage: 1.00, avg tokens: 438.8.
- Patched selective trace coverage: 1.00, avg tokens: 335.0.

## Conservative Reading

Plain summarization can cover several high-salience API-review concerns in this small family. The structured loop is therefore not valuable merely because it names obvious rules.

The current added value is narrower and more defensible: verifier feedback identifies the missed long-tail/failure-critical rule, the patch loop restores it, and trace/gate machinery controls deployment risk.

## Boundary

This is a deterministic toy attribution slice. It does not prove direct summarization is generally strong or weak, and it does not prove the structured system is broadly superior.
