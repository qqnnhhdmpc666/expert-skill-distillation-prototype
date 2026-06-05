# Fixed-Budget Compiler 001

## Positioning

This is a method-discovery slice. It asks whether execution-aware compact selection can make a better tradeoff under a fixed budget, rather than simply appending more rules.

It is not a benchmark and does not claim a general compact compiler.

## Budget

- Token budget: 237
- Compact v1 rule cost: 199
- All expected rule cost: 281

## Comparison

| Policy | Selected Rules | Dropped Rules | Tokens | Over Budget | Checklist | Failure-Critical Recovered | Missed Rules | Reward |
|---|---|---|---:|---|---:|---|---|---:|
| priority-only | R001, R002, R003, R004 | R005, R006, R007 | 199 | False | 4 / 6 | none | R005, R006 | 0.0 |
| risk-cost | R001, R002, R004, R005, R007 | R003, R006 | 221 | False | 4 / 6 | R005 | R003, R006 | 0.0 |
| execution-aware-fixed-budget | R001, R002, R004, R005, R006 | R003, R007 | 223 | False | 5 / 6 | R005, R006 | R003 | 0.0 |

## Conservative Takeaway

- Priority-only remains cheap but misses R005/R006.
- Risk-cost uses the same budget but can still miss R006 because it does not know which omitted rule caused execution failure.
- Execution-aware fixed-budget selection recovers R005/R006 without exceeding the budget, but it still misses R003. This supports the tradeoff mechanism only partially.
- The result should be read as a toy mechanism probe: fixed budgets force meaningful rule replacement, but the current rule granularity and small case count are not enough for broad claims.
