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
from scripts.run_non_oracle_validation import classify_non_oracle, select_representative_cases  # noqa: E402


SUITE_PATH = ROOT / "data" / "external_security_mini_suite" / "holdout_cases.json"
OUTPUT_ROOT = ROOT / "outputs" / "live_llm_validation"
REPORT = ROOT / "reports" / "LIVE_LLM_VALIDATION_STATUS.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def api_key_present() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


def classify_live_row_from_failure(case_id: str, task_family: str, out_dir: Path, exc: Exception) -> dict[str, Any]:
    metadata = read_json(out_dir / "agent" / "backend_metadata.json", {})
    raw_response = (out_dir / "agent" / "raw_response.txt").read_text(encoding="utf-8", errors="replace") if (out_dir / "agent" / "raw_response.txt").exists() else ""
    failure_reason = str(metadata.get("failure_reason") or exc)
    error_text = str(metadata.get("error") or exc)
    status = "failed"
    blocked_reason = None
    if failure_reason in {"api_error", "env_missing"}:
        status = "blocked"
        blocked_reason = f"live_llm_configured_but_api_blocked:{failure_reason}"
    elif failure_reason == "network_or_parse_error" and not raw_response.strip():
        status = "blocked"
        blocked_reason = "live_llm_configured_but_api_blocked:network_or_timeout"
    elif "timed out" in error_text.lower() or "urlopen" in error_text.lower():
        status = "blocked"
        blocked_reason = "live_llm_configured_but_api_blocked:network_or_timeout"
    return {
        "case_id": case_id,
        "task_family": task_family,
        "backend": "live_llm_text",
        "status": status,
        "blocked_reason": blocked_reason,
        "activated_capability_group": None,
        "verifier_result": "fail" if status == "failed" else None,
        "verifier_feedback_type": None,
        "score": None,
        "false_positive_count": None,
        "discrepancy_vs_offline_deterministic": "backend_error" if status == "failed" else "not_run",
        "failure_reason": failure_reason if status == "failed" else None,
        "artifact_dir": str(out_dir),
    }


