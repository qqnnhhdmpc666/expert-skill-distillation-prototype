# Text Gradients From Failure Contrast

These gradients are optimizer-facing constraints. They are not direct Skill edits.

## config_security_001

- Failure pattern: `missing_capability`
- Lesson: A2 still misses the same capability set: ['CONFIG_ENV_GUARD'].
- Text gradient: Capability presence is insufficient; output templates must force realization in the generated finding.
- Patch risk: `skill_to_execution_gap`

## api_review_001

- Failure pattern: `missing_capability`
- Lesson: A2 still misses the same capability set: ['API_OVERBROAD_RISK'].
- Text gradient: Patch operators must verify a manifest diff before rerun; no-op capability patches must be rejected early.
- Patch risk: `repair_operator_noop_or_patch_application_failure`

## Rejected Edit Memory

- `rejected::config_security_001`: Capability presence is insufficient; output templates must force realization in the generated finding.
- `rejected::api_review_001`: Patch operators must verify a manifest diff before rerun; no-op capability patches must be rejected early.
