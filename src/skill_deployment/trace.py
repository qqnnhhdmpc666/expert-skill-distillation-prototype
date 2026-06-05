from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TraceCheckResult:
    passed: bool
    traced_rule_ids: tuple[str, ...]
    missing_trace_rule_ids: tuple[str, ...]
    trace_errors: tuple[str, ...]


def check_rule_application_trace(review: dict[str, Any], traced_rule_ids: set[str]) -> TraceCheckResult:
    findings = review.get("findings", [])
    applications = review.get("rule_applications", [])
    seen_rule_ids = {str(item.get("rule_id")) for item in findings if isinstance(item, dict)}
    applications_by_rule = {str(item.get("rule_id")): item for item in applications if isinstance(item, dict)}
    errors: list[str] = []
    missing: list[str] = []
    for rule_id in sorted(traced_rule_ids):
        if rule_id not in seen_rule_ids:
            errors.append(f"{rule_id} has no finding")
            missing.append(rule_id)
            continue
        app = applications_by_rule.get(rule_id)
        if not app:
            errors.append(f"{rule_id} missing rule_application")
            missing.append(rule_id)
            continue
        for field in ("finding_id", "trigger_condition_found", "evidence_span", "confidence"):
            if not str(app.get(field, "")).strip():
                errors.append(f"{rule_id} missing {field}")
        if app.get("applicable") is not True:
            errors.append(f"{rule_id} must set applicable=true")
    return TraceCheckResult(
        passed=not errors,
        traced_rule_ids=tuple(sorted(traced_rule_ids)),
        missing_trace_rule_ids=tuple(sorted(set(missing))),
        trace_errors=tuple(errors),
    )

