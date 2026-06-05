# Validation-Aware Compiler 001

## Positioning

This is M2.1: validation-aware fixed-budget recompilation. It links the fixed-budget compiler and rollback gate findings.

It is a toy mechanism probe, not a general compiler claim.

## Hard Constraints

- Must include failure-critical rules: R005, R006
- Must preserve previously covered rules: R001, R002, R003, R004
- Must not exceed budget: 237

## Candidate Results

| Candidate | Status | Tokens | Validation | Covered | Missed | Explanation |
|---|---|---:|---|---|---|---|
| candidate_A_naive_execution_aware | candidate | 223 / 237 | reject_regression | R001, R002, R004, R005, R006 | R003 | Naive execution-aware fixed-budget selection from fixed_budget_compiler_001. It recovers R005/R006 but drops R003. |
| candidate_B_preserve_covered_first | candidate | 281 / 237 | reject_over_budget | R001, R002, R003, R004, R005, R006 | none | Preserve all previously covered R001-R004 and add failure-critical R005/R006 with original wording. |
| candidate_C_compressed_required_rules | candidate | 93 / 237 | accept | R001, R002, R003, R004, R005, R006 | none | Preserve R001-R006 by using compressed checklist wording. This is success with compressed wording, not natural success of the original selector. |
| candidate_D_infeasible_original_wording | infeasible_under_budget | 0 / 237 | infeasible | none | R001, R002, R003, R004, R005, R006 | Original R001-R006 wording cannot fit the current budget; required original rule cost exceeds the token budget. |

## Conclusion

- Status: partially_supported
- Finding: Validation-aware fixed-budget recompilation succeeds only when compressed wording is allowed; original wording is infeasible under the current budget.
- Boundary: Toy API-review rules only. Success with compressed wording should not be read as proof of a general compact compiler.
