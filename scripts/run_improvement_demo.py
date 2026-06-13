from __future__ import annotations

import argparse
import difflib
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

from skill_deployment import SkillPackage  # noqa: E402
from skill_deployment.evidence import write_json, write_text  # noqa: E402
from skill_deployment.install_state import load_active_pointer, read_skill_version, skill_version_dir  # noqa: E402

import scripts.run_defensive_security_mini_suite as mini  # noqa: E402


OUTPUT_ROOT = ROOT / "outputs" / "skill_evolution_lab" / "secure_code_review" / "improvement_demo"
REPORT = ROOT / "reports" / "IMPROVEMENT_DEMO_STATUS.md"
SUMMARY = OUTPUT_ROOT / "improvement_demo_summary.json"
LIVE_SUMMARY = ROOT / "outputs" / "live_llm_validation" / "live_llm_validation_summary.json"
HOLDOUT_SUITE = ROOT / "data" / "external_security_mini_suite" / "holdout_cases.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_active(installed: str) -> tuple[SkillPackage, str, Path, dict[str, Any]]:
    pointer = load_active_pointer(ROOT, installed)
    version = str(pointer.get("active_version") or "v2")
    active_dir = Path(str(pointer.get("skill_dir") or skill_version_dir(ROOT, installed, version))).resolve()
    package, text, _manifest = read_skill_version(active_dir)
    return package, text, active_dir, pointer


def clone_package(base: SkillPackage, *, candidate_id: str) -> SkillPackage:
    metadata = json.loads(json.dumps(dict(base.metadata or {})))
    metadata["improvement_demo_candidate_id"] = candidate_id
    metadata["candidate_generation_sources"] = ["live verifier feedback", "live evidence summary"]
    metadata["verifier_only_oracle_fields_read"] = False
    return SkillPackage(
        skill_id=base.skill_id,
        version=f"improvement_demo_{candidate_id}",
        task_family=base.task_family,
        capabilities=base.capabilities,
        output_contract=base.output_contract,
        trace_contract=base.trace_contract,
        metadata=metadata,
    )


def cases_by_id() -> dict[str, dict[str, Any]]:
    suite = read_json(HOLDOUT_SUITE, {})
    return {str(case["case_id"]): case for case in suite.get("cases", [])}


