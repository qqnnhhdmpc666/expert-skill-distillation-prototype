from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationGateResult:
    accepted: bool
    decision: str
    reason: str
    over_budget: bool
    regression_detected: bool
    missing_required_rules: tuple[str, ...]


def evaluate_validation_gate(
    *,
    selected_rule_ids: set[str],
    required_rule_ids: set[str],
    token_count: int,
    token_budget: int,
    regression_detected: bool = False,
    trace_passed: bool = True,
) -> ValidationGateResult:
    missing_required_rules = tuple(sorted(required_rule_ids - selected_rule_ids))
    over_budget = token_count > token_budget
    if over_budget:
        return ValidationGateResult(False, "reject_over_budget", "Candidate exceeds token budget.", True, regression_detected, missing_required_rules)
    if regression_detected:
        return ValidationGateResult(False, "reject_regression", "Candidate introduces a regression.", False, True, missing_required_rules)
    if missing_required_rules:
        return ValidationGateResult(False, "reject_missing_required_rules", "Candidate misses required rules.", False, regression_detected, missing_required_rules)
    if not trace_passed:
        return ValidationGateResult(False, "reject_trace_failure", "Candidate fails required trace checks.", False, regression_detected, missing_required_rules)
    return ValidationGateResult(True, "accept", "Candidate satisfies gate constraints.", False, False, missing_required_rules)

