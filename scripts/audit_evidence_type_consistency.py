from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "EVIDENCE_TYPE_CONSISTENCY_AUDIT.md"
JSON_REPORT = ROOT / "reports" / "evidence_type_consistency_audit.json"

ALLOWED_EVIDENCE_TYPES = {
    "fresh_run",
    "derived_summary",
    "scaffold",
    "infra_blocked",
    "replay",
    "external_official_harness",
}

MAIN_REPORTS = [
    ROOT / "reports" / "REPRESENTATIVE_VALIDATION_MATRIX.md",
    ROOT / "reports" / "FRAMEWORK_MATURITY_EVIDENCE_LEDGER.md",
    ROOT / "reports" / "DEFENSIVE_SECURITY_MINI_SUITE_STATUS.md",
    ROOT / "reports" / "SMALL_CANDIDATE_EVOLUTION_STATUS.md",
    ROOT / "reports" / "SWEBENCH_OFFICIAL_HARNESS_INFRA_UNBLOCK_STATUS.md",
    ROOT / "reports" / "RAPID_ADVANCEMENT_SPRINT_STATUS.md",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


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


def matrix_evidence_rows() -> list[dict[str, Any]]:
    payload = read_json(ROOT / "reports" / "representative_validation_matrix.json", {})
    rows = []
    for item in payload.get("rows", []):
        evidence_type = str(item.get("evidence_type") or "")
        rows.append(
            {
                "claim": item.get("claim"),
                "lane": item.get("lane"),
                "skill_package": item.get("skill_package"),
                "evidence_type": evidence_type,
                "allowed": evidence_type in ALLOWED_EVIDENCE_TYPES,
                "current_evidence": item.get("current_evidence"),
            }
        )
    return rows


def report_scan_rows() -> list[dict[str, Any]]:
    rows = []
    allowed_pattern = re.compile(r"\b(" + "|".join(re.escape(item) for item in sorted(ALLOWED_EVIDENCE_TYPES)) + r")\b")
    legacy_pattern = re.compile(r"\bderived\b")
    for path in MAIN_REPORTS:
        text = read_text(path)
        rows.append(
            {
                "report": str(path),
                "exists": path.exists(),
                "allowed_evidence_mentions": sorted(set(allowed_pattern.findall(text))),
                "legacy_or_disallowed_mentions": sorted(set(legacy_pattern.findall(text))),
            }
        )
    return rows


def boundary_checks() -> dict[str, Any]:
    matrix_text = read_text(ROOT / "reports" / "REPRESENTATIVE_VALIDATION_MATRIX.md").lower()
    sprint_text = read_text(ROOT / "reports" / "RAPID_ADVANCEMENT_SPRINT_STATUS.md").lower()
    swe_text = read_text(ROOT / "reports" / "SWEBENCH_OFFICIAL_HARNESS_INFRA_UNBLOCK_STATUS.md").lower()
    mini_text = read_text(ROOT / "reports" / "DEFENSIVE_SECURITY_MINI_SUITE_STATUS.md").lower()
    docs_text = read_text(ROOT / "docs" / "CLAIM_BOUNDARY.md").lower()
    all_text = "\n".join([matrix_text, sprint_text, swe_text, mini_text, docs_text])
    return {
        "infra_blocked_not_pass": "infra_blocked" in all_text and "not benchmark success" in all_text,
        "scaffold_not_fresh_run": "scaffold" in all_text and "fresh_run" in all_text,
        "swebench_not_used_for_secure_code_review": "does not support secure_code_review claims" in all_text
        or "must not be used to support `secure_code_review`" in all_text,
        "internal_deterministic_not_real_world_validity": "does not imply real-world vulnerability scanning" in all_text
        or "real-world security effectiveness" in all_text,
        "local_mini_suite_not_official_benchmark": "not an official autopatchbench" in all_text
        and "cyberseceval" in all_text,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Evidence Type Consistency Audit",
        "",
        f"Generated at: `{payload['generated_at']}`",
        "",
        "Allowed evidence types: `fresh_run`, `derived_summary`, `scaffold`, `infra_blocked`, `replay`, `external_official_harness`.",
        "",
        "## Representative Matrix Rows",
        "",
        "| Lane | Claim | Evidence type | Allowed | Evidence |",
        "|---|---|---|---:|---|",
    ]
    for row in payload["matrix_rows"]:
        lines.append(
            f"| {row['lane']} | {row['claim']} | {row['evidence_type']} | {row['allowed']} | {row['current_evidence']} |"
        )
    lines.extend(["", "## Main Report Scan", "", "| Report | Exists | Allowed mentions | Legacy/disallowed mentions |", "|---|---:|---|---|"])
    for row in payload["report_rows"]:
        lines.append(
            f"| {row['report']} | {row['exists']} | {', '.join(row['allowed_evidence_mentions']) or 'none'} | {', '.join(row['legacy_or_disallowed_mentions']) or 'none'} |"
        )
    lines.extend(["", "## Boundary Checks", ""])
    for key, value in payload["boundary_checks"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Decision", "", f"- Overall status: `{payload['overall_status']}`"])
    if payload["issues"]:
        lines.extend(["", "## Issues", ""])
        for issue in payload["issues"]:
            lines.append(f"- {issue}")
    return "\n".join(lines) + "\n"


def main() -> int:
    matrix_rows = matrix_evidence_rows()
    report_rows = report_scan_rows()
    checks = boundary_checks()
    issues: list[str] = []
    for row in matrix_rows:
        if not row["allowed"]:
            issues.append(f"matrix row uses disallowed evidence type `{row['evidence_type']}` for {row['claim']}")
    for row in report_rows:
        if row["legacy_or_disallowed_mentions"]:
            issues.append(f"{row['report']} contains legacy evidence label mentions: {row['legacy_or_disallowed_mentions']}")
    for key, value in checks.items():
        if not value:
            issues.append(f"boundary check failed: {key}")
    payload = {
        "generated_at": utc_now(),
        "allowed_evidence_types": sorted(ALLOWED_EVIDENCE_TYPES),
        "matrix_rows": matrix_rows,
        "report_rows": report_rows,
        "boundary_checks": checks,
        "issues": issues,
        "overall_status": "pass" if not issues else "needs_fix",
    }
    write_json(JSON_REPORT, payload)
    write_text(REPORT, render_markdown(payload))
    print(json.dumps({"status": payload["overall_status"], "issues": len(issues), "report": str(REPORT)}, indent=2))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