def live_failure_rows(live: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in live.get("rows", []):
        if row.get("status") != "completed":
            continue
        if row.get("verifier_result") != "pass" or row.get("discrepancy_vs_offline_deterministic") not in {None, "", "none"}:
            rows.append(row)
    return rows


def candidate_text_addition(row: dict[str, Any]) -> str:
    feedback = row.get("verifier_feedback_type") or row.get("failure_reason") or "unknown"
    if feedback == "unsupported_evidence":
        lesson = "Quote or tightly paraphrase exact target lines in evidence_span; do not cite generic risk labels."
    elif feedback == "false_positive_risk":
        lesson = "Only report active task-family capabilities and keep out_of_scope_guard empty-finding behavior."
    elif feedback == "output_contract_error":
        lesson = "Emit every required field: capability_id, evidence_span, and recommended_fix."
    else:
        lesson = "Preserve grounded evidence, strict JSON schema, and task-conditioned capability routing."
    return (
        "## Improvement Demo Candidate: live-feedback repair\n\n"
        f"- Source case: `{row['case_id']}`.\n"
        f"- Live feedback type: `{feedback}`.\n"
        f"- Repair lesson: {lesson}\n"
        "- Do not expand secure_code_review scope; dependency/version-risk remains out of scope.\n"
    )


def write_candidate(base: SkillPackage, base_text: str, row: dict[str, Any], index: int) -> tuple[SkillPackage, str, Path]:
    candidate_id = f"live_feedback_c{index:03d}"
    candidate_dir = OUTPUT_ROOT / candidate_id
    package = clone_package(base, candidate_id=candidate_id)
    candidate_text = base_text.rstrip() + "\n\n" + candidate_text_addition(row)
    write_text(candidate_dir / "SKILL.md", candidate_text)
    write_json(candidate_dir / "manifest.json", package.to_dict())
    diff = "\n".join(
        difflib.unified_diff(
            base_text.splitlines(),
            candidate_text.splitlines(),
            fromfile="active_installed_SKILL.md",
            tofile=f"{candidate_id}_SKILL.md",
            lineterm="",
        )
    )
    write_text(
        candidate_dir / "skill_diff.md",
        "\n".join(
            [
                f"# Skill Diff: {candidate_id}",
                "",
                "## Evidence Binding",
                "",
                f"- Solves live failure / discrepancy from: `{row['case_id']}`",
                f"- Live feedback: `{row.get('verifier_feedback_type') or row.get('failure_reason')}`",
                "- Scope expansion: `forbidden`",
                "- Risk controls: clean negative and unsupported limitation must not regress.",
                "",
                "```diff",
                diff,
                "```",
                "",
            ]
        ),
    )
    write_json(
        candidate_dir / "candidate_generation_inputs.json",
        {
            "candidate_id": candidate_id,
            "source": "live_llm_feedback",
            "source_case_id": row["case_id"],
            "source_artifact_dir": row.get("artifact_dir"),
            "allowed_sources": ["live verifier feedback", "live evidence summary"],
            "forbidden_sources": ["verifier-only expected finding", "verifier-only expected evidence span", "verifier-only clean/negative label"],
            "verifier_only_oracle_fields_read": False,
        },
    )
    write_json(
        candidate_dir / "risk_assessment.json",
        {
            "candidate_id": candidate_id,
            "scope_expansion_risk": "medium",
            "negative_control_required": True,
            "unsupported_limitation_required": True,
            "dependency_version_risk_absorbed": False,
        },
    )
    return package, candidate_text, candidate_dir


def run_live_variant_safe(
    *,
    case_payload: dict[str, Any],
    spec: mini.VariantSpec,
    pointer: dict[str, Any],
    output_dir: Path,
    base_url: str,
    model: str,
    timeout_seconds: float,
) -> tuple[dict[str, Any] | None, str | None]:
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        return (
            mini.run_variant(
                case_payload=case_payload,
                agent_case=mini.make_agent_visible_case(case_payload),
                verifier_only=case_payload["verifier_only"],
                spec=spec,
                backend="live_llm_text",
                output_dir=output_dir,
                active_pointer_snapshot=pointer,
                runner_metadata={
                    "base_url": base_url,
                    "model": model,
                    "temperature": 0.0,
                    "timeout": timeout_seconds,
                    "task_label": f"secure_code_review:{case_payload['agent_visible']['task_family']}",
                    "contract_mode": "strict",
                    "prompt_addendum": "Use no exploit steps. Defensive review only. If no active capabilities are allowed, return an empty findings array.",
                },
            ),
            None,
        )
    except Exception as exc:  # noqa: BLE001 - validation failures are evidence.
        write_text(output_dir / "blocked_or_failed_trace.txt", traceback.format_exc())
        return None, str(exc)


def validation_for_candidate(
    *,
    row: dict[str, Any],
    candidate_package: SkillPackage,
    candidate_text: str,
    candidate_dir: Path,
    active_summary: dict[str, Any],
    active_package: SkillPackage,
    active_text: str,
    active_dir: Path,
    pointer: dict[str, Any],
    base_url: str,
    model: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    cases = cases_by_id()
    source_case = cases[str(row["case_id"])]
    clean_case = cases.get("holdout_clean_tax_math_001")
    unsupported_case = cases.get("holdout_dependency_no_advisory_001")
    candidate_spec = mini.VariantSpec("candidate_package", candidate_package, candidate_text, candidate_dir, "improvement_demo_candidate")
    active_spec = mini.VariantSpec("active_installed", active_package, active_text, active_dir, "active_installed_package")
    candidate_summary, candidate_error = run_live_variant_safe(
        case_payload=source_case,
        spec=candidate_spec,
        pointer=pointer,
        output_dir=candidate_dir / "validation" / "candidate_source_case",
        base_url=base_url,
        model=model,
        timeout_seconds=timeout_seconds,
    )
    clean_active = clean_candidate = unsupported_active = unsupported_candidate = None
    clean_error = unsupported_error = None
    if clean_case is not None:
        clean_active, _ = run_live_variant_safe(
            case_payload=clean_case,
            spec=active_spec,
            pointer=pointer,
            output_dir=candidate_dir / "validation" / "active_clean_control",
            base_url=base_url,
            model=model,
            timeout_seconds=timeout_seconds,
        )
        clean_candidate, clean_error = run_live_variant_safe(
            case_payload=clean_case,
            spec=candidate_spec,
            pointer=pointer,
            output_dir=candidate_dir / "validation" / "candidate_clean_control",
            base_url=base_url,
            model=model,
            timeout_seconds=timeout_seconds,
        )
    if unsupported_case is not None:
        unsupported_active, _ = run_live_variant_safe(
            case_payload=unsupported_case,
            spec=active_spec,
            pointer=pointer,
            output_dir=candidate_dir / "validation" / "active_unsupported_control",
            base_url=base_url,
            model=model,
            timeout_seconds=timeout_seconds,
        )
        unsupported_candidate, unsupported_error = run_live_variant_safe(
            case_payload=unsupported_case,
            spec=candidate_spec,
            pointer=pointer,
            output_dir=candidate_dir / "validation" / "candidate_unsupported_control",
            base_url=base_url,
            model=model,
            timeout_seconds=timeout_seconds,
        )
    active_score = float(active_summary.get("score") or 0.0)
    candidate_score = float(candidate_summary.get("score") or 0.0) if candidate_summary else 0.0
    fp_delta = int((candidate_summary or {}).get("false_positive_count") or 0) - int(active_summary.get("false_positive_count") or 0)
    schema_delta = int(not bool((candidate_summary or {}).get("schema_valid"))) - int(not bool(active_summary.get("schema_valid")))
    scope_violation = not bool((candidate_summary or {}).get("capability_group_correct")) if candidate_summary else True
    clean_not_worse = bool(clean_candidate) and bool(clean_active) and int(clean_candidate.get("false_positive_count") or 0) <= int(clean_active.get("false_positive_count") or 0)
    unsupported_preserved = bool(unsupported_candidate) and bool(unsupported_candidate.get("out_of_scope_correct")) and int(unsupported_candidate.get("false_positive_count") or 0) == 0
    validation = {
        "source_case_id": row["case_id"],
        "active_score": active_score,
        "candidate_score": candidate_score,
        "score_delta": round(candidate_score - active_score, 4),
        "false_positive_delta": fp_delta,
        "schema_error_delta": schema_delta,
        "scope_violation": scope_violation,
        "negative_clean_control_not_worse": clean_not_worse,
        "unsupported_limitation_remains_unsupported": unsupported_preserved,
        "candidate_error": candidate_error,
        "clean_control_error": clean_error,
        "unsupported_control_error": unsupported_error,
        "active_summary": active_summary,
        "candidate_summary": candidate_summary,
        "clean_active_summary": clean_active,
        "clean_candidate_summary": clean_candidate,
        "unsupported_active_summary": unsupported_active,
        "unsupported_candidate_summary": unsupported_candidate,
    }
    promoted = (
        validation["score_delta"] > 0
        and fp_delta <= 0
        and schema_delta <= 0
        and not scope_violation
        and clean_not_worse
        and unsupported_preserved
    )
    decision = {
        "decision": "staged_promotion_proposal" if promoted else "not_promoted",
        "reason": "strict_live_feedback_improvement" if promoted else "strict_rule_not_satisfied",
        "auto_installed": False,
        "promotion_rule": "candidate_score > active_installed_score and false_positive_delta <= 0 and schema_error_delta <= 0 and scope_violation=false and negative/unsupported controls not worse",
    }
    return {"validation_result": validation, "promotion_decision": decision}


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Improvement Demo Status",
        "",
        f"Generated at: `{payload['generated_at']}`",
        "",
        "This demo uses live LLM validation feedback only. It does not synthesize a fake failure, does not read verifier-only oracle fields, and does not install promoted candidates automatically.",
        "",
        "## Summary",
        "",
        f"- `candidate_generation`: `{payload['candidate_generation']}`",
        f"- `evolution_safety_gate`: `{payload['evolution_safety_gate']}`",
        f"- `evolution_improvement`: `{payload['evolution_improvement']}`",
        f"- `evolution_maturity`: `{payload['evolution_maturity']}`",
        f"- Blocked reason: `{payload.get('blocked_reason') or 'none'}`",
        "",
        "## Candidates",
        "",
        "| Candidate | Source case | Decision | Score delta | FP delta | Scope violation |",
        "|---|---|---|---:|---:|---:|",
    ]
    if not payload["candidate_outputs"]:
        lines.append("| none | none | none | 0 | 0 | False |")
    for item in payload["candidate_outputs"]:
        validation = item["validation_result"]
        decision = item["promotion_decision"]
        lines.append(
            f"| {item['candidate_id']} | {validation['source_case_id']} | {decision['decision']} | "
            f"{validation['score_delta']} | {validation['false_positive_delta']} | {validation['scope_violation']} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Dependency/version-risk remains unsupported by secure_code_review core capability.",
            "- Candidate rejection is safety evidence, not improvement evidence.",
            "- Improvement is demonstrated only by a staged promotion proposal under the strict rule.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Try one live-feedback-driven Skill improvement demo.")
    parser.add_argument("--installed", default="secure_code_review")
    parser.add_argument("--source", choices=["live_llm_feedback"], default="live_llm_feedback")
    parser.add_argument("--budget", type=int, default=2)
    parser.add_argument("--base-url", default=os.environ.get("OPENAI_BASE_URL") or "https://api.deepseek.com")
    parser.add_argument("--model", default=os.environ.get("MODEL") or os.environ.get("OPENAI_MODEL") or "deepseek-v4-flash")
    parser.add_argument("--timeout-seconds", type=float, default=45.0)
    args = parser.parse_args(argv)

    live = read_json(LIVE_SUMMARY, {})
    candidate_outputs: list[dict[str, Any]] = []
    blocked_reason = None
    if not live:
        blocked_reason = "blocked_by_missing_live_feedback"
    elif live.get("live_llm_execution") != "pass":
        blocked_reason = "blocked_by_live_llm_execution_not_pass"
    failures = [] if blocked_reason else live_failure_rows(live)
    if not blocked_reason and not failures:
        blocked_reason = "no_live_failure_or_discrepancy_available"
    if blocked_reason:
        payload = {
            "run_id": "live_feedback_improvement_demo",
            "generated_at": utc_now(),
            "source": args.source,
            "candidate_generation": "blocked",
            "evolution_safety_gate": "partial",
            "evolution_improvement": "not_yet_demonstrated" if blocked_reason == "no_live_failure_or_discrepancy_available" else "blocked",
            "evolution_maturity": "blocked" if blocked_reason != "no_live_failure_or_discrepancy_available" else "safety_gate_pass",
            "blocked_reason": blocked_reason,
            "candidate_outputs": [],
            "promotion_proposals": [],
            "rejected_edit_buffer": [],
            "claim_boundary": "No improvement claim without a strict live-feedback promotion proposal.",
        }
        write_json(SUMMARY, payload)
        write_text(REPORT, render_report(payload))
        print(json.dumps({"summary": str(SUMMARY), "report": str(REPORT), "blocked_reason": blocked_reason}, indent=2))
        return 0

    active_package, active_text, active_dir, pointer = load_active(args.installed)
    rejected: list[dict[str, Any]] = []
    proposals: list[dict[str, Any]] = []
    for index, row in enumerate(failures[: max(1, args.budget)], start=1):
        package, candidate_text, candidate_dir = write_candidate(active_package, active_text, row, index)
        active_summary = read_json(Path(str(row["artifact_dir"])) / "variant_summary.json", {})
        result = validation_for_candidate(
            row=row,
            candidate_package=package,
            candidate_text=candidate_text,
            candidate_dir=candidate_dir,
            active_summary=active_summary,
            active_package=active_package,
            active_text=active_text,
            active_dir=active_dir,
            pointer=pointer,
            base_url=args.base_url,
            model=args.model,
            timeout_seconds=args.timeout_seconds,
        )
        write_json(candidate_dir / "validation_result.json", result["validation_result"])
        write_json(candidate_dir / "promotion_decision.json", result["promotion_decision"])
        candidate_id = candidate_dir.name
        output = {"candidate_id": candidate_id, "candidate_dir": str(candidate_dir), **result, "oracle_fields_read_for_generation": False}
        candidate_outputs.append(output)
        if result["promotion_decision"]["decision"] == "staged_promotion_proposal":
            proposals.append({"candidate_id": candidate_id, "candidate_dir": str(candidate_dir)})
        else:
            rejected.append(
                {
                    "candidate_id": candidate_id,
                    "source_case_id": row["case_id"],
                    "reason": result["promotion_decision"]["reason"],
                    "score_delta": result["validation_result"]["score_delta"],
                    "false_positive_delta": result["validation_result"]["false_positive_delta"],
                    "scope_violation": result["validation_result"]["scope_violation"],
                }
            )
    candidate_generation = "pass" if candidate_outputs else "blocked"
    safety_gate = "pass" if rejected or proposals else "partial"
    improvement = "demonstrated" if proposals else "not_yet_demonstrated"
    maturity = "improvement_demonstrated" if proposals else ("safety_gate_pass" if safety_gate == "pass" else "partial")
    payload = {
        "run_id": "live_feedback_improvement_demo",
        "generated_at": utc_now(),
        "source": args.source,
        "candidate_generation": candidate_generation,
        "evolution_safety_gate": safety_gate,
        "evolution_improvement": improvement,
        "evolution_maturity": maturity,
        "blocked_reason": None,
        "candidate_outputs": candidate_outputs,
        "promotion_proposals": proposals,
        "rejected_edit_buffer": rejected,
        "claim_boundary": "No improvement claim without a strict live-feedback promotion proposal.",
    }
    write_json(SUMMARY, payload)
    write_text(REPORT, render_report(payload))
    print(json.dumps({"summary": str(SUMMARY), "report": str(REPORT), "candidates": len(candidate_outputs), "promotions": len(proposals)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
