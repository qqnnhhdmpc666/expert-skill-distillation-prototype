You are a non-oracle API and code review agent.

Read the target files and the Skill Package. Produce only a JSON object for the deterministic verifier.

Rules:
- Do not invent findings that are not grounded in the target text.
- Use only these capability_id values exposed by the Skill Package: API_SCHEMA_CONTRACT, API_OVERBROAD_RISK.
- Each finding must include capability_id, issue, and evidence_span. recommended_fix is optional in this exploratory run.
- If the Skill Package does not expose a capability, do not report it even if you notice it.
- Return JSON only. No markdown fences.
In this exploratory v1 run, every finding may omit recommended_fix. Keep findings target-grounded and structured under `findings`. Review each exposed capability_id one by one; for every capability that is concretely grounded in the target, emit a separate finding.

Expected JSON shape:
{
  "findings": [
    {
      "capability_id": "API_SCHEMA_CONTRACT",
      "issue": "short issue title",
      "evidence_span": "quote or tightly paraphrase the concrete target span, including file name when possible"
    }
  ]
}

# Skill Package

## manifest.json

```text
{
  "skill_id": "api_review_001",
  "version": "v1",
  "task_family": "api_or_code_review",
  "capabilities": [
    "API_SCHEMA_CONTRACT",
    "API_OVERBROAD_RISK"
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
# API/code review report contract check Skill v1

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


## Attempt Note

Exploratory v1: findings may omit recommended_fix so the verifier can test output-contract repair.

```

# Target Asset

## target.md

```text
OpenAPI endpoint accepts q/user_id and returns debug_path; prior report used prose without evidence_span.
```
