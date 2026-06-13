from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
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
OUTPUT_ROOT = ROOT / "outputs" / "non_oracle_validation"
REPORT = ROOT / "reports" / "NON_ORACLE_VALIDATION_STATUS.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def select_representative_cases(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    families = [
        "upload_security",
        "config_security",
        "auth_access_control",
        "api_or_code_review",
        "clean_business_logic_review",
        "dependency_version_risk",
    ]
    selected = []
    for family in families:
        match = next((case for case in cases if case["agent_visible"]["task_family"] == family), None)
        if match is not None:
            selected.append(match)
    return selected


def live_llm_available() -> tuple[bool, str | None]:
    missing = [name for name in ("OPENAI_BASE_URL", "OPENAI_API_KEY") if not os.environ.get(name)]
    if not (os.environ.get("MODEL") or os.environ.get("OPENAI_MODEL")):
        missing.append("MODEL_or_OPENAI_MODEL")
    if missing:
        return False, "missing_env:" + ",".join(missing)
    return True, None


def run_backend_case(
    *,
    case_payload: dict[str, Any],
    active_spec: mini.VariantSpec,
    backend: str,
    output_root: Path,
    active_pointer: dict[str, Any],
    offline_summary: dict[str, Any] | None,
) -> dict[str, Any]:
    case_id = str(case_payload["case_id"])
    agent_case = mini.make_agent_visible_case(case_payload)
    verifier_only = case_payload["verifier_only"]
    if backend == "live_llm_text":
        available, reason = live_llm_available()
        if not available:
            return {
                "case_id": case_id,
                "task_family": agent_case.task_family,
                "backend": backend,
                "status": "blocked",
                "blocked_reason": reason,
                "activated_capability_group": None,
                "verifier_result": None,
                "false_positive_count": None,
                "discrepancy_vs_offline_deterministic": "not_run",
                "failure_reason": None,
                "artifact_dir": None,
            }
    try:
        out_dir = output_root / "cases" / case_id / backend
        summary = mini.run_variant(
            case_payload=case_payload,
            agent_case=agent_case,
            verifier_only=verifier_only,
            spec=active_spec,
            backend=backend,
            output_dir=out_dir,
            active_pointer_snapshot=active_pointer,
        )
        offline_pass = offline_summary.get("pass") if offline_summary else None
        offline_feedback = offline_summary.get("feedback_type") if offline_summary else None
        discrepancy = []
        if offline_summary:
            if summary.get("pass") != offline_pass:
                discrepancy.append("pass_mismatch")
            if summary.get("feedback_type") != offline_feedback:
                discrepancy.append("feedback_type_mismatch")
            if summary.get("false_positive_count") != offline_summary.get("false_positive_count"):
                discrepancy.append("false_positive_count_mismatch")
        return {
            "case_id": case_id,
            "task_family": agent_case.task_family,
            "backend": backend,
            "status": "completed",
            "blocked_reason": None,
            "activated_capability_group": summary.get("activated_capability_group"),
            "verifier_result": "pass" if summary.get("pass") else "fail",
            "verifier_feedback_type": summary.get("feedback_type"),
            "score": summary.get("score"),
            "false_positive_count": summary.get("false_positive_count"),
            "discrepancy_vs_offline_deterministic": "none" if not discrepancy else ",".join(discrepancy),
            "failure_reason": None if summary.get("pass") else summary.get("feedback_type"),
            "artifact_dir": str(out_dir),
        }
    except Exception as exc:  # noqa: BLE001 - this is an audit runner; failures become evidence.
        error_dir = output_root / "cases" / case_id / backend
        write_text(error_dir / "blocked_or_failed_trace.txt", traceback.format_exc())
        return {
            "case_id": case_id,
            "task_family": agent_case.task_family,
            "backend": backend,
            "status": "failed",
            "blocked_reason": None,
            "activated_capability_group": None,
            "verifier_result": "fail",
            "false_positive_count": None,
            "discrepancy_vs_offline_deterministic": "backend_error",
            "failure_reason": str(exc),
            "artifact_dir": str(error_dir),
        }


