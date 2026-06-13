# QGSE-Pareto + Marginal Utility Mechanism

## Role of QGSE-Pareto

QGSE-Pareto is the promotion control layer. It is not the whole project and it is not a reward-only selector. It decides whether a candidate can be staged, quarantined, rejected, or retained for further evidence.

## Marginal Utility

Marginal utility is package-level evidence: the same case, target, verifier, and backend compare active installed packages or candidate packages. A candidate must improve over `active_installed`, not only over a weak baseline.

## Task-Conditioned Activation

Task-conditioned activation routes each task family to a bounded capability group and sends unsupported tasks to `out_of_scope_guard`. Its purpose is to reduce false positives and negative transfer.

## Rejected Buffer

The rejected edit buffer stores rejected candidate direction, score deltas, false-positive deltas, and scope violations. It prevents repeated bad updates rather than deleting inconvenient failures.

## Retirement / Quarantine

Retirement and quarantine are lifecycle controls. They mark stale, risky, no-benefit, or scope-expanding edits as non-promotable until new evidence changes the decision.

## Difference From Simple Pass/Fail

Simple pass/fail asks whether one run passed. This mechanism asks whether a package version has positive marginal value, preserves negative controls, keeps schema and scope constraints, and remains supported by evidence type labels.
