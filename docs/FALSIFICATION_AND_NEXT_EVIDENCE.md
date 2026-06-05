# Falsification And Next Evidence

Date: 2026-06-06

## Purpose

This document states how the current core claim could fail, and what evidence should be collected next.

Core claim:

```text
Skill deployment needs risk-budgeted verification, not just better summarization.
```

This document is deliberately conservative. It is meant to prevent the prototype from turning toy-slice evidence into broad claims.

## Current Claim Status

Current status:

```text
partially_supported
```

Current supporting evidence:

- Direct summary is strong but misses one residual rule: `R006`.
- Patched compact recovers that rule in the controlled holdout.
- Risk-based selective trace selects `R005/R006`, the failure-critical rules.
- All size=2 trace combinations show only `R005/R006` covers both failure-critical rules under the same trace size.
- Validation gate rejects known regression and over-budget candidates in toy slices.

## Falsification Conditions

### F1: Direct Summary Has No Residual Misses

If direct summary reaches stable `1.00` coverage on a larger controlled holdout, then the claim that structured deployment recovers residual misses becomes weaker.

Impact:

```text
The system should shift from coverage recovery to patchability, traceability, auditability, and versioned deployment control.
```

Next evidence:

- Expand holdout to 6-8 cases only after current demo is stable.
- Include long-tail rules and false-positive controls.
- Compare direct summary, compact, patched compact, and selective trace.

### F2: Random Trace Performs Like Risk-Based Trace

If random selective trace matches risk-based trace across many settings, then the risk-budgeted trace policy claim becomes weak.

Impact:

```text
Risk signals are insufficient and the trace policy needs redesign.
```

Next evidence:

- Enumerate small rule pools when feasible.
- Use multiple seeds when enumeration is infeasible.
- Report random hit rate for failure-critical rules.

### F3: Trace Verifier Cannot Detect Fake Evidence

If the trace verifier accepts shallow or fake evidence spans, then the traceability claim should be downgraded.

Impact:

```text
Trace protocol is only a formatting constraint, not reliable evidence of rule application.
```

Next evidence:

- Add adversarial trace examples.
- Check whether evidence spans actually appear in the case text.
- Add stronger verifier contracts before making larger claims.

### F4: Validation Gate Only Catches Toy Regressions

If the validation gate only catches hand-constructed regressions and misses realistic regressions, then the gate claim remains an engineering check.

Impact:

```text
The gate should be described as a prototype safeguard, not a robust deployment validator.
```

Next evidence:

- Add more regression cases.
- Test patches that fix one rule while degrading another.
- Track accept/reject decisions with explicit rollback evidence.

### F5: Selective Trace Cost Remains Too High

If selective trace remains over budget or expensive in more complex tasks, the deployment feasibility claim must be weakened.

Impact:

```text
Trace remains useful for audit/debug but may not be feasible for compact deployment.
```

Next evidence:

- Compress protocol wording.
- Trace only failure-critical or newly patched rules.
- Measure overhead across more task cases.

### F6: Failure-Critical Labels Are Too Retrospective

If failure-critical labels only work after manually inspecting outcomes, the method risks being post-hoc.

Impact:

```text
Risk-budgeting becomes explanatory rather than predictive.
```

Next evidence:

- Separate pre-execution risk signals from post-execution failure signals.
- Track which rules were high-risk before the verifier failure.
- Evaluate whether pre-execution risk predicts later failures.

## Next Evidence Priority

Priority order:

1. `risk_trace_policy_robustness_001`: done. Enumerates all size=2 trace combinations in the current rule pool.
2. `direct_summary_miss_analysis_001`: done. Explains the only direct-summary miss.
3. Expand to 6-8 holdout cases only after demo stability is preserved.
4. Add adversarial trace-verifier checks if traceability becomes a central claim.
5. Separate pre-execution risk and post-execution failure signals before claiming predictive risk allocation.

## Safe Wording

Use:

```text
Current toy evidence supports the diagnostic value of risk-budgeted verification in a controlled API-review family.
```

Avoid:

```text
We have proven a general risk-budgeted skill deployment method.
```

Avoid:

```text
Risk-based trace is statistically validated.
```

Avoid:

```text
Direct summary is weak.
```
