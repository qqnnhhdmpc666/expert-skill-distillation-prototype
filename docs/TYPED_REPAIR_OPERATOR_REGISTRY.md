# Typed Repair Operator Registry

Updated: 2026-06-08

## Why this exists

The early prototype selected repairs with an inline branch table inside `scripts/run_generalization_suite.py`. That was enough to prove the story, but it was still script-first. The new layer in `src/skill_deployment/repair.py` moves the repair decision into a reusable, typed operator registry.

This is not a claim of a novel learning algorithm. It is a system-design improvement that makes the prototype less brittle and easier to extend across task families.

## Core idea

Instead of:

```text
feedback_type -> one ad hoc branch in the suite script
```

the project now uses:

```text
VerifierReport + TaskFamily + RepairPolicy
-> typed RepairOperator selection
-> strategy application
-> PatchPlan + GateDecision
```

## Current operator types

- `patch_capability`
- `patch_boundary`
- `rewrite_output_contract`
- `reduce_false_positive_risk`
- `strengthen_evidence_requirement`
- `add_observation_step`
- `reject_and_rollback`
- `no_op`

## What is new here

1. The repair choice is now a first-class module instead of script-local glue.
2. Operators can be family-aware without hard-coding scenario names.
3. Observation-only repair is now represented explicitly.
4. The resulting `PatchPlan` and `GateDecision` carry operator metadata, which makes later audits easier.

## Why this matters

This gives the repository a small but real method layer:

- verifier output is typed
- repair dispatch is typed
- repair execution is strategy-based
- gate decisions remain deterministic
- capability semantics are now shared through `src/skill_deployment/capability_registry.py` instead of duplicated separately in the suite and the local semantic agent

That is a better foundation for:

- non-security transfer
- Harbor runner reuse
- ablations over operator classes
- future learned or LLM-assisted operator selection

## Boundary

This registry does not make the system autonomous. It is still a controlled repair framework with deterministic operator application. The current innovation value is in cleaner posterior revision structure, not in claiming open-ended self-improvement.
