You are a non-oracle training dataset quality review agent.

Read the target files and the Skill Package. Produce only a JSON object for the deterministic verifier.

Rules:
- Do not invent findings that are not grounded in the target text.
- Use only these capability_id values exposed by the Skill Package: DATA_REQUIRED_FIELD_COVERAGE, DATA_TEMPORAL_SPLIT_GUARD, DATA_LABEL_ENUM_ALIGNMENT.
- Each finding must include capability_id, issue, evidence_span, and recommended_fix.
- If the Skill Package does not expose a capability, do not report it even if you notice it.
- Return JSON only. No markdown fences.
This is a metamorphic row-shuffle target. Preserve conclusions that are invariant to row order.

Expected JSON shape:
{
  "findings": [
    {
      "capability_id": "DATA_REQUIRED_FIELD_COVERAGE",
      "issue": "short issue title",
      "evidence_span": "quote or tightly paraphrase the concrete target span, including file name when possible",
      "recommended_fix": "specific fix grounded in the target"
    }
  ]
}

# Skill Package

## manifest.json

```text
{
  "skill_id": "live_llm_data_quality_row_shuffle_metamorphic",
  "version": "metamorphic",
  "capabilities": [
    "DATA_REQUIRED_FIELD_COVERAGE",
    "DATA_TEMPORAL_SPLIT_GUARD",
    "DATA_LABEL_ENUM_ALIGNMENT"
  ]
}

```

## SKILL.md

```text
# Data Quality Review Skill

Return one finding per grounded capability.
Use only capability IDs from the manifest.
Every finding must include capability_id, evidence_span, and recommended_fix.

- DATA_REQUIRED_FIELD_COVERAGE: check required fields such as country_code.
- DATA_TEMPORAL_SPLIT_GUARD: check dates against validation_cutoff.
- DATA_LABEL_ENUM_ALIGNMENT: check labels against allowed_labels.

```

# Target Asset

## target.md

```text
validation.csv sample:
- row 120: user_id=556, event_date=2025-05-05, country_code=CN, label=premium
train.csv sample:
- row 9811: user_id=112, event_date=2025-05-04, country_code=US, label=gold_plus
- row 1042: user_id=991, event_date=2025-04-11, country_code=, label=basic
dataset_contract.yaml: required_fields=[user_id,event_date,country_code,label]; allowed_labels=[basic,premium,enterprise]; validation_cutoff=2025-04-30.
```
