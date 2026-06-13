# Data Quality Review Skill

Return one finding per grounded capability.
Use only capability IDs from the manifest.
Every finding must include capability_id, evidence_span, and recommended_fix.

- DATA_REQUIRED_FIELD_COVERAGE: check required fields such as country_code.
- DATA_TEMPORAL_SPLIT_GUARD: check dates against validation_cutoff.
- DATA_LABEL_ENUM_ALIGNMENT: check labels against allowed_labels.
