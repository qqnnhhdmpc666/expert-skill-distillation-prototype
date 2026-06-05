# Validation-Aware Compiler

This document describes the M2.1 method-discovery slice:

```text
Validation-aware Fixed-budget Compact Compiler
```

It is not a final method claim. It is a probe for whether compact skill recompilation can respect both failure feedback and validation constraints under a fixed token budget.

## Starting Finding

The previous fixed-budget slice showed:

- `execution-aware-fixed-budget` can recover `R005/R006`.
- It stays within the fixed budget.
- But it drops `R003`.

The rollback gate then rejected that patch:

```text
resolves_original_failure: true
regression_detected: true
lost_previously_covered_rules: R003
decision: reject_and_rollback
```

So the next compiler cannot only optimize for failure-critical recovery. It must also preserve previously covered rules or explicitly report infeasibility.

## Mechanism Chain

```text
failure feedback
-> fixed-budget recompilation
-> validation constraints
-> candidate compact skill
-> validation gate
-> accept / reject / rollback / infeasible
```

## Hard Constraints

- `must_include_failure_critical_rules`: `R005`, `R006`.
- `must_preserve_previously_covered_rules`: `R001`, `R002`, `R003`, `R004`.
- `must_include_output_contract_rules` when output contract failures are present.
- `must_not_exceed_budget`.

## Soft Objectives

- Minimize token count.
- Maximize risk, evidence, and execution score.
- Prefer supported rules.
- Avoid unsupported or irrelevant rules.

## Candidate Types

- `candidate_A`: naive execution-aware fixed-budget selector.
- `candidate_B`: preserve-covered-rules-first selector.
- `candidate_C`: compressed-rule variant.
- `candidate_D`: infeasible report if the original required rule set cannot fit.

## Expected Interpretation

If the original rule wording cannot fit under the fixed budget, the compiler should report:

```text
status: infeasible_under_budget
```

That is a useful result, not a failure to hide.

If compressed wording fits, the conclusion should be:

```text
success_with_compressed_wording
```

This means the mechanism may work when rule granularity or wording is optimized. It does not prove that the original selector naturally succeeds.

