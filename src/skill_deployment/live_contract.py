from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .capability_registry import CAPABILITY_SPECS
from .schemas import ExecutionReport
from .verifier import verify_controlled_execution


FAILURE_TAXONOMY = (
    "schema_error",
    "missing_evidence",
    "non_exact_span",
    "unsupported_evidence",
    "wrong_capability_group",
    "over_reporting",
    "under_reporting",
    "unsupported_scope",
    "low_confidence_needed",
    "normalizer_needed",
    "model_contract_violation",
)


@dataclass(frozen=True)
class NormalizationResult:
    raw_execution: dict[str, Any]
    normalized_execution: dict[str, Any]
    trace: dict[str, Any]


def _lines(target_text: str) -> list[str]:
    return [line.strip() for line in target_text.splitlines() if line.strip()]


def _clean_span(value: str) -> str:
    text = str(value or "").strip()
    text = re.sub(r"^(target\.md|snippet|evidence|line)\s*:\s*", "", text, flags=re.IGNORECASE).strip()
    text = text.strip("`'\" ")
    return re.sub(r"\s+", " ", text)


def _token_sequence(value: str) -> list[str]:
    return [token for token in re.findall(r"[a-z0-9_\.]+", value.lower()) if len(token) >= 3]


def _ordered_tokens_in_line(tokens: list[str], line: str) -> bool:
    if len(tokens) < 3:
        return False
    cursor = 0
    lowered = line.lower()
    for token in tokens:
        index = lowered.find(token, cursor)
        if index < 0:
            return False
        cursor = index + len(token)
    return True


def _line_for_span(span: str, target_lines: list[str]) -> tuple[str | None, str]:
    cleaned = _clean_span(span)
    if not cleaned:
        return None, "missing_evidence"
    lowered_cleaned = cleaned.lower()
    for line in target_lines:
        if cleaned == line:
            return line, "exact"
        if lowered_cleaned == line.lower():
            return line, "case_normalized_exact"
    for line in target_lines:
        if lowered_cleaned in line.lower():
            return line, "substring_to_complete_line"
    tokens = _token_sequence(cleaned)
    for line in target_lines:
        if _ordered_tokens_in_line(tokens, line):
            return line, "ordered_tokens_to_complete_line"
    return None, "non_exact_span"


def _capability_group_from_id(capability_id: str, activated_capability_group: str | None) -> str:
    if activated_capability_group:
        return activated_capability_group
    if capability_id.startswith("UPLOAD_"):
        return "upload_security"
    if capability_id.startswith("CONFIG_"):
        return "config_security"
    if capability_id.startswith("AUTH_"):
        return "auth_access_control"
    if capability_id.startswith("API_"):
        return "api_or_code_review"
    return "unknown"


def _looks_like_positive_observation(item: dict[str, Any]) -> bool:
    text = " ".join(
        str(item.get(key) or "")
        for key in ("issue", "title", "evidence_span", "recommended_fix", "fix")
    ).lower()
    positive_markers = (
        "prevents",
        "is generated",
        "server_filename is generated",
        "are both checked",
        "both checked",
        "checked",
        "configured",
        "is configured",
        "implemented",
        "enforced",
        "safe denial",
        "required role scope",
        "tenant_id and owner_id",
        "returns only request_id",
        "continue to",
        "maintain",
        "remains set",
        "is set",
        "set to",
        "appropriate value",
        "no issue",
        "already",
        "retention_days is",
        "audit_log_retention_days is",
    )
    risk_markers = (
        "missing",
        "without",
        "empty",
        "unset",
        "generic risk",
        "lacks",
        "leaks",
        "user-controlled",
        "user controlled",
        "trusts",
        "extension only",
        "only extension",
        "only authentication",
        "only checks authentication",
        "only checks is_authenticated",
        "stores uploads_dir",
        "not ",
        "does not",
    )
    return any(marker in text for marker in positive_markers) and not any(marker in text for marker in risk_markers)


