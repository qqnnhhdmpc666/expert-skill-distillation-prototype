# Counterfactual Patch Utility 001

## Positioning

This is a toy counterfactual experiment. It tests whether type-correct failure attribution plus patch action better explains compact skill recovery than no patch, random patch, or wrong-type patch. It is not a benchmark.

- Random seed: `260605`

| Failure Case | Patch Variant | Action | Type Correct | Sampled Rules | Hit Affected | Added Tokens | Failure Resolved | Passed | Recovered Rules | Notes |
|---|---|---|---|---|---|---:|---|---|---|---|
| missing_rule | no_patch | none | False | none | False | 0 | False | False | none |  |
| missing_rule | random_patch_any | random_rule_patch | False | R003, R007 | False | 44 | False | False | none | Randomly sampled two candidate rules from a small rule pool. |
| missing_rule | random_patch_non_affected | random_rule_patch | False | R007, R003 | False | 44 | False | False | none | Randomly sampled only non-affected rules. |
| missing_rule | wrong_type_patch | rewrite_output_contract | False | none | False | 38 | False | False | none | Wrong type: rewrites output contract but does not add R005/R006. |
| missing_rule | compiler_patch | patch_into_compact_v2 | True | R005, R006 | True | 44 | True | True | R005, R006 | Type-correct compiler patch adds affected missing rules. |
| missing_rule | full_skill_or_oracle_patch | upper_bound_full_review | True | R005, R006 | True | 44 | True | True | R005, R006 | Upper bound only; not part of fair budget comparison. |
| output_format_error | no_patch | none | False | none | False | 0 | False | False | none |  |
| output_format_error | random_rule_patch | random_rule_patch | False | R005 | True | 20 | False | False | R005 | Random content rule patch; does not fix missing required fields in existing findings. |
| output_format_error | wrong_missing_rule_patch | patch_into_compact_v2 | False | R005, R006 | True | 44 | False | False | R005, R006 | Wrong type: adds missing-rule content but does not fix output contract. |
| output_format_error | output_contract_patch | rewrite_output_contract | True | none | False | 38 | True | False | none | Type-correct patch fills required fields. |
| output_format_error | full_contract_patch | full_contract_patch | True | none | False | 38 | True | True | R003, R004, R005, R006 | Upper bound: complete review plus valid output contract. |

## Conservative Interpretation

- If compiler patches outperform no/random/wrong-type patches, this partially supports the failure-to-patch mapping mechanism.
- Random patches may occasionally hit affected rules because the toy rule pool is small; such hits must be reported, not hidden.
- Full skill or oracle patches are upper bounds and are not part of the fair token-budget comparison.
- For output-format failures, `failure_resolved` can be true even if `verifier_passed` is false: this means the format failure was fixed, but other missing-rule failures remain.
- This experiment does not prove a general patch compiler.
