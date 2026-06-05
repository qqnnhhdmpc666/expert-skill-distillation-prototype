# Risk Trace Policy Robustness 001

## Purpose

Enumerate all size=2 trace allocations over R001-R006 to avoid relying on one random seed.

## Aggregate

- total_combinations: 15
- full_failure_critical_coverage_count: 1
- partial_failure_critical_coverage_count: 8
- zero_failure_critical_coverage_count: 6

## Key Comparisons

- risk_based_selective_trace: R005, R006, coverage 1.00, tokens 183 / 237
- previous_random_seed_4: R002, R003, coverage 0.00, tokens 183 / 237

| Traced Rules | Coverage | Tokens | Shortcut Blocked | Gate | Interpretation |
|---|---:|---:|---|---|---|
| R005, R006 | 1.00 | 183 / 237 | True | accept | covers_all_failure_critical |
| R001, R005 | 0.50 | 183 / 237 | True | accept | covers_some_failure_critical |
| R002, R005 | 0.50 | 183 / 237 | True | accept | covers_some_failure_critical |
| R003, R005 | 0.50 | 183 / 237 | True | accept | covers_some_failure_critical |
| R004, R005 | 0.50 | 183 / 237 | True | accept | covers_some_failure_critical |
| R001, R006 | 0.50 | 183 / 237 | True | accept | covers_some_failure_critical |
| R002, R006 | 0.50 | 183 / 237 | True | accept | covers_some_failure_critical |
| R003, R006 | 0.50 | 183 / 237 | True | accept | covers_some_failure_critical |
| R004, R006 | 0.50 | 183 / 237 | True | accept | covers_some_failure_critical |
| R001, R002 | 0.00 | 183 / 237 | True | accept | misses_failure_critical |
| R001, R003 | 0.00 | 183 / 237 | True | accept | misses_failure_critical |
| R001, R004 | 0.00 | 183 / 237 | True | accept | misses_failure_critical |
| R002, R003 | 0.00 | 183 / 237 | True | accept | misses_failure_critical |
| R002, R004 | 0.00 | 183 / 237 | True | accept | misses_failure_critical |
| R003, R004 | 0.00 | 183 / 237 | True | accept | misses_failure_critical |

## Conservative Conclusion

- Status: partially_supported
- Finding: Risk signals identify the only size=2 allocation that covers both failure-critical rules in this toy rule pool.
- Boundary: Toy rule-pool enumeration only. This is not statistical significance and not a mature trace policy.
