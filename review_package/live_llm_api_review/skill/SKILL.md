# API/code review report contract check Skill v2

Task family: `api_or_code_review`

## Inspection Procedure

1. Read the target assets and identify concrete evidence spans.
2. Emit only findings grounded in the current target.
3. Follow the output contract: capability_id, evidence_span, recommended_fix.

## Capabilities

### API_SCHEMA_CONTRACT: Strict report schema
- Evidence: agent output omits evidence_span or uses free-form prose
- Fix: Emit JSON findings with required evidence and fix fields.

### API_OVERBROAD_RISK: Overbroad finding control
- Evidence: generic security risk without code/config evidence
- Fix: Reject findings not grounded in target spans.
