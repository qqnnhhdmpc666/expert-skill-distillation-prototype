# Improvement Demo Status

Generated at: `2026-06-12T15:01:38.952093+00:00`

This demo uses live LLM validation feedback only. It does not synthesize a fake failure, does not read verifier-only oracle fields, and does not install promoted candidates automatically.

## Summary

- `candidate_generation`: `pass`
- `evolution_safety_gate`: `pass`
- `evolution_improvement`: `not_yet_demonstrated`
- `evolution_maturity`: `safety_gate_pass`
- Blocked reason: `none`

## Candidates

| Candidate | Source case | Decision | Score delta | FP delta | Scope violation |
|---|---|---|---:|---:|---:|
| live_feedback_c001 | holdout_api_overbroad_schema_001 | not_promoted | 0.0 | 0 | False |

## Boundary

- Dependency/version-risk remains unsupported by secure_code_review core capability.
- Candidate rejection is safety evidence, not improvement evidence.
- Improvement is demonstrated only by a staged promotion proposal under the strict rule.
