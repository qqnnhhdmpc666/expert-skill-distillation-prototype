# Policy Comparison 001

## Positioning

This is an exploratory compact decision policy comparison. It uses the current API review rules and two existing cases. It is not a benchmark and does not claim large-scale superiority.

- Token budget for budgeted policies: 237

| Policy | Selected Rules | Tokens | Within Budget | Checklist | Reward | Missed Rules | Patch Needed |
|---|---|---:|---|---:|---:|---|---|
| priority-only | R001, R002, R003, R004 | 199 | True | 4 / 6 | 0.0 | R005, R006 | True |
| risk-cost | R001, R002, R004, R005, R007 | 221 | True | 4 / 6 | 0.0 | R003, R006 | True |
| execution-aware-risk-cost | R001, R002, R003, R004, R005, R006 | 281 | False | 6 / 6 | 1.0 | none | False |

## Conservative Takeaway

- Priority-only is cheap but misses medium-priority execution-critical rules.
- Risk-cost is budgeted, but without execution evidence it can still miss rules needed by the verifier.
- Execution-aware risk-cost adds prior failure evidence, so it keeps R005/R006 in this small slice, at the cost of exceeding the current budget.
- The current comparison is exploratory; more cases and failure types are required before stronger claims.
