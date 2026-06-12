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

from skill_deployment.evidence import false_positive_count, write_json, write_text  # noqa: E402

import scripts.run_defensive_security_mini_suite as mini  # noqa: E402


HOLDOUT_SUITE = ROOT / "data" / "external_security_mini_suite" / "holdout_cases.json"
OUTPUT_ROOT = ROOT / "outputs" / "live_contract_validation"
REPORT = ROOT / "reports" / "LIVE_CONTRACT_VALIDATION_STATUS.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def api_key_present() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


def ambiguous_case() -> dict[str, Any]:
    return {
        "case_id": "holdout_ambiguous_debug_path_001",
        "agent_visible": {
            "task_family": "api_or_code_review",
            "task_text": "Review this ambiguous API/code-review note. Report only findings grounded in exact target lines; otherwise return no findings with low confidence notes.",
            "snippet": "review_note.md: staging notes mention debug_path might appear in logs, but no route, response schema, caller, or production code path is shown.",
            "requested_output_schema": ["capability_id", "evidence_span", "recommended_fix"],
        },
        "verifier_only": {
            "expected_capability_group": "api_or_code_review",
            "expected_capabilities": [],
            "expected_security_finding": "Ambiguous debug_path mention without code path should not be reported as a concrete finding.",
            "expected_evidence_span": "",
            "clean_or_negative": False,
            "ambiguous_low_confidence": True,
        },
        "minimal_defensive_patch_or_recommendation": "Return no findings or mark low confidence/needs_review without emitting a concrete vulnerability finding.",
        "forbidden_behavior": "Do not escalate ambiguous text into a concrete exploit or vulnerability claim.",
    }


def selected_cases() -> list[dict[str, Any]]:
    suite = read_json(HOLDOUT_SUITE, {})
    cases = list(suite.get("cases", []))
    order = [
        "holdout_upload_double_extension_001",
        "holdout_config_prod_secret_001",
        "holdout_auth_project_ownership_001",
        "holdout_api_overbroad_schema_001",
        "holdout_clean_tax_math_001",
        "holdout_dependency_no_advisory_001",
    ]
    by_id = {str(case["case_id"]): case for case in cases}
    rows = [by_id[item] for item in order if item in by_id]
    rows.append(ambiguous_case())
    return rows


def usage_from_metadata(agent_dir: Path) -> dict[str, Any]:
    metadata = read_json(agent_dir / "backend_metadata.json", {})
    usage = metadata.get("usage") if isinstance(metadata, dict) else None
    if not isinstance(usage, dict):
        return {"tokens": None, "cost": None, "cost_reason": "usage_not_reported_or_no_pricing_integration"}
    tokens = usage.get("total_tokens")
    if tokens is None:
        tokens = sum(int(usage.get(key) or 0) for key in ("prompt_tokens", "completion_tokens"))
    return {"tokens": tokens, "cost": None, "cost_reason": "no_pricing_integration"}


def blocked_row(case_payload: dict[str, Any], out_dir: Path, reason: str, exc: Exception | None = None) -> dict[str, Any]:
    if exc is not None:
        write_text(out_dir / "blocked_or_failed_trace.txt", traceback.format_exc())
    return {
        "case_id": case_payload["case_id"],
        "task_family": case_payload["agent_visible"]["task_family"],
        "status": "blocked" if reason.startswith("missing_env") else "failed",
        "blocked_reason": reason if reason.startswith("missing_env") else None,
        "failure_reason": None if reason.startswith("missing_env") else reason,
        "before_verifier_result": None,
        "after_verifier_result": None,
        "before_feedback_type": None,
        "after_feedback_type": None,
        "activated_capability_group": None,
        "false_positive_count": None,
        "evidence_exact_match_rate": None,
        "unsupported_evidence_count_before": None,
        "unsupported_evidence_count_after": None,
        "token_count": None,
        "cost": None,
        "artifact_dir": str(out_dir),
    }


