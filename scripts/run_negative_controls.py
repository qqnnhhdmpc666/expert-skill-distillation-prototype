from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data" / "task_cases"
OUT = ROOT / "outputs" / "validation"
REPORTS = ROOT / "reports"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def evidence_supported(evidence_span: str, target_text: str) -> bool:
    evidence = evidence_span.strip()
    if not evidence:
        return False
    return evidence.lower() in target_text.lower()


def verify_findings(expected: list[str], findings: list[dict[str, Any]], target_text: str) -> dict[str, Any]:
    expected_set = set(expected)
    seen = {str(item.get("capability_id", "")) for item in findings if item.get("capability_id")}
    missing = sorted(expected_set - seen)
    false_positive = sorted(seen - expected_set)
    schema_errors = []
    unsupported = []
    for idx, item in enumerate(findings):
        capability_id = str(item.get("capability_id", f"finding_{idx}"))
        if not str(item.get("recommended_fix", "")).strip():
            schema_errors.append(f"{capability_id}.recommended_fix")
        evidence = str(item.get("evidence_span", ""))
        if not evidence_supported(evidence, target_text):
            unsupported.append(capability_id)
    passed = not missing and not false_positive and not schema_errors and not unsupported
    if missing:
        feedback_type = "missing_capability"
    elif false_positive:
        feedback_type = "false_positive_risk"
    elif schema_errors:
        feedback_type = "output_contract_error"
    elif unsupported:
        feedback_type = "unsupported_evidence"
    else:
        feedback_type = "pass"
    return {
        "pass": passed,
        "feedback_type": feedback_type,
        "missing_capabilities": missing,
        "false_positive_capabilities": false_positive,
        "schema_errors": schema_errors,
        "unsupported_evidence_capabilities": unsupported,
        "scores": {
            "capability_coverage_score": 1.0 if not expected_set else round(len(expected_set & seen) / len(expected_set), 4),
            "evidence_binding_score": 0.0 if unsupported else 1.0,
            "output_contract_score": 0.0 if schema_errors else 1.0,
            "regression_safety_score": 0.0 if false_positive else 1.0,
        },
    }


def materialize_case(case_id: str, title: str, target_text: str, expected: list[str]) -> None:
    case_dir = DATA_ROOT / case_id
    write_json(
        case_dir / "case.yaml",
        {
            "case_id": case_id,
            "title": title,
            "task_family": "negative_control",
            "expected_capabilities": expected,
            "v1_capabilities": expected,
            "typical_feedback": "unsupported_evidence" if expected else "false_positive_risk",
            "typical_repair": "reject_or_remove_unsupported_finding",
            "negative_control": True,
            "purpose": "Reject unsupported evidence or false positives.",
        },
    )
    write_text(case_dir / "target_asset" / "target.md", target_text)
    write_text(
        case_dir / "source_materials" / "negative_control_note.md",
        "This case is intentionally adversarial and should not be counted as a positive task pass.",
    )
    write_text(
        case_dir / "source_materials" / "expert_material.md",
        "Negative controls test whether the verifier rejects unsupported evidence and false positives.",
    )
    write_json(case_dir / "expected_behavior.yaml", {"expected_capabilities": expected, "negative_control": True})
    write_json(
        case_dir / "verifier_contract.yaml",
        {
            "checks": [
                "unsupported_evidence_rejection",
                "false_positive_rejection",
                "schema_presence",
            ],
            "required_fields": ["capability_id", "evidence_span", "recommended_fix"],
            "negative_control": True,
        },
    )


def upload_security_negative() -> dict[str, Any]:
    target_text = (
        "app.py: upload() delegates storage to storage_service.save_secure(file). "
        "The local fixture intentionally omits filename.endswith and audit fields."
    )
    expected = ["UPLOAD_TYPE_MAGIC"]
    materialize_case("upload_security_negative", "Upload negative control with missing evidence", target_text, expected)
    findings = [
        {
            "capability_id": "UPLOAD_TYPE_MAGIC",
            "issue": "Upload type and content validation",
            "evidence_span": "filename.endswith without MIME or magic-byte validation",
            "recommended_fix": "Validate MIME, signature, size, and extension together.",
        }
    ]
    report = verify_findings(expected, findings, target_text)
    return {
        "case_id": "upload_security_negative",
        "purpose": "The verifier should reject a finding whose evidence_span is not present in the target asset.",
        "expected_outcome": "fail",
        "agent_findings": findings,
        "verifier_report": report,
        "control_passed": report["pass"] is False and "UPLOAD_TYPE_MAGIC" in report["unsupported_evidence_capabilities"],
    }


