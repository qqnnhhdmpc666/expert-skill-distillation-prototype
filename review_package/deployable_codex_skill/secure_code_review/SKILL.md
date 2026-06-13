# Secure Code Review Skill

Use this Skill for bounded, defensive security code review and repair recommendation tasks.

## Safety Boundary

- Allowed: defensive detection, explanation, fix recommendation, patch validation, and evidence-grounded review.
- Forbidden: exploit generation, attack-chain execution, unauthorized target testing, credential harvesting, persistence, evasion, or real-target automation.
- For CVE-style material, operate only inside local benchmark or sandbox artifacts and do not emit reusable exploitation steps.

## Required Inputs

- A local target asset or benchmark case.
- A declared task family, such as upload security, config security, API/code review, or data-quality review.
- A Skill manifest with scoped capabilities.

## Required Output

Emit machine-checkable findings. Each finding must include:

- `capability_id`
- `evidence_span`
- `recommended_fix`

Findings without target-grounded evidence should be omitted.

## Operating Procedure

1. Read the target files before proposing any finding.
2. Apply only capabilities enabled in the active Skill manifest.
3. Bind each finding to a concrete evidence span.
4. Prefer minimal fix guidance over broad rewrites.
5. Run verifier or `skill-deploy compare-variants` before promotion.
6. Do not promote a revised Skill unless the qualification card allows it.

## Evolution Policy

- A single failed trajectory is evidence, not permission to edit the Skill.
- Candidate edits must pass marginal utility comparison against `no_skill`, `skill_v1`, `skill_v2`, and `upper_bound`.
- Rejected edits must be recorded in `rejected_edit_buffer.json`.
- Skills may be quarantined, downgraded, retired, or rolled back when evidence shows no utility or harmful side effects.
