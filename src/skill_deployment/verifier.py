from __future__ import annotations

import re
from typing import Any

from .schemas import ExecutionReport, VerifierReport


def _candidate_evidence_variants(evidence_span: str) -> tuple[str, ...]:
    value = evidence_span.strip()
    if not value:
        return ()
    variants = {value.lower()}
    if value.lower().startswith("target.md:"):
        variants.add(value.split(":", 1)[1].strip().lower())
    expanded = set(variants)
    for variant in list(variants):
        if ":" in variant:
            expanded.add(variant.split(":")[-1].strip())
        if ")" in variant:
            expanded.add(variant.split(")", 1)[1].strip())
    variants = expanded
    return tuple(sorted(variants))


def _ordered_token_match(evidence_span: str, normalized_target: str) -> bool:
    tokens = [token for token in re.findall(r"[a-z0-9_\.]+", evidence_span.lower()) if len(token) >= 3]
    if len(tokens) < 3:
        return False
    cursor = 0
    for token in tokens:
        index = normalized_target.find(token, cursor)
        if index < 0:
            return False
        cursor = index + len(token)
    return True


def verify_controlled_execution(
    expected_capabilities: tuple[str, ...],
    output: ExecutionReport | dict[str, Any],
    *,
    feedback_overrides: dict[str, Any] | None = None,
    target_text: str | None = None,
) -> VerifierReport:
    expected = set(expected_capabilities)
    payload = output.to_dict() if isinstance(output, ExecutionReport) else output
    findings = [item for item in payload.get("findings", []) if isinstance(item, dict)]
    seen = {str(item.get("capability_id")) for item in findings if item.get("capability_id")}
    missing = sorted(expected - seen)
    false_positive = sorted(seen - expected)
    schema_errors: list[str] = []
    weak_evidence: list[str] = []
    unsupported_evidence: list[str] = []
    normalized_target = (target_text or "").lower()
    for item in findings:
        capability_id = str(item.get("capability_id", ""))
        evidence_span = str(item.get("evidence_span", "")).strip()
        if capability_id in expected:
            if not evidence_span:
                weak_evidence.append(capability_id)
            if not str(item.get("recommended_fix", "")).strip():
                schema_errors.append(f"{capability_id}.recommended_fix")
            if normalized_target and evidence_span and not (
                any(variant in normalized_target for variant in _candidate_evidence_variants(evidence_span))
                or _ordered_token_match(evidence_span, normalized_target)
            ):
                unsupported_evidence.append(capability_id)
    feedback_type = "pass"
    if missing:
        feedback_type = "missing_capability"
    elif schema_errors:
        feedback_type = "output_contract_error"
    elif weak_evidence:
        feedback_type = "weak_evidence"
    elif unsupported_evidence:
        feedback_type = "unsupported_evidence"
    elif false_positive:
        feedback_type = "false_positive_risk"
    if weak_evidence and isinstance(feedback_overrides, dict):
        feedback_type = str(feedback_overrides.get("weak_evidence", feedback_type))
    return VerifierReport(
        passed=not missing and not false_positive and not schema_errors and not weak_evidence and not unsupported_evidence,
        feedback_type=feedback_type,
        missing_capabilities=tuple(missing),
        false_positive_capabilities=tuple(false_positive),
        schema_errors=tuple(schema_errors),
        weak_evidence_capabilities=tuple(weak_evidence),
        unsupported_evidence_capabilities=tuple(unsupported_evidence),
        scores={
            "capability_coverage_score": round(len(expected & seen) / len(expected), 4) if expected else 1.0,
            "evidence_binding_score": 0.0 if weak_evidence or unsupported_evidence else 1.0,
            "output_contract_score": 0.0 if schema_errors else 1.0,
            "regression_safety_score": 0.0 if false_positive else 1.0,
            "trace_observability_score": 1.0,
        },
    )


def summarize_verifier_report(report: VerifierReport | dict[str, Any]) -> dict[str, Any]:
    payload = report.to_dict() if isinstance(report, VerifierReport) else report
    scores = payload.get("scores", {})
    return {
        "pass": payload["pass"],
        "feedback_type": payload["feedback_type"],
        "coverage": scores.get("capability_coverage_score", 0.0),
        "evidence_binding": scores.get("evidence_binding_score", 0.0),
        "schema_correctness": scores.get("output_contract_score", 0.0),
        "regression_safety": scores.get("regression_safety_score", 0.0),
        "missing_capabilities": payload.get("missing_capabilities", []),
        "unsupported_evidence": payload.get("unsupported_evidence_capabilities", []),
        "schema_errors": payload.get("schema_errors", []),
        "weak_evidence_capabilities": payload.get("weak_evidence_capabilities", []),
        "unsupported_evidence_checked": bool(payload.get("unsupported_evidence_capabilities")),
    }