def run_live_case(
    *,
    case_payload: dict[str, Any],
    active_spec: mini.VariantSpec,
    output_root: Path,
    active_pointer: dict[str, Any],
    offline_summary: dict[str, Any],
    base_url: str,
    model: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    case_id = str(case_payload["case_id"])
    agent_case = mini.make_agent_visible_case(case_payload)
    out_dir = output_root / "cases" / case_id / "live_llm_text"
    if not api_key_present():
        return {
            "case_id": case_id,
            "task_family": agent_case.task_family,
            "backend": "live_llm_text",
            "status": "blocked",
            "blocked_reason": "missing_env:OPENAI_API_KEY",
            "activated_capability_group": None,
            "verifier_result": None,
            "false_positive_count": None,
            "discrepancy_vs_offline_deterministic": "not_run",
            "failure_reason": None,
            "artifact_dir": None,
        }
    try:
        summary = mini.run_variant(
            case_payload=case_payload,
            agent_case=agent_case,
            verifier_only=case_payload["verifier_only"],
            spec=active_spec,
            backend="live_llm_text",
            output_dir=out_dir,
            active_pointer_snapshot=active_pointer,
            runner_metadata={
                "base_url": base_url,
                "model": model,
                "temperature": 0.0,
                "timeout": timeout_seconds,
                "task_label": f"secure_code_review:{agent_case.task_family}",
                "contract_mode": "strict",
                "prompt_addendum": "Use no exploit steps. Defensive review only. If no active capabilities are allowed, return an empty findings array.",
            },
        )
        discrepancy = []
        if summary.get("pass") != offline_summary.get("pass"):
            discrepancy.append("pass_mismatch")
        if summary.get("feedback_type") != offline_summary.get("feedback_type"):
            discrepancy.append("feedback_type_mismatch")
        if summary.get("false_positive_count") != offline_summary.get("false_positive_count"):
            discrepancy.append("false_positive_count_mismatch")
        return {
            "case_id": case_id,
            "task_family": agent_case.task_family,
            "backend": "live_llm_text",
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
    except Exception as exc:  # noqa: BLE001 - failures are preserved as evidence.
        write_text(out_dir / "blocked_or_failed_trace.txt", traceback.format_exc())
        return classify_live_row_from_failure(case_id, agent_case.task_family, out_dir, exc)


def classify_live(rows: list[dict[str, Any]], case_count: int) -> dict[str, Any]:
    base = classify_non_oracle([{**row, "backend": "non_oracle_local_semantic"} for row in rows], case_count)
    return {
        "live_llm_execution": base["non_oracle_execution"],
        "live_llm_effectiveness": base["non_oracle_effectiveness"],
        "live_llm_behavior": base["non_oracle_behavior"],
        "verifier_pass_rows": base["non_oracle_verifier_pass_rows"],
        "verifier_fail_rows": base["non_oracle_verifier_fail_rows"],
        "discrepancy_rows": base["non_oracle_discrepancy_rows"],
    }


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Live LLM Validation Status",
        "",
        f"Generated at: `{payload['generated_at']}`",
        "",
        "This run checks the installed secure_code_review package through the OpenAI-compatible `live_llm_text` backend. API keys are not written to artifacts.",
        "",
        "## Configuration",
        "",
        f"- Base URL configured: `{payload['config']['base_url_configured']}`",
        f"- Model: `{payload['config']['model']}`",
        f"- API key present: `{payload['config']['api_key_present']}`",
        "",
        "## Summary",
        "",
        f"- Selected cases: `{payload['case_count']}`",
        f"- `live_llm_execution`: `{payload['live_llm_execution']}`",
        f"- `live_llm_effectiveness`: `{payload['live_llm_effectiveness']}`",
        f"- `live_llm_behavior`: `{payload['live_llm_behavior']}`",
        f"- Verifier pass rows: `{payload['verifier_pass_rows']}`",
        f"- Verifier fail rows: `{payload['verifier_fail_rows']}`",
        f"- Discrepancy rows: `{payload['discrepancy_rows']}`",
        "",
        "## Rows",
        "",
        "| Case | Task family | Status | Activated group | Verifier | FP count | Discrepancy | Blocked/failure reason |",
        "|---|---|---|---|---|---:|---|---|",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['case_id']} | {row['task_family']} | {row['status']} | {row.get('activated_capability_group')} | "
            f"{row.get('verifier_result')} | {row.get('false_positive_count')} | {row.get('discrepancy_vs_offline_deterministic')} | "
            f"{row.get('blocked_reason') or row.get('failure_reason') or 'none'} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Verifier was not relaxed.",
            "- Verifier-only expected findings, evidence spans, and clean labels were not exposed to the runner.",
            "- Malformed JSON, schema errors, unsupported evidence, and false positives remain failures.",
            "- API/network/model blocks are infrastructure/configuration blocks, not model success.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run installed secure_code_review through live_llm_text on representative holdout cases.")
    parser.add_argument("--installed", default="secure_code_review")
    parser.add_argument("--suite", default=str(SUITE_PATH))
    parser.add_argument("--output-dir", default=str(OUTPUT_ROOT))
    parser.add_argument("--base-url", default=os.environ.get("OPENAI_BASE_URL") or "https://api.deepseek.com")
    parser.add_argument("--model", default=os.environ.get("MODEL") or os.environ.get("OPENAI_MODEL") or "deepseek-v4-flash")
    parser.add_argument("--timeout-seconds", type=float, default=45.0)
    args = parser.parse_args(argv)

    suite = read_json(Path(args.suite), {})
    cases = select_representative_cases(suite.get("cases", []))
    specs, active_pointer, unavailable = mini.build_variant_specs(args.installed)
    active_spec = next(spec for spec in specs if spec.name == "active_installed")
    output_root = Path(args.output_dir)
    offline_by_case: dict[str, dict[str, Any]] = {}
    rows: list[dict[str, Any]] = []
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
    for case_payload in cases:
        case_id = str(case_payload["case_id"])
        rows.append(
            run_live_case(
                case_payload=case_payload,
                active_spec=active_spec,
                output_root=output_root,
                active_pointer=active_pointer,
                offline_summary=offline_by_case[case_id],
                base_url=args.base_url,
                model=args.model,
                timeout_seconds=args.timeout_seconds,
            )
        )
    live_status = classify_live(rows, len(cases))
    payload = {
        "run_id": "live_llm_validation_secure_code_review",
        "generated_at": utc_now(),
        "installed_skill": args.installed,
        "suite_path": str(Path(args.suite)),
        "output_root": str(output_root),
        "case_count": len(cases),
        "selected_cases": [str(case["case_id"]) for case in cases],
        "unavailable_variants": unavailable,
        "config": {
            "base_url_configured": bool(args.base_url),
            "model": args.model,
            "api_key_present": api_key_present(),
            "timeout_seconds": args.timeout_seconds,
        },
        "offline_baseline": offline_by_case,
        "rows": rows,
        **live_status,
        "claim_boundary": "live LLM validation remains bounded local holdout evidence; it is not an external benchmark result.",
    }
    write_json(output_root / "live_llm_validation_summary.json", payload)
    write_text(REPORT, render_report(payload))
    print(json.dumps({"summary": str(output_root / "live_llm_validation_summary.json"), "report": str(REPORT), **live_status}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
