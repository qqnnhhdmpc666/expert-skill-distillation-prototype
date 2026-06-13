from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PRE_ROOT = ROOT / "outputs" / "non_oracle_validation_pre_p0_l_repair"
POST_ROOT = ROOT / "outputs" / "non_oracle_validation"
REPORT = ROOT / "reports" / "NON_ORACLE_DISCREPANCY_ANALYSIS.md"
JSON_REPORT = ROOT / "reports" / "non_oracle_discrepancy_analysis.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def row_by_case(summary: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = {}
    for row in summary.get("rows", []):
        if row.get("backend") == "non_oracle_local_semantic":
            rows[str(row.get("case_id"))] = row
    return rows


def verifier_for(root: Path, case_id: str) -> dict[str, Any]:
    return read_json(root / "cases" / case_id / "non_oracle_local_semantic" / "verifier_report.json", {})


def output_for(root: Path, case_id: str) -> dict[str, Any]:
    return read_json(root / "cases" / case_id / "non_oracle_local_semantic" / "agent" / "agent_output.json", {})


def classify_failure(row: dict[str, Any], verifier: dict[str, Any], output: dict[str, Any]) -> dict[str, Any]:
    findings = output.get("findings", []) if isinstance(output.get("findings"), list) else []
    false_positive_caps = verifier.get("false_positive_capabilities", [])
    unsupported_caps = verifier.get("unsupported_evidence_capabilities", [])
    schema_errors = verifier.get("schema_errors", [])
    missing_caps = verifier.get("missing_capabilities", [])
    reasons: list[str] = []
    repairable: list[str] = []
    if false_positive_caps:
        reasons.append("capability_activation_or_false_positive_issue")
        repairable.append("filter non-oracle scanning to task-conditioned active capabilities")
    if unsupported_caps:
        reasons.append("evidence_span_formatting_issue")
        repairable.append("normalize evidence spans to exact target lines")
    if schema_errors:
        reasons.append("output_schema_issue")
        repairable.append("normalize required output fields without changing verifier")
    if missing_caps:
        reasons.append("backend_detection_gap")
    if not reasons and row.get("verifier_result") == "fail":
        reasons.append(str(row.get("failure_reason") or "unknown_verifier_failure"))
    if not findings and row.get("activated_capability_group") == "out_of_scope_guard":
        reasons.append("out_of_scope_no_findings_expected")
    return {
        "failure_categories": reasons,
        "normalization_repair_candidate": repairable,
        "backend_too_weak": bool(missing_caps) or ("backend_detection_gap" in reasons),
        "schema_issue": bool(schema_errors),
        "evidence_span_issue": bool(unsupported_caps),
        "false_positive_issue": bool(false_positive_caps),
        "false_positive_capabilities": false_positive_caps,
        "unsupported_evidence_capabilities": unsupported_caps,
        "schema_errors": schema_errors,
        "missing_capabilities": missing_caps,
    }


