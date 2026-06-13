from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from skill_deployment.evidence import write_json, write_text  # noqa: E402

import scripts.run_defensive_security_mini_suite as mini  # noqa: E402


SUITE_PATH = ROOT / "data" / "external_security_mini_suite" / "cases.json"
OUTPUT_ROOT = ROOT / "outputs" / "external_security_mini_suite" / "rerun_stability"
REPORT = ROOT / "reports" / "MINI_SUITE_RERUN_STABILITY_STATUS.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def select_cases(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    upload = next(case for case in cases if case["agent_visible"]["task_family"] == "upload_security")
    selected.append(upload)
    mid = next(case for case in cases if case["agent_visible"]["task_family"] in {"config_security", "auth_access_control", "api_or_code_review"})
    selected.append(mid)
    clean = next(case for case in cases if case["verifier_only"].get("clean_or_negative"))
    selected.append(clean)
    limitation = next((case for case in cases if case["verifier_only"].get("unsupported_limitation")), None)
    if limitation is not None:
        selected.append(limitation)
    return selected


def original_by_case() -> dict[str, dict[str, Any]]:
    summary = read_json(ROOT / "outputs" / "external_security_mini_suite" / "mini_suite_summary.json", {})
    return {str(row["case_id"]): row for row in summary.get("case_summaries", [])}


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Mini-Suite Rerun Stability Status",
        "",
        f"Generated at: `{payload['generated_at']}`",
        f"Rerun id: `{payload['rerun_id']}`",
        f"Output root: `{payload['output_root']}`",
        "",
        "## Fresh Rerun Command",
        "",
        "```powershell",
        "python scripts\\run_mini_suite_rerun_stability.py",
        "```",
        "",
        "## Results",
        "",
        "| Case | Original status | Rerun status | Stable | Active group | FP count | Note |",
        "|---|---|---|---:|---|---:|---|",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['case_id']} | {row['original_status']} | {row['rerun_status']} | {row['stable']} | "
            f"{row['activated_capability_group']} | {row['false_positive_count']} | {row['note']} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Overall status: `{payload['overall_status']}`",
            f"- Clean negative false-positive control: `{payload['clean_negative_status']}`",
            f"- Unsupported limitation retained: `{payload['unsupported_limitation_status']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    suite = read_json(SUITE_PATH, {})
    cases = select_cases(suite.get("cases", []))
    specs, active_pointer, unavailable = mini.build_variant_specs("secure_code_review")
    active_spec = next(spec for spec in specs if spec.name == "active_installed")
    rerun_id = run_stamp()
    output_root = OUTPUT_ROOT / rerun_id
    original = original_by_case()
    rows = []
    for case_payload in cases:
        agent_case = mini.make_agent_visible_case(case_payload)
        case_dir = output_root / "cases" / str(case_payload["case_id"]) / "active_installed"
        variant = mini.run_variant(
            case_payload=case_payload,
            agent_case=agent_case,
            verifier_only=case_payload["verifier_only"],
            spec=active_spec,
            backend="offline_deterministic",
            output_dir=case_dir,
            active_pointer_snapshot=active_pointer,
        )
        status = mini.case_status(case_payload, {"active_installed": variant})
        orig = original.get(str(case_payload["case_id"]), {})
        is_clean = bool(case_payload["verifier_only"].get("clean_or_negative"))
        is_limitation = bool(case_payload["verifier_only"].get("unsupported_limitation"))
        stable = (
            status.get("status") == orig.get("status")
            and status.get("activated_capability_group") == orig.get("activated_capability_group")
            and status.get("false_positive_count") == orig.get("false_positive_count")
        )
        note = "ok"
        if is_clean and status.get("false_positive_count") != 0:
            stable = False
            note = "clean negative false positive regression"
        if is_limitation and status.get("status") != "unsupported_limitation":
            stable = False
            note = "unsupported limitation was absorbed or changed"
        rows.append(
            {
                "case_id": status["case_id"],
                "original_status": orig.get("status", "missing"),
                "rerun_status": status["status"],
                "stable": stable,
                "activated_capability_group": status.get("activated_capability_group"),
                "expected_capability_group": status.get("expected_capability_group"),
                "capability_group_correct": status.get("capability_group_correct"),
                "false_positive_count": status.get("false_positive_count"),
                "artifact_dir": str(case_dir),
                "note": note,
            }
        )
    clean_rows = [row for row in rows if row["case_id"] == "mini_clean_out_of_scope_001"]
    limitation_rows = [row for row in rows if row["case_id"] == "mini_dependency_version_risk_001"]
    payload = {
        "generated_at": utc_now(),
        "rerun_id": rerun_id,
        "output_root": str(output_root),
        "unavailable_variants": unavailable,
        "selected_cases": [str(case["case_id"]) for case in cases],
        "rows": rows,
        "clean_negative_status": "pass" if clean_rows and clean_rows[0]["false_positive_count"] == 0 else "fail",
        "unsupported_limitation_status": "retained" if limitation_rows and limitation_rows[0]["rerun_status"] == "unsupported_limitation" else "missing_or_changed",
    }
    payload["overall_status"] = (
        "pass"
        if all(row["stable"] for row in rows)
        and payload["clean_negative_status"] == "pass"
        and payload["unsupported_limitation_status"] == "retained"
        else "fail"
    )
    write_json(output_root / "rerun_stability_summary.json", payload)
    write_json(OUTPUT_ROOT / "latest_rerun_stability_summary.json", payload)
    write_text(REPORT, render_report(payload))
    print(json.dumps({"status": payload["overall_status"], "report": str(REPORT), "output_root": str(output_root)}, indent=2))
    return 0 if payload["overall_status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