def classify_non_oracle(rows: list[dict[str, Any]], case_count: int) -> dict[str, Any]:
    non_oracle_rows = [row for row in rows if row["backend"] == "non_oracle_local_semantic"]
    completed = [row for row in non_oracle_rows if row["status"] == "completed"]
    blocked = [row for row in non_oracle_rows if row["status"] == "blocked"]
    failed = [row for row in non_oracle_rows if row["status"] == "failed"]
    verifier_pass = [row for row in completed if row.get("verifier_result") == "pass"]
    discrepancies = [
        row
        for row in completed
        if row.get("discrepancy_vs_offline_deterministic") not in {None, "", "none"}
    ]
    verifier_fail = [row for row in completed if row.get("verifier_result") != "pass"]
    if completed and len(completed) == case_count:
        execution = "pass"
    elif completed:
        execution = "partial"
    elif blocked:
        execution = "blocked"
    elif failed:
        execution = "fail"
    else:
        execution = "blocked"
    if completed and len(verifier_pass) == len(completed) and not discrepancies:
        effectiveness = "pass"
    elif completed and verifier_pass and (verifier_fail or discrepancies):
        effectiveness = "partial"
    elif completed and (verifier_fail or discrepancies):
        effectiveness = "discrepancy_detected"
    elif blocked:
        effectiveness = "blocked"
    else:
        effectiveness = "fail"
    if execution == "pass" and effectiveness == "pass":
        behavior = "pass"
    elif execution in {"pass", "partial"} and effectiveness in {"partial", "discrepancy_detected"}:
        behavior = "partial"
    elif execution == "blocked" or effectiveness == "blocked":
        behavior = "blocked"
    else:
        behavior = "fail"
    return {
        "non_oracle_execution": execution,
        "non_oracle_effectiveness": effectiveness,
        "non_oracle_behavior": behavior,
        "non_oracle_verifier_pass_rows": len(verifier_pass),
        "non_oracle_verifier_fail_rows": len(verifier_fail),
        "non_oracle_discrepancy_rows": len(discrepancies),
    }


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Non-Oracle Validation Status",
        "",
        f"Generated at: `{payload['generated_at']}`",
        "",
        "This validation checks whether installed secure_code_review behavior is merely offline-deterministic/verifier aligned or also observable through a non-oracle backend. Live LLM unavailability is reported as blocked, not as model failure.",
        "",
        "## Summary",
        "",
        f"- Selected cases: `{payload['case_count']}`",
        f"- Non-oracle completed rows: `{payload['non_oracle_completed_rows']}`",
        f"- Live LLM status: `{payload['live_llm_status']}`",
        f"- Non-oracle execution: `{payload['non_oracle_execution']}`",
        f"- Non-oracle effectiveness: `{payload['non_oracle_effectiveness']}`",
        f"- Non-oracle behavior: `{payload['non_oracle_behavior']}`",
        f"- Overall status: `{payload['overall_status']}`",
        "",
        "Execution success means the backend ran. Effectiveness requires verifier pass with no discrepancy against the offline deterministic reference. These are intentionally separated.",
        "",
        "## Rows",
        "",
        "| Case | Task family | Backend | Status | Activated group | Verifier | FP count | Discrepancy | Blocked/failure reason |",
        "|---|---|---|---|---|---|---:|---|---|",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['case_id']} | {row['task_family']} | {row['backend']} | {row['status']} | "
            f"{row.get('activated_capability_group')} | {row.get('verifier_result')} | {row.get('false_positive_count')} | "
            f"{row.get('discrepancy_vs_offline_deterministic')} | {row.get('blocked_reason') or row.get('failure_reason') or 'none'} |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run non-oracle validation on representative installed secure_code_review cases.")
    parser.add_argument("--installed", default="secure_code_review")
    parser.add_argument("--suite", default=str(SUITE_PATH))
    parser.add_argument("--output-dir", default=str(OUTPUT_ROOT))
    parser.add_argument("--backends", default="non_oracle_local_semantic,live_llm_text")
    args = parser.parse_args(argv)

    suite = read_json(Path(args.suite), {})
    cases = select_representative_cases(suite.get("cases", []))
    specs, active_pointer, unavailable = mini.build_variant_specs(args.installed)
    active_spec = next(spec for spec in specs if spec.name == "active_installed")
    output_root = Path(args.output_dir)
    rows: list[dict[str, Any]] = []
    offline_by_case: dict[str, dict[str, Any]] = {}
    for case_payload in cases:
        case_id = str(case_payload["case_id"])
        offline_by_case[case_id] = mini.run_variant(
            case_payload=case_payload,
            agent_case=mini.make_agent_visible_case(case_payload),
            verifier_only=case_payload["verifier_only"],
            spec=active_spec,
            backend="offline_deterministic",
            output_dir=output_root / "cases" / case_id / "offline_deterministic",
            active_pointer_snapshot=active_pointer,
        )
    for backend in [item.strip() for item in args.backends.split(",") if item.strip()]:
        for case_payload in cases:
            case_id = str(case_payload["case_id"])
            rows.append(
                run_backend_case(
                    case_payload=case_payload,
                    active_spec=active_spec,
                    backend=backend,
                    output_root=output_root,
                    active_pointer=active_pointer,
                    offline_summary=offline_by_case.get(case_id),
                )
            )
    live_rows = [row for row in rows if row["backend"] == "live_llm_text"]
    non_oracle_rows = [row for row in rows if row["backend"] == "non_oracle_local_semantic"]
    non_oracle_status = classify_non_oracle(rows, len(cases))
    payload = {
        "run_id": "non_oracle_validation_secure_code_review",
        "generated_at": utc_now(),
        "installed_skill": args.installed,
        "suite_path": str(Path(args.suite)),
        "output_root": str(output_root),
        "case_count": len(cases),
        "selected_cases": [str(case["case_id"]) for case in cases],
        "unavailable_variants": unavailable,
        "offline_baseline": offline_by_case,
        "rows": rows,
        "non_oracle_completed_rows": sum(1 for row in non_oracle_rows if row["status"] == "completed"),
        "live_llm_status": "not_requested"
        if not live_rows
        else ("blocked" if all(row["status"] == "blocked" for row in live_rows) else "attempted"),
        **non_oracle_status,
        "overall_status": non_oracle_status["non_oracle_behavior"],
        "claim_boundary": "non-oracle/local semantic evidence is still local; it does not prove real-world security validity.",
    }
    write_json(output_root / "non_oracle_validation_summary.json", payload)
    write_text(REPORT, render_report(payload))
    print(json.dumps({"summary": str(output_root / "non_oracle_validation_summary.json"), "report": str(REPORT), "overall_status": payload["overall_status"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
