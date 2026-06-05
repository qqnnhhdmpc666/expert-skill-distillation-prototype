# Risk Trace Policy Baseline 001

## Purpose

Compare risk-based selective trace against no trace, full trace, and same-size random selective trace.

| Variant | Selection | Traced Rules | Tokens | Failure-Critical Trace Coverage | Shortcut Blocked | Gate |
|---|---|---|---:|---:|---|---|
| A_no_trace | none | none | 140 / 237 | 0.00 | False | accept |
| B_full_trace | full | R001, R002, R003, R004, R005, R006 | 300 / 237 | 1.00 | True | reject_over_budget |
| C_random_selective_trace | random | R002, R003 | 183 / 237 | 0.00 | True | accept |
| D_risk_based_selective_trace | risk_based | R005, R006 | 183 / 237 | 1.00 | True | accept |

## Randomness

- random_seed: 4
- random_sampled_rule_ids: R002, R003
- random_hit_failure_critical_rule: False

## Conservative Conclusion

- Status: partially_supported
- Finding: Risk signals help allocate trace budget to failure-critical rules in this toy slice.
- Boundary: Toy risk-trace policy baseline only. Random hit or miss can change results in this small rule pool; this is not statistical evidence.
