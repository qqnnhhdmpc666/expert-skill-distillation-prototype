# Training dataset quality review Skill v1

Task family: `data_quality_review`

## Inspection Procedure

1. Read the target assets and identify concrete evidence spans.
2. Emit only findings grounded in the current target.
3. Follow the output contract: capability_id, evidence_span, recommended_fix.

## Capabilities

### DATA_REQUIRED_FIELD_COVERAGE: Required field coverage
- Evidence: row 1042 has blank country_code in a required column
- Fix: Enforce non-null checks and reject rows missing required fields.

### DATA_TEMPORAL_SPLIT_GUARD: Temporal split guard
- Evidence: train.csv includes row 9811 dated after the validation cutoff
- Fix: Bind split assignment to cutoff rules and quote offending row ids.

### DATA_LABEL_ENUM_ALIGNMENT: Label enum alignment
- Evidence: row 9811 uses label gold_plus outside the allowed enum
- Fix: Validate labels against the contract before training or export.


## Attempt Note

Exploratory v1: findings may omit recommended_fix so the verifier can test output-contract repair.
