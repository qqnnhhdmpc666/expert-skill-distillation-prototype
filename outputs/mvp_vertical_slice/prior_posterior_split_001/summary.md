# Prior Posterior Split 001

## Purpose

Separate what prior expert-material signals can decide from what posterior verifier/execution signals add.

| Domain | Prior-Only Decision | Posterior-Only Decision | Prior+Posterior Decision | Posterior Required For |
|---|---|---|---|---|
| api_review | likely_drop_or_deprioritize_residual_rule | patch affected missing rules and trace failure-critical rules | preserve prior high-salience rules while patching posterior failure-critical rules and gating regression | identifying R006/R005 as failure-critical in compact deployment; rejecting a patch that drops R003; allocating trace to failure-critical rules rather than arbitrary high-priority rules |
| config_security | likely_keep C001-C005 and omit C006 | patch C006, repair output contract, and trace C006 | keep C001-C005, patch C006, preserve C003, use compact trace for C006, reject full trace/full skill over budget | marking C006 as a residual deployment miss; discovering that append-only repair breaks output contract; detecting C003 regression under accept-if-fixed; choosing selective trace instead of full trace under budget |

## Aggregate Interpretation

- Status: partially_supported
- Finding: Across the two controlled domains, prior signals are sufficient for initial full skills and many salient rules, but posterior signals are needed to identify residual deployment-critical misses, wrong repair type, regression, and trace-budget pressure. This is the current closest bridge to SPARK's posterior-evidence motivation.
- Boundary: This is a diagnostic split, not a causal or statistical proof. Prior-only decisions are represented by controlled summary/compact baselines, not by an exhaustive prior optimizer.
