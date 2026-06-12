# Iterative Contract Improvement Status

Generated at: `2026-06-12T18:10:11.949283+00:00`

- Candidate attempts: `5`
- Best candidate: `c006_combo`
- Evolution improvement: `demonstrated`
- Evolution maturity: `improvement_demonstrated`
- Promotion proposals: `2`

## Candidate Decisions

| Candidate | Decision | Active score | Candidate score | Delta | FP delta | Positive regressions | Clean not worse | Unsupported preserved |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| c002_guard | not_promoted | 0.8792 | 0.8125 | -0.0667 | 0 | 2 | True | True |
| c003_auth | staged_promotion_proposal | 0.8792 | 0.925 | 0.0458 | 0 | 0 | True | True |
| c004_api | not_promoted | 0.8792 | 0.8292 | -0.05 | 0 | 2 | True | True |
| c005_cfg | not_promoted | 0.8792 | 0.8417 | -0.0375 | 0 | 1 | True | True |
| c006_combo | staged_promotion_proposal | 0.8792 | 0.9292 | 0.05 | 0 | 0 | True | True |

## Boundary

- Candidates were generated only from failure reports, verifier feedback, evidence summaries, and normalization traces.
- Verifier-only oracle fields were not read.
- No candidate is auto-installed; staged promotion is a proposal requiring human review.
- Dependency/version-risk, regex DoS, and server-side execution review remain out of scope.
