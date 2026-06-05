# Selective Trace Compiler 001

## Positioning

Toy slice for deciding where traceability cost should be spent under a fixed budget.

| Variant | Traced Rules | Tokens | Trace Pass | Shortcut Blocked | Gate |
|---|---|---:|---|---|---|
| A_no_trace | none | 140 / 237 | True | False | accept |
| B_full_trace | R001, R002, R003, R004, R005, R006 | 300 / 237 | True | True | reject_over_budget |
| C_selective_trace_failure_critical | R005, R006 | 183 / 237 | True | True | accept |
| D_selective_trace_high_risk_or_patched | R001, R003, R005, R006 | 186 / 237 | True | True | accept |

## Conservative Conclusion

- Status: partially_supported
- Finding: Selective trace reduces protocol overhead while preserving traceability for failure-critical rules in this toy slice.
- Boundary: Toy selective-trace slice only. It does not prove a mature protocol or general correctness.