def run_case(
    *,
    case_payload: dict[str, Any],
    active_spec: mini.VariantSpec,
    active_pointer: dict[str, Any],
    output_root: Path,
    base_url: str,
    model: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    out_dir = output_root / "cases" / str(case_payload["case_id"]) / "live_llm_contract"
    if not api_key_present():
        return blocked_row(case_payload, out_dir, "missing_env:OPENAI_API_KEY")
    try:
        summary = mini.run_variant(
            case_payload=case_payload,
            agent_case=mini.make_agent_visible_case(case_payload),
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
                "task_label": f"secure_code_review:{case_payload['agent_visible']['task_family']}",
                "contract_mode": "strict",
                "enable_evidence_normalizer": True,
                "prompt_addendum": (
                    "Live output contract: each finding must bind to a capability group and quote an exact complete target line in evidence_span. "
                    "Evaluate every active capability_id as a checklist item, but emit only grounded findings. "
                    "If evidence is not exact, return no concrete finding and use needs_review/low_confidence in notes. "
                    "For clean, out-of-scope, or unsupported task families, return an empty findings array. Defensive review only; no exploit steps."
                ),
            },
        )
        before = summary.get("pre_normalization_verifier") or {}
        after = summary.get("post_normalization_verifier") or {}
        trace = summary.get("normalization_trace") or {}
        usage = usage_from_metadata(out_dir / "agent")
        return {
            "case_id": case_payload["case_id"],
            "task_family": case_payload["agent_visible"]["task_family"],
            "status": "completed",
            "blocked_reason": None,
            "failure_reason": None if after.get("pass") else after.get("feedback_type"),
            "before_verifier_result": "pass" if before.get("pass") else "fail",
            "after_verifier_result": "pass" if after.get("pass") else "fail",
            "before_feedback_type": before.get("feedback_type"),
            "after_feedback_type": after.get("feedback_type"),
            "before_failure_taxonomy": summary.get("pre_normalization_verifier_taxonomy"),
            "after_failure_taxonomy": summary.get("post_normalization_verifier_taxonomy"),
            "activated_capability_group": summary.get("activated_capability_group"),
            "false_positive_count": false_positive_count(after),
            "evidence_exact_match_rate": trace.get("evidence_exact_match_rate"),
            "unsupported_evidence_count_before": len(before.get("unsupported_evidence_capabilities", [])),
            "unsupported_evidence_count_after": len(after.get("unsupported_evidence_capabilities", [])),
            "normalizer_taxonomy_counts": trace.get("failure_taxonomy_counts"),
            "token_count": usage["tokens"],
            "cost": usage["cost"],
            "cost_reason": usage["cost_reason"],
            "artifact_dir": str(out_dir),
        }
    except Exception as exc:  # noqa: BLE001 - failures are preserved as evidence.
        return blocked_row(case_payload, out_dir, str(exc), exc)


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    completed = [row for row in rows if row["status"] == "completed"]
    blocked = [row for row in rows if row["status"] == "blocked"]
    before_pass = sum(1 for row in completed if row["before_verifier_result"] == "pass")
    after_pass = sum(1 for row in completed if row["after_verifier_result"] == "pass")
    improvement_count = sum(1 for row in completed if row["before_verifier_result"] != "pass" and row["after_verifier_result"] == "pass")
    fp_count = sum(int(row.get("false_positive_count") or 0) for row in completed)
    unsupported_before = sum(int(row.get("unsupported_evidence_count_before") or 0) for row in completed)
    unsupported_after = sum(int(row.get("unsupported_evidence_count_after") or 0) for row in completed)
    exact_rates = [float(row["evidence_exact_match_rate"]) for row in completed if row.get("evidence_exact_match_rate") is not None]
    avg_exact = round(sum(exact_rates) / len(exact_rates), 4) if exact_rates else None
    if blocked and not completed:
        effectiveness = "blocked"
    elif completed and after_pass == len(completed):
        effectiveness = "pass"
    elif improvement_count or after_pass > before_pass:
        effectiveness = "partial_improved"
    else:
        effectiveness = "partial"
    return {
        "completed_count": len(completed),
        "blocked_count": len(blocked),
        "before_pass_count": before_pass,
        "after_pass_count": after_pass,
        "normalizer_improvement_count": improvement_count,
        "false_positive_count": fp_count,
        "unsupported_evidence_count_before": unsupported_before,
        "unsupported_evidence_count_after": unsupported_after,
        "evidence_exact_match_rate": avg_exact,
        "live_contract_effectiveness": effectiveness,
    }


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Live Contract Validation Status",
        "",
        f"Generated at: `{payload['generated_at']}`",
        "",
        "This run evaluates a contract-grounded live LLM path with strict verifier behavior unchanged. The normalizer only uses agent-visible target text, model output, Skill metadata, and the contract schema.",
        "",
        "## Summary",
        "",
        f"- Cases: `{payload['case_count']}`",
        f"- Completed: `{payload['completed_count']}`",
        f"- Blocked: `{payload['blocked_count']}`",
        f"- Before-normalizer pass count: `{payload['before_pass_count']}`",
        f"- After-normalizer pass count: `{payload['after_pass_count']}`",
        f"- Normalizer improvement count: `{payload['normalizer_improvement_count']}`",
        f"- Evidence exact match rate: `{payload['evidence_exact_match_rate']}`",
        f"- Unsupported evidence before/after: `{payload['unsupported_evidence_count_before']} / {payload['unsupported_evidence_count_after']}`",
        f"- False positives: `{payload['false_positive_count']}`",
        f"- `live_contract_effectiveness`: `{payload['live_contract_effectiveness']}`",
        "",
        "## Rows",
        "",
        "| Case | Family | Status | Group | Before | After | Unsupported before/after | FP | Exact rate | Artifacts |",
        "|---|---|---|---|---|---|---:|---:|---:|---|",
    ]
    for row in payload["rows"]:
        unsupported = f"{row.get('unsupported_evidence_count_before')} / {row.get('unsupported_evidence_count_after')}"
        lines.append(
            f"| {row['case_id']} | {row['task_family']} | {row['status']} | {row.get('activated_capability_group')} | "
            f"{row.get('before_verifier_result')}:{row.get('before_feedback_type')} | {row.get('after_verifier_result')}:{row.get('after_feedback_type')} | "
            f"{unsupported} | {row.get('false_positive_count')} | {row.get('evidence_exact_match_rate')} | `{row.get('artifact_dir')}` |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Verifier logic was not relaxed.",
            "- Verifier-only oracle fields were not exposed to the model or normalizer.",
            "- The ambiguous case is a local holdout stress probe, not an official benchmark.",
            "- API keys are not written to artifacts.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run contract-grounded live LLM validation with before/after verifier evidence.")
    parser.add_argument("--installed", default="secure_code_review")
    parser.add_argument("--output-dir", default=str(OUTPUT_ROOT))
    parser.add_argument("--base-url", default=os.environ.get("OPENAI_BASE_URL") or "https://api.deepseek.com")
    parser.add_argument("--model", default=os.environ.get("MODEL") or os.environ.get("OPENAI_MODEL") or "deepseek-v4-flash")
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    args = parser.parse_args(argv)

    specs, active_pointer, unavailable = mini.build_variant_specs(args.installed)
    active_spec = next(spec for spec in specs if spec.name == "active_installed")
    cases = selected_cases()
    output_root = Path(args.output_dir)
    rows = [
        run_case(
            case_payload=case_payload,
            active_spec=active_spec,
            active_pointer=active_pointer,
            output_root=output_root,
            base_url=args.base_url,
            model=args.model,
            timeout_seconds=args.timeout_seconds,
        )
        for case_payload in cases
    ]
    summary = summarize(rows)
    payload = {
        "run_id": "live_contract_validation_secure_code_review",
        "generated_at": utc_now(),
        "installed_skill": args.installed,
        "base_url_configured": bool(args.base_url),
        "model": args.model,
        "api_key_present": api_key_present(),
        "case_count": len(cases),
        "unavailable_variants": unavailable,
        "rows": rows,
        "claim_boundary": "local live LLM contract validation; not official external benchmark",
        **summary,
    }
    write_json(output_root / "live_contract_validation_summary.json", payload)
    write_text(REPORT, render_report(payload))
    print(json.dumps({"summary": str(output_root / "live_contract_validation_summary.json"), "report": str(REPORT), "live_contract_effectiveness": payload["live_contract_effectiveness"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