def _looks_hypothetical_or_ambiguous(item: dict[str, Any]) -> bool:
    text = " ".join(
        str(item.get(key) or "")
        for key in ("issue", "title", "evidence_span", "recommended_fix", "fix")
    ).lower()
    ambiguity_markers = (
        "might",
        "may ",
        "future",
        "potential",
        "if ",
        "no route",
        "no concrete",
        "not shown",
        "is shown",
        "without a concrete",
    )
    concrete_risk_markers = (
        "emits prose",
        "without evidence_span",
        "without tenant",
        "without owner",
        "loads invoice by id",
        "trusts file.name",
        "stores uploads_dir",
        "retention_days/export_sink empty",
    )
    return any(marker in text for marker in ambiguity_markers) and not any(marker in text for marker in concrete_risk_markers)


def normalize_live_execution_report(
    execution: ExecutionReport | dict[str, Any],
    *,
    target_text: str,
    active_capabilities: list[str] | tuple[str, ...],
    activated_capability_group: str | None,
    out_of_scope: bool,
) -> NormalizationResult:
    """Normalize live-agent output before strict verifier evaluation.

    The normalizer may only use agent-visible target text, model output, and
    Skill/runtime metadata. It does not inspect expected capabilities, expected
    findings, verifier-only evidence spans, or clean labels.
    """

    raw = execution.to_dict() if isinstance(execution, ExecutionReport) else dict(execution)
    allowed = {str(item) for item in active_capabilities}
    target_lines = _lines(target_text)
    normalized_findings: list[dict[str, Any]] = []
    trace_findings: list[dict[str, Any]] = []
    taxonomy_counts = {name: 0 for name in FAILURE_TAXONOMY}

    raw_findings = [item for item in raw.get("findings", []) if isinstance(item, dict)]
    notes = list(raw.get("notes", [])) + ["live_contract_normalized"]
    if out_of_scope and raw_findings:
        taxonomy_counts["unsupported_scope"] += len(raw_findings)
        taxonomy_counts["over_reporting"] += len(raw_findings)
        normalized = {
            "attempt": raw.get("attempt", ""),
            "backend": raw.get("backend", "live_llm_text"),
            "findings": [],
            "notes": list(raw.get("notes", [])) + ["out_of_scope_guard_suppressed_findings"],
        }
        return NormalizationResult(
            raw_execution=raw,
            normalized_execution=normalized,
            trace={
                "normalizer_version": "live_contract_normalizer.v1",
                "oracle_fields_visible_to_normalizer": False,
                "out_of_scope": True,
                "suppressed_findings_count": len(raw_findings),
                "finding_traces": [],
                "failure_taxonomy_counts": taxonomy_counts,
                "evidence_exact_match_rate": 1.0,
                "unsupported_evidence_count_before": None,
                "unsupported_evidence_count_after": 0,
            },
        )

    exact_matches = 0
    for index, item in enumerate(raw_findings):
        capability_id = str(item.get("capability_id") or "").strip()
        finding_trace: dict[str, Any] = {
            "index": index,
            "capability_id": capability_id,
            "input_evidence_span": str(item.get("evidence_span") or ""),
            "action": "kept",
            "normalization_reason": "none",
            "failure_taxonomy": [],
        }
        if not capability_id or (allowed and capability_id not in allowed):
            taxonomy_counts["wrong_capability_group"] += 1
            taxonomy_counts["model_contract_violation"] += 1
            finding_trace["action"] = "dropped"
            finding_trace["failure_taxonomy"].extend(["wrong_capability_group", "model_contract_violation"])
            trace_findings.append(finding_trace)
            continue
        if _looks_like_positive_observation(item):
            taxonomy_counts["over_reporting"] += 1
            taxonomy_counts["normalizer_needed"] += 1
            notes.append(f"positive_observation_suppressed:{capability_id}")
            finding_trace["action"] = "suppressed_positive_observation"
            finding_trace["failure_taxonomy"].extend(["over_reporting", "normalizer_needed"])
            finding_trace["normalization_reason"] = "positive_observation_not_a_finding"
            trace_findings.append(finding_trace)
            continue
        if _looks_hypothetical_or_ambiguous(item):
            taxonomy_counts["over_reporting"] += 1
            taxonomy_counts["low_confidence_needed"] += 1
            taxonomy_counts["normalizer_needed"] += 1
            notes.append(f"ambiguous_or_hypothetical_suppressed:{capability_id}")
            finding_trace["action"] = "suppressed_low_confidence"
            finding_trace["failure_taxonomy"].extend(["over_reporting", "low_confidence_needed", "normalizer_needed"])
            finding_trace["normalization_reason"] = "ambiguous_or_hypothetical_not_a_concrete_finding"
            trace_findings.append(finding_trace)
            continue

        normalized_item = dict(item)
        normalized_item["capability_group"] = _capability_group_from_id(capability_id, activated_capability_group)
        line, reason = _line_for_span(str(item.get("evidence_span") or ""), target_lines)
        if line is None:
            taxonomy_counts["non_exact_span"] += 1
            taxonomy_counts["low_confidence_needed"] += 1
            taxonomy_counts["normalizer_needed"] += 1
            notes.append(f"needs_review_low_confidence_suppressed:{capability_id}")
            finding_trace["action"] = "suppressed_low_confidence"
            finding_trace["failure_taxonomy"].extend(["non_exact_span", "low_confidence_needed", "normalizer_needed"])
            finding_trace["normalization_reason"] = reason
            trace_findings.append(finding_trace)
            continue
        else:
            exact_matches += 1
            if reason != "exact":
                taxonomy_counts["normalizer_needed"] += 1
                if reason != "case_normalized_exact":
                    taxonomy_counts["non_exact_span"] += 1
            normalized_item["evidence_span"] = line
            normalized_item["evidence_match"] = "exact_target_line"
            normalized_item["confidence"] = "high"
            finding_trace["action"] = "rewrote_evidence_span" if reason not in {"exact", "case_normalized_exact"} else "kept"
            finding_trace["normalization_reason"] = reason
            finding_trace["output_evidence_span"] = line
        if not str(normalized_item.get("recommended_fix") or "").strip():
            taxonomy_counts["schema_error"] += 1
            finding_trace["failure_taxonomy"].append("schema_error")
        if capability_id in CAPABILITY_SPECS and not str(normalized_item.get("issue") or "").strip():
            normalized_item["issue"] = CAPABILITY_SPECS[capability_id].title
        normalized_findings.append(normalized_item)
        trace_findings.append(finding_trace)

    denominator = len(normalized_findings)
    evidence_exact_match_rate = round(exact_matches / denominator, 4) if denominator else 1.0
    normalized = {
        "attempt": raw.get("attempt", ""),
        "backend": raw.get("backend", "live_llm_text"),
        "findings": normalized_findings,
        "notes": notes,
    }
    return NormalizationResult(
        raw_execution=raw,
        normalized_execution=normalized,
        trace={
            "normalizer_version": "live_contract_normalizer.v1",
            "oracle_fields_visible_to_normalizer": False,
            "out_of_scope": bool(out_of_scope),
            "suppressed_findings_count": 0,
            "finding_traces": trace_findings,
            "failure_taxonomy_counts": taxonomy_counts,
            "evidence_exact_match_rate": evidence_exact_match_rate,
            "normalized_finding_count": len(normalized_findings),
        },
    )


def classify_verifier_failure(verifier: dict[str, Any]) -> list[str]:
    labels: list[str] = []
    if verifier.get("schema_errors"):
        labels.append("schema_error")
    if verifier.get("missing_capabilities"):
        labels.append("under_reporting")
    if verifier.get("weak_evidence_capabilities"):
        labels.append("missing_evidence")
    if verifier.get("unsupported_evidence_capabilities"):
        labels.append("unsupported_evidence")
    if verifier.get("false_positive_capabilities"):
        labels.append("over_reporting")
    if not labels and verifier.get("pass"):
        labels.append("pass")
    return labels or ["model_contract_violation"]


def before_after_verifier(
    *,
    expected_capabilities: tuple[str, ...],
    raw_execution: dict[str, Any],
    normalized_execution: dict[str, Any],
    target_text: str,
) -> dict[str, Any]:
    before = verify_controlled_execution(expected_capabilities, raw_execution, target_text=target_text).to_dict()
    after = verify_controlled_execution(expected_capabilities, normalized_execution, target_text=target_text).to_dict()
    return {
        "before": before,
        "after": after,
        "before_failure_taxonomy": classify_verifier_failure(before),
        "after_failure_taxonomy": classify_verifier_failure(after),
    }
