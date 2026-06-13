You are a non-oracle training dataset quality review agent.

Read the target files and the Skill Package. Produce only a JSON object for the deterministic verifier.

Rules:
- Do not invent findings that are not grounded in the target text.
- Use only these capability_id values exposed by the Skill Package: DATA_REQUIRED_FIELD_COVERAGE, DATA_TEMPORAL_SPLIT_GUARD, DATA_LABEL_ENUM_ALIGNMENT.
- Each finding must include capability_id, issue, and evidence_span. recommended_fix is optional in this exploratory run.
- If the Skill Package does not expose a capability, do not report it even if you notice it.
- Return JSON only. No markdown fences.
In this exploratory v1 run, every finding may omit recommended_fix. Keep findings target-grounded and structured under `findings`.

Expected JSON shape:
{
  "findings": [
    {
      "capability_id": "DATA_REQUIRED_FIELD_COVERAGE",
      "issue": "short issue title",
      "evidence_span": "quote or tightly paraphrase the concrete target span, including file name when possible"
    }
  ]
}

# Skill Package

## manifest.json

```text
{
  "skill_id": "data_quality_review_001",
  "version": "v1",
  "task_family": "data_quality_review",
  "capabilities": [
    "DATA_REQUIRED_FIELD_COVERAGE",
    "DATA_TEMPORAL_SPLIT_GUARD",
    "DATA_LABEL_ENUM_ALIGNMENT"
  ],
  "output_contract": [
    "capability_id",
    "evidence_span",
    "recommended_fix"
  ],
  "trace_contract": [
    "event",
    "capability_id",
    "evidence_span"
  ],
  "metadata": {}
}

```

## SKILL.md

```text
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

```

# Target Asset

## target.md

```text
dataset_contract.yaml: required_fields=[user_id,event_date,country_code,label]; allowed_labels=[basic,premium,enterprise]; validation_cutoff=2025-04-30.

train.csv sample:
- row 1042: user_id=991, event_date=2025-04-11, country_code=, label=basic
- row 9811: user_id=112, event_date=2025-05-04, country_code=US, label=gold_plus

validation.csv sample:
- row 120: user_id=556, event_date=2025-05-05, country_code=CN, label=premium
```