def build_payload() -> dict[str, Any]:
    pre = read_json(PRE_ROOT / "non_oracle_validation_summary.json", {})
    post = read_json(POST_ROOT / "non_oracle_validation_summary.json", {})
    pre_rows = row_by_case(pre)
    post_rows = row_by_case(post)
    cases = sorted(set(pre_rows) | set(post_rows))
    analyses = []
    for case_id in cases:
        pre_row = pre_rows.get(case_id, {})
        post_row = post_rows.get(case_id, {})
        pre_verifier = verifier_for(PRE_ROOT, case_id)
        pre_output = output_for(PRE_ROOT, case_id)
        post_verifier = verifier_for(POST_ROOT, case_id)
        classification = classify_failure(pre_row, pre_verifier, pre_output)
        analyses.append(
            {
                "case_id": case_id,
                "task_family": pre_row.get("task_family") or post_row.get("task_family"),
                "pre_repair_verifier_result": pre_row.get("verifier_result"),
                "pre_repair_feedback_type": pre_row.get("verifier_feedback_type") or pre_row.get("failure_reason"),
                "pre_repair_false_positive_count": pre_row.get("false_positive_count"),
                "post_repair_verifier_result": post_row.get("verifier_result"),
                "post_repair_feedback_type": post_row.get("verifier_feedback_type") or post_row.get("failure_reason"),
                "post_repair_false_positive_count": post_row.get("false_positive_count"),
                "post_repair_discrepancy": post_row.get("discrepancy_vs_offline_deterministic"),
                "classification": classification,
                "repair_attempted": [
                    "task-conditioned active capability filtering",
                    "exact-line evidence span normalization",
                    "out_of_scope_guard false-positive suppression via empty active capability set",
                ],
                "verifier_relaxed": False,
                "verifier_only_oracle_read": False,
                "pre_repair_artifact_dir": pre_row.get("artifact_dir"),
                "post_repair_artifact_dir": post_row.get("artifact_dir"),
            }
        )
    post_pass = sum(1 for row in post_rows.values() if row.get("verifier_result") == "pass")
    return {
        "generated_at": utc_now(),
        "pre_repair_summary": str(PRE_ROOT / "non_oracle_validation_summary.json"),
        "post_repair_summary": str(POST_ROOT / "non_oracle_validation_summary.json"),
        "case_count": len(analyses),
        "post_repair_pass_count": post_pass,
        "post_repair_behavior": post.get("non_oracle_behavior") or post.get("overall_status"),
        "oracle_policy": {
            "verifier_only_oracle_read_for_analysis": False,
            "verifier_relaxed": False,
            "secure_code_review_scope_expanded": False,
            "dependency_version_risk_absorbed": False,
        },
        "case_analyses": analyses,
    }


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# Non-Oracle Discrepancy Analysis",
        "",
        f"Generated at: `{payload['generated_at']}`",
        "",
        "## Scope",
        "",
        "This analysis separates backend execution from behavior effectiveness. It reads pre-repair and post-repair non-oracle summaries, verifier reports, and agent outputs only. It does not read verifier-only expected findings or evidence spans, does not relax the verifier, and does not expand secure_code_review scope.",
        "",
        "## Summary",
        "",
        f"- Pre-repair evidence: `{payload['pre_repair_summary']}`",
        f"- Post-repair evidence: `{payload['post_repair_summary']}`",
        f"- Cases analyzed: `{payload['case_count']}`",
        f"- Post-repair verifier pass count: `{payload['post_repair_pass_count']}`",
        f"- Post-repair non-oracle behavior: `{payload['post_repair_behavior']}`",
        "- Repair attempted: task-conditioned active capability filtering, exact-line evidence span normalization, and out-of-scope false-positive suppression.",
        "",
        "## Case Analysis",
        "",
        "| Case | Task family | Pre result | Pre reason | Pre FP | Failure category | Post result | Post reason | Post FP | Post discrepancy |",
        "|---|---|---|---|---:|---|---|---|---:|---|",
    ]
    for row in payload["case_analyses"]:
        category = ", ".join(row["classification"]["failure_categories"])
        lines.append(
            f"| {row['case_id']} | {row['task_family']} | {row['pre_repair_verifier_result']} | "
            f"{row['pre_repair_feedback_type']} | {row['pre_repair_false_positive_count']} | {category} | "
            f"{row['post_repair_verifier_result']} | {row['post_repair_feedback_type']} | "
            f"{row['post_repair_false_positive_count']} | {row['post_repair_discrepancy']} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Verifier was not relaxed.",
            "- No verifier-only oracle expected finding, evidence span, or clean/negative label was used for repair generation.",
            "- Dependency/version-risk remains unsupported by secure_code_review core capability.",
            "- If a future non-oracle row fails, it remains discrepancy evidence rather than being deleted.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    payload = build_payload()
    write_json(JSON_REPORT, payload)
    write_text(REPORT, render(payload))
    print(json.dumps({"report": str(REPORT), "post_repair_behavior": payload["post_repair_behavior"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