def config_security_false_positive_control() -> dict[str, Any]:
    target_text = (
        "config.yaml: prod.debug=false; prod.audit.enabled=true; "
        "prod.audit.retention_days=90; prod.audit.export_sink=siem; "
        "prod.secret_ref=vault://prod/api-token."
    )
    expected: list[str] = []
    materialize_case("config_security_false_positive_control", "Clean production config false-positive control", target_text, expected)
    always_append_findings = [
        {
            "capability_id": "CONFIG_AUDIT_EXPORT",
            "issue": "Production audit retention/export",
            "evidence_span": "prod.audit enabled but retention_days/export_sink missing",
            "recommended_fix": "Require retention and export sink for production audit logs.",
        },
        {
            "capability_id": "CONFIG_ENV_GUARD",
            "issue": "Environment-aware config guard",
            "evidence_span": "dev api_token/debug should not be production findings",
            "recommended_fix": "Bind findings to prod/dev/test path before flagging.",
        },
    ]
    always_append_report = verify_findings(expected, always_append_findings, target_text)
    typed_repair_findings: list[dict[str, Any]] = []
    typed_repair_report = verify_findings(expected, typed_repair_findings, target_text)
    gate = {
        "always_append_decision": "reject" if not always_append_report["pass"] else "accept",
        "typed_repair_plus_gate_decision": "accept" if typed_repair_report["pass"] else "reject",
        "reason": "Reject unsupported findings on a clean target; accept the no-finding output only when expected issue set is empty.",
    }
    return {
        "case_id": "config_security_false_positive_control",
        "purpose": "A clean config should expose false-positive risk in append-style repair.",
        "expected_outcome": "always_append_fail_typed_empty_pass",
        "always_append": {
            "agent_findings": always_append_findings,
            "verifier_report": always_append_report,
        },
        "typed_repair_plus_gate": {
            "agent_findings": typed_repair_findings,
            "verifier_report": typed_repair_report,
        },
        "gate": gate,
        "control_passed": (
            always_append_report["pass"] is False
            and typed_repair_report["pass"] is True
            and gate["always_append_decision"] == "reject"
        ),
    }


def render_report(payload: dict[str, Any]) -> str:
    rows = payload["cases"]
    lines = [
        "# Negative Control Status",
        "",
        "## Result",
        "",
        f"- Cases: `{len(rows)}`",
        f"- Controls passed: `{sum(1 for item in rows if item['control_passed'])}/{len(rows)}`",
        f"- Overall: `{'PASS' if payload['overall_pass'] else 'FAIL'}`",
        "",
        "| Case | Expected | Control Passed | Key Feedback |",
        "|---|---|---:|---|",
    ]
    for item in rows:
        if item["case_id"] == "config_security_false_positive_control":
            feedback = item["always_append"]["verifier_report"]["feedback_type"]
        else:
            feedback = item["verifier_report"]["feedback_type"]
        lines.append(f"| {item['case_id']} | {item['expected_outcome']} | {item['control_passed']} | {feedback} |")
    lines.extend(
        [
            "",
            "## Required Questions",
            "",
            "- Does the system mis-PASS no-evidence issues? No. The upload negative control is rejected as unsupported evidence.",
            "- Can the verifier reject unsupported findings? Yes. It checks that `evidence_span` is present in the target text.",
            "- Can the gate block false positive / regression? In this controlled check, the append-style config output is rejected and the empty typed output is accepted only because the expected issue set is empty.",
            "",
            "## Boundary",
            "",
            "These controls are small deterministic checks. They improve confidence that the verifier can reject unsupported evidence and false positives, but they are not a broad adversarial benchmark.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    cases = [upload_security_negative(), config_security_false_positive_control()]
    payload = {
        "run_id": "negative_controls_001",
        "created_at": utc_now(),
        "cases": cases,
        "overall_pass": all(item["control_passed"] for item in cases),
        "claim_scope": "controlled negative checks for unsupported evidence and false-positive rejection",
    }
    write_json(OUT / "negative_controls.json", payload)
    write_text(REPORTS / "NEGATIVE_CONTROL_STATUS.md", render_report(payload))
    print(json.dumps({"output": str(OUT / "negative_controls.json"), "passed": payload["overall_pass"]}, ensure_ascii=False, indent=2))
    return 0 if payload["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
