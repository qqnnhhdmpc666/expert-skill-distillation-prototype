# Output Format Error Repair Log

## Source Execution Report

- Task: api-review-output-format-error-001
- Passed: False
- Failure type: output_format_error
- Affected contract: OUTPUT_CONTRACT
- Patch action: rewrite_output_contract

## Interpretation

This is not a `missing_rule` patch. The verifier did not fail because R005/R006 were absent from the compact skill. It failed because the agent output violated the required review JSON contract: each finding must include `rule_id`, `issue`, `severity`, and `evidence`.

## Patch

The compact skill v2 adds an explicit JSON schema and required-field instruction. The patch target is the output contract, not a domain review rule.
