# MVP Demo Report

## Positioning

This report is a deterministic MVP baseline. It does not claim a strong new method yet; it validates a minimal expert-skill artifact flow where a rule-level ledger acts as the internal decision backbone.

## Flow

```text
expert materials -> full_skill -> evidence_map -> rule_ledger
-> compact_skill_v1 -> execution_report_v1 -> repair_log
-> compact_skill_v2 -> cost/effect comparison
```

## Four-way Comparison

| Variant | Input Tokens | Passed | Checklist Pass | Missed Rules | Verifier Calls | Retry Count |
|---|---:|---|---:|---|---:|---:|
| no_skill | 0 | False | 0 / 6 | R001, R002, R003, R004, R005, R006 | 1 | 0 |
| full_skill | 1330 | True | 6 / 6 | none | 1 | 0 |
| compact_skill_v1 | 265 | False | 4 / 6 | R005, R006 | 1 | 0 |
| compact_skill_v2 | 339 | True | 6 / 6 | none | 1 | 0 |

## Key Observation

- Compact v1 uses 265 estimated input tokens, about 0.199 of the full skill, but misses R005/R006.
- Execution feedback marks R005/R006 as failure-critical in `rule_ledger.json` and patches them into compact v2.
- Compact v2 uses 339 estimated input tokens, about 0.255 of the full skill, and reaches full checklist coverage on this case.

## Conservative Interpretation

The current result supports the demo goal: compact and repair decisions are traceable through artifacts. It does not yet prove a general optimization method. The next research step is to replace the simple v1/v2 decision policy with a stronger risk-cost or budgeted compact-skill policy.
