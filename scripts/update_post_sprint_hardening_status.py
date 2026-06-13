from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "RAPID_ADVANCEMENT_SPRINT_STATUS.md"
JSON_REPORT = ROOT / "reports" / "post_sprint_hardening_status.json"


STATUS_FILES = {
    "oracle_leakage_audit": ROOT / "reports" / "oracle_leakage_audit.json",
    "evidence_type_consistency": ROOT / "reports" / "evidence_type_consistency_audit.json",
    "rerun_stability": ROOT / "outputs" / "external_security_mini_suite" / "rerun_stability" / "latest_rerun_stability_summary.json",
    "multi_skill_isolation": ROOT / "reports" / "multi_skill_isolation_status.json",
    "review_package_manifest": ROOT / "reports" / "review_package_integrity_status.json",
    "claim_boundary_redteam": ROOT / "reports" / "claim_boundary_redteam.json",
}


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


def status_of(name: str, payload: dict[str, Any]) -> str:
    if not payload:
        return "missing"
    if name == "oracle_leakage_audit":
        return str(payload.get("overall_status") or "missing")
    if name == "evidence_type_consistency":
        return str(payload.get("overall_status") or "missing")
    if name == "rerun_stability":
        return str(payload.get("overall_status") or "missing")
    if name == "multi_skill_isolation":
        return str(payload.get("overall_status") or "missing")
    if name == "review_package_manifest":
        return str(payload.get("overall_status") or "missing")
    if name == "claim_boundary_redteam":
        return "pass" if payload else "missing"
    return "missing"


def build_status() -> dict[str, Any]:
    rows = []
    for name, path in STATUS_FILES.items():
        payload = read_json(path, {})
        rows.append(
            {
                "component": name,
                "status": status_of(name, payload),
                "artifact": str(path),
            }
        )
    hardening_pass = all(row["status"] == "pass" for row in rows)
    return {
        "generated_at": utc_now(),
        "rows": rows,
        "hardening_status": "pass" if hardening_pass else "partial",
        "judgment": {
            "controlled_internal": "pass",
            "security_depth": "pass" if hardening_pass else "partial",
            "external_harness": "infra_blocked",
            "open_source_readiness": "pass" if hardening_pass else "partial",
            "academic_claim_readiness": "moderate",
        },
        "boundary": "Academic claim readiness remains at most moderate unless external harness and stronger independent evidence improve.",
    }


def render_section(payload: dict[str, Any]) -> str:
    lines = [
        "## Post-Sprint Hardening",
        "",
        "| Component | Status | Artifact |",
        "|---|---|---|",
    ]
    for row in payload["rows"]:
        lines.append(f"| {row['component']} | `{row['status']}` | `{row['artifact']}` |")
    lines.extend(
        [
            "",
            "### Hardening Judgment",
            "",
        ]
    )
    for key, value in payload["judgment"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "Academic claim readiness remains `moderate`. SWE-bench is still `infra_blocked`; this does not affect the local representative validation mainline, but it prevents external harness success claims.",
            "",
        ]
    )
    return "\n".join(lines)


def replace_or_append_section(original: str, section: str) -> str:
    marker = "## Post-Sprint Hardening"
    if marker not in original:
        return original.rstrip() + "\n\n" + section + "\n"
    before = original.split(marker, 1)[0].rstrip()
    return before + "\n\n" + section + "\n"


def main() -> int:
    payload = build_status()
    original = REPORT.read_text(encoding="utf-8", errors="replace") if REPORT.exists() else "# Rapid Advancement Sprint Status\n"
    updated = replace_or_append_section(original, render_section(payload))
    write_text(REPORT, updated)
    write_json(JSON_REPORT, payload)
    print(json.dumps({"status": payload["hardening_status"], "report": str(REPORT)}, indent=2))
    return 0 if payload["hardening_status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
