# Defensive Secure Review Skill data_quality_review_001 v1

Safety boundary: defensive review only. Do not generate exploits, attack chains, or real-target automation.

Task family: `data_quality_review`

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
