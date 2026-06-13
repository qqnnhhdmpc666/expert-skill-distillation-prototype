from __future__ import annotations

import argparse
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


SUITE_PATH = ROOT / "data" / "external_security_mini_suite" / "holdout_cases.json"
OUTPUT_ROOT = ROOT / "outputs" / "external_security_mini_suite" / "holdout"
REPORT = ROOT / "reports" / "HOLDOUT_SECURITY_MINI_SUITE_STATUS.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def has_agent_visible_oracle_leak(case_payload: dict[str, Any]) -> bool:
    visible_text = json.dumps(case_payload.get("agent_visible", {}), ensure_ascii=False, sort_keys=True)
    verifier = case_payload.get("verifier_only", {})
    forbidden_keys = {
        "expected_capability_group",
        "expected_capabilities",
        "expected_security_finding",
        "expected_evidence_span",
        "clean_or_negative",
        "unsupported_limitation",
    }
    if any(key in case_payload.get("agent_visible", {}) for key in forbidden_keys):
        return True
    expected_finding = str(verifier.get("expected_security_finding") or "").strip()
    return bool(expected_finding and expected_finding in visible_text)


def run_suite(*, installed: str, backend: str, suite_path: Path, output_root: Path) -> dict[str, Any]:
    suite = read_json(suite_path, {})
    integrity = mini.version_integrity(installed)
    specs, active_pointer_snapshot, unavailable = mini.build_variant_specs(installed)
    case_summaries: list[dict[str, Any]] = []
    variant_results: dict[str, dict[str, dict[str, Any]]] = {}
    leakage_rows: list[dict[str, Any]] = []
    for case_payload in suite.get("cases", []):
        case_id = str(case_payload["case_id"])
        leakage = has_agent_visible_oracle_leak(case_payload)
        leakage_rows.append({"case_id": case_id, "leakage_found": leakage})
        agent_case = mini.make_agent_visible_case(case_payload)
        verifier_only = case_payload["verifier_only"]
        case_dir = output_root / "cases" / case_id
        write_json(
            case_dir / "agent_visible_case.json",
            {
                "case_id": case_id,
                "agent_visible": case_payload["agent_visible"],
                "minimal_defensive_patch_or_recommendation": case_payload["minimal_defensive_patch_or_recommendation"],
                "forbidden_behavior": case_payload["forbidden_behavior"],
                "oracle_fields_visible_to_runner": False,
                "holdout": True,
            },
        )
        write_json(
            case_dir / "verifier_only_oracle.redacted_summary.json",
            {
                "case_id": case_id,
                "expected_capability_count": len(verifier_only.get("expected_capabilities", [])),
                "expected_capability_group": verifier_only.get("expected_capability_group"),
                "clean_or_negative": bool(verifier_only.get("clean_or_negative")),
                "unsupported_limitation": bool(verifier_only.get("unsupported_limitation")),
                "note": "Full oracle fields are not written into runner inputs.",
            },
        )
        variant_results[case_id] = {}
        for spec in specs:
            variant_results[case_id][spec.name] = mini.run_variant(
                case_payload=case_payload,
                agent_case=agent_case,
                verifier_only=verifier_only,
                spec=spec,
                backend=backend,
                output_dir=case_dir / spec.name,
                active_pointer_snapshot=active_pointer_snapshot,
            )
        case_summaries.append(mini.case_status(case_payload, variant_results[case_id]))

    positive_rows = [
        row
        for row in case_summaries
        if not row["unsupported_limitation"] and not str(row["status"]).startswith("false_positive_control")
    ]
    negative_rows = [row for row in case_summaries if str(row["status"]).startswith("false_positive_control")]
    limitation_rows = [row for row in case_summaries if row["unsupported_limitation"]]
    payload = {
        "run_id": "holdout_security_mini_suite_installed_runtime",
        "generated_at": utc_now(),
        "installed_skill": installed,
        "backend": backend,
        "suite_path": str(suite_path),
        "output_root": str(output_root),
        "version_integrity": integrity,
        "unavailable_variants": unavailable,
        "fresh_case_count": len(case_summaries),
        "positive_security_effective_pass_count": sum(1 for row in positive_rows if row["status"] == "pass"),
        "false_positive_control_status": "pass" if negative_rows and all(row["false_positive_count"] == 0 for row in negative_rows) else "fail",
        "unsupported_limitation_status": "retained" if limitation_rows else "missing",
        "oracle_leakage_status": "pass" if not any(row["leakage_found"] for row in leakage_rows) else "fail",
        "leakage_rows": leakage_rows,
        "case_summaries": case_summaries,
        "claim_boundary": "local holdout defensive evidence; not official CyberSecEval/AutoPatchBench/CVE-Bench",
    }
    write_json(output_root / "holdout_summary.json", payload)
    write_text(REPORT, render_report(payload))
    return payload


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Holdout Security Mini-Suite Status",
        "",
        f"Generated at: `{payload['generated_at']}`",
        "",
        "This is local holdout defensive evidence. It is not an official CyberSecEval, AutoPatchBench, or CVE-Bench run.",
        "",
        "## Summary",
        "",
        f"- Fresh holdout cases: `{payload['fresh_case_count']}`",
        f"- Positive effective pass count: `{payload['positive_security_effective_pass_count']}`",
        f"- Clean negative false-positive control: `{payload['false_positive_control_status']}`",
        f"- Unsupported limitation: `{payload['unsupported_limitation_status']}`",
        f"- Oracle leakage status: `{payload['oracle_leakage_status']}`",
        "",
        "## Case Results",
        "",
        "| Case | Task family | Status | Active group | Expected group | Group correct | FP count |",
        "|---|---|---|---|---|---:|---:|",
    ]
    for row in payload["case_summaries"]:
        lines.append(
            f"| {row['case_id']} | {row['task_family']} | {row['status']} | {row.get('activated_capability_group')} | "
            f"{row.get('expected_capability_group')} | {row.get('capability_group_correct')} | {row.get('false_positive_count')} |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run installed secure_code_review on local holdout defensive cases.")
    parser.add_argument("--installed", default="secure_code_review")
    parser.add_argument("--backend", default="offline_deterministic")
    parser.add_argument("--suite", default=str(SUITE_PATH))
    parser.add_argument("--output-dir", default=str(OUTPUT_ROOT))
    args = parser.parse_args(argv)
    payload = run_suite(installed=args.installed, backend=args.backend, suite_path=Path(args.suite), output_root=Path(args.output_dir))
    print(
        json.dumps(
            {
                "summary": str(Path(args.output_dir) / "holdout_summary.json"),
                "report": str(REPORT),
                "fresh_case_count": payload["fresh_case_count"],
                "false_positive_control_status": payload["false_positive_control_status"],
                "unsupported_limitation_status": payload["unsupported_limitation_status"],
            },
            indent=2,
        )
    )
    return 0 if payload["fresh_case_count"] >= 6 and payload["oracle_leakage_status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
