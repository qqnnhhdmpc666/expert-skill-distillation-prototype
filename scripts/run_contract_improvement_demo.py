from __future__ import annotations

import argparse
import difflib
import json
import os
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

from skill_deployment import SkillPackage, score_from_verifier  # noqa: E402
from skill_deployment.evidence import false_positive_count, write_json, write_text  # noqa: E402
from skill_deployment.install_state import load_active_pointer, read_skill_version, skill_version_dir  # noqa: E402

import scripts.run_defensive_security_mini_suite as mini  # noqa: E402
from scripts.run_external_generalization_validation import materialize_cases, download_sources  # noqa: E402


OUTPUT_ROOT = ROOT / "outputs" / "contract_improvement_demo"
REPORT = ROOT / "reports" / "CONTRACT_IMPROVEMENT_DEMO_STATUS.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def api_key_present() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_active(installed: str) -> tuple[SkillPackage, str, Path, dict[str, Any]]:
    pointer = load_active_pointer(ROOT, installed)
    version = str(pointer.get("active_version") or "v2")
    path = Path(str(pointer.get("skill_dir") or skill_version_dir(ROOT, installed, version))).resolve()
    package, text, _manifest = read_skill_version(path)
    return package, text, path, pointer


def source_failure_rows() -> list[dict[str, Any]]:
    external = read_json(ROOT / "outputs" / "external_generalization_validation" / "external_generalization_summary.json", {})
    live_contract = read_json(ROOT / "outputs" / "live_contract_validation" / "live_contract_validation_summary.json", {})
    rows = []
    for row in external.get("rows", []):
        if row.get("status") == "completed" and not row.get("effective_pass"):
            rows.append({"source": "external_generalization", **row})
    for row in live_contract.get("rows", []):
        if row.get("status") == "completed" and row.get("after_verifier_result") != "pass":
            rows.append({"source": "live_contract_validation", **row})
    return rows


def candidate_addition(failures: list[dict[str, Any]]) -> str:
    lines = [
        "## Contract-Grounded Improvement Candidate",
        "",
        "This candidate is generated only from verifier feedback, evidence summaries, and normalization traces. It does not expand secure_code_review scope.",
        "",
        "### Live Checklist Strengthening",
        "",
        "- Treat active capabilities as independent checklist items, not as a menu of optional examples.",
        "- For `AUTH_SCOPE_MATRIX`, report when the target says access checks only authentication or lacks role/scope authorization. Keep this separate from object ownership.",
        "- For `API_OVERBROAD_RISK`, report when the target says a risk such as debug_path is generic, ungrounded, or lacks a target evidence span. Keep this separate from the JSON schema contract.",
        "- Positive observations are not findings: if upload validation, server filename generation, storage isolation, or audit retention are already present, emit no finding for that capability.",
        "- For unsupported dependency, regex DoS, server-side code execution, and other task families outside the manifest, keep `out_of_scope_guard` behavior and emit no findings.",
        "",
        "### Boundaries",
        "",
        "- Do not add dependency/version-risk, regex DoS, or code execution review to core capabilities.",
        "- Do not generate exploit steps or attack chains.",
        "- Use exact complete target lines as evidence spans; if exact evidence is absent, prefer no finding or needs_review/low_confidence trace.",
        "",
        "### Failure Evidence Used",
        "",
    ]
    for row in failures:
        lines.append(
            f"- `{row.get('case_id')}` from `{row.get('source')}`: feedback=`{row.get('feedback_type') or row.get('after_feedback_type')}`, "
            f"false_positive_count=`{row.get('false_positive_count')}`, artifact=`{row.get('artifact_dir')}`"
        )
    return "\n".join(lines) + "\n"


def clone_candidate(base: SkillPackage, candidate_id: str) -> SkillPackage:
    metadata = json.loads(json.dumps(dict(base.metadata or {})))
    metadata["contract_improvement_candidate_id"] = candidate_id
    metadata["candidate_generation_sources"] = ["failure report", "verifier feedback", "evidence summary", "normalization trace"]
    metadata["verifier_only_oracle_fields_read"] = False
    metadata["scope_expansion_forbidden"] = True
    return SkillPackage(
        skill_id=base.skill_id,
        version=f"contract_improvement_{candidate_id}",
        task_family=base.task_family,
        capabilities=base.capabilities,
        output_contract=base.output_contract,
        trace_contract=base.trace_contract,
        metadata=metadata,
    )


def write_candidate(base: SkillPackage, base_text: str, failures: list[dict[str, Any]]) -> tuple[str, SkillPackage, str, Path]:
    candidate_id = "c001"
    candidate_dir = OUTPUT_ROOT / "candidates" / candidate_id
    package = clone_candidate(base, candidate_id)
    text = base_text.rstrip() + "\n\n" + candidate_addition(failures)
    write_text(candidate_dir / "SKILL.md", text)
    write_json(candidate_dir / "manifest.json", package.to_dict())
    diff = "\n".join(difflib.unified_diff(base_text.splitlines(), text.splitlines(), fromfile="active_SKILL.md", tofile="candidate_SKILL.md", lineterm=""))
    write_text(
        candidate_dir / "skill_diff.md",
        "\n".join(
            [
                f"# Skill Diff: {candidate_id}",
                "",
                "## Why this candidate exists",
                "",
                "- Addresses real live/external failures: auth scope under-reporting, API overbroad-risk under-reporting, and positive-observation false positives.",
                "- Does not expand secure_code_review scope.",
                "- Risk controls: clean negative, unsupported limitation, and no scope violation are required before staged promotion.",
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
            "allowed_sources": ["failure report", "verifier feedback", "evidence summary", "normalization trace"],
            "forbidden_sources": ["verifier-only expected finding", "verifier-only expected evidence span", "verifier-only clean/negative answer label"],
            "verifier_only_oracle_fields_read": False,
            "failure_rows": failures,
        },
    )
    write_json(
        candidate_dir / "risk_assessment.json",
        {
            "scope_violation_risk": "medium",
            "dependency_version_risk_absorbed": False,
            "negative_control_required": True,
            "unsupported_limitation_required": True,
        },
    )
    return candidate_id, package, text, candidate_dir


def validation_cases() -> list[dict[str, Any]]:
    source_status = download_sources(OUTPUT_ROOT / "validation_sources")
    cases = materialize_cases(source_status)
    wanted = {
        "independent_upload_clean_001",
        "independent_config_prod_audit_001",
        "independent_auth_invoice_scope_001",
        "independent_api_schema_001",
        "independent_dependency_unsupported_001",
        "independent_ambiguous_debug_001",
    }
    return [case for case in cases if case["case_id"] in wanted]


def run_one(
    *,
    case_payload: dict[str, Any],
    spec: mini.VariantSpec,
    pointer: dict[str, Any],
    variant_name: str,
    candidate_dir: Path,
    base_url: str,
    model: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    out_dir = candidate_dir / "validation" / str(case_payload["case_id"]) / variant_name
    out_dir.mkdir(parents=True, exist_ok=True)
    if not api_key_present():
        return {"case_id": case_payload["case_id"], "variant": variant_name, "status": "blocked", "blocked_reason": "missing_env:OPENAI_API_KEY", "artifact_dir": str(out_dir)}
    try:
        summary = mini.run_variant(
            case_payload=case_payload,
            agent_case=mini.make_agent_visible_case(case_payload),
            verifier_only=case_payload["verifier_only"],
            spec=spec,
            backend="live_llm_text",
            output_dir=out_dir,
            active_pointer_snapshot=pointer,
            runner_metadata={
                "base_url": base_url,
                "model": model,
                "temperature": 0.0,
                "timeout": timeout_seconds,
                "task_label": f"secure_code_review:{case_payload['agent_visible']['task_family']}",
                "contract_mode": "strict",
                "enable_evidence_normalizer": True,
                "prompt_addendum": "Candidate validation: quote exact target lines; emit no concrete finding for unsupported, clean, or ambiguous claims. Defensive review only.",
            },
        )
        verifier = summary.get("post_normalization_verifier") or summary.get("pre_normalization_verifier") or read_json(out_dir / "verifier_report.json", {})
        return {
            "case_id": case_payload["case_id"],
            "variant": variant_name,
            "status": "completed",
            "verifier_result": "pass" if verifier.get("pass") else "fail",
            "feedback_type": verifier.get("feedback_type"),
            "score": score_from_verifier(verifier),
            "false_positive_count": false_positive_count(verifier),
            "schema_error_count": len(verifier.get("schema_errors", [])),
            "unsupported_evidence_count": len(verifier.get("unsupported_evidence_capabilities", [])),
            "scope_violation": summary.get("activated_capability_group") != summary.get("expected_capability_group"),
            "out_of_scope_correct": summary.get("out_of_scope_correct"),
            "artifact_dir": str(out_dir),
        }
    except Exception as exc:  # noqa: BLE001
        write_text(out_dir / "blocked_or_failed_trace.txt", str(exc))
        return {"case_id": case_payload["case_id"], "variant": variant_name, "status": "failed", "failure_reason": str(exc), "artifact_dir": str(out_dir)}


def decide(rows: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    active = [row for row in rows if row.get("variant") == "active"]
    candidate = [row for row in rows if row.get("variant") == "candidate"]
    active_score = sum(float(row.get("score") or 0.0) for row in active) / len(active) if active else 0.0
    candidate_score = sum(float(row.get("score") or 0.0) for row in candidate) / len(candidate) if candidate else 0.0
    fp_delta = sum(int(row.get("false_positive_count") or 0) for row in candidate) - sum(int(row.get("false_positive_count") or 0) for row in active)
    schema_delta = sum(int(row.get("schema_error_count") or 0) for row in candidate) - sum(int(row.get("schema_error_count") or 0) for row in active)
    unsupported_delta = sum(int(row.get("unsupported_evidence_count") or 0) for row in candidate) - sum(int(row.get("unsupported_evidence_count") or 0) for row in active)
    scope_violation = any(bool(row.get("scope_violation")) for row in candidate if row.get("status") == "completed")
    clean_not_worse = all(
        int(c.get("false_positive_count") or 0) <= int(a.get("false_positive_count") or 0)
        for c, a in zip(candidate, active)
        if "clean" in str(c.get("case_id")) or "ambiguous" in str(c.get("case_id"))
    )
    unsupported_preserved = all(
        bool(row.get("out_of_scope_correct")) and int(row.get("false_positive_count") or 0) == 0
        for row in candidate
        if "dependency" in str(row.get("case_id"))
    )
    validation = {
        "active_score": round(active_score, 4),
        "candidate_score": round(candidate_score, 4),
        "score_delta": round(candidate_score - active_score, 4),
        "false_positive_delta": fp_delta,
        "schema_error_delta": schema_delta,
        "unsupported_evidence_delta": unsupported_delta,
        "scope_violation": scope_violation,
        "clean_negative_not_worse": clean_not_worse,
        "unsupported_limitation_preserved": unsupported_preserved,
    }
    promoted = (
        validation["score_delta"] > 0
        and fp_delta <= 0
        and schema_delta <= 0
        and unsupported_delta <= 0
        and not scope_violation
        and clean_not_worse
        and unsupported_preserved
    )
    decision = {
        "decision": "staged_promotion_proposal" if promoted else "not_promoted",
        "reason": "strict_contract_improvement_rule_satisfied" if promoted else "strict_contract_improvement_rule_not_satisfied",
        "auto_installed": False,
        "promotion_rule": "candidate_score > active_score and false_positive_delta<=0 and schema_error_delta<=0 and unsupported_evidence_delta<=0 and clean negative not worse and scope_violation=false",
    }
    return validation, decision


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Contract Improvement Demo Status",
        "",
        f"Generated at: `{payload['generated_at']}`",
        "",
        f"- Candidate generation: `{payload['candidate_generation']}`",
        f"- Evolution safety gate: `{payload['evolution_safety_gate']}`",
        f"- Evolution improvement: `{payload['evolution_improvement']}`",
        f"- Evolution maturity: `{payload['evolution_maturity']}`",
        f"- Promotion decision: `{payload['promotion_decision']['decision']}`",
        f"- Score delta: `{payload['validation_result']['score_delta']}`",
        "",
        "## Validation Rows",
        "",
        "| Case | Variant | Status | Verifier | FP | Unsupported evidence | Scope violation | Score |",
        "|---|---|---|---|---:|---:|---:|---:|",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row.get('case_id')} | {row.get('variant')} | {row.get('status')} | {row.get('verifier_result')}:{row.get('feedback_type')} | "
            f"{row.get('false_positive_count')} | {row.get('unsupported_evidence_count')} | {row.get('scope_violation')} | {row.get('score')} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Candidate was generated from failure reports, verifier feedback, evidence summaries, and normalization traces.",
            "- Verifier-only oracle fields were not read.",
            "- The candidate was not auto-installed.",
            "- A staged promotion proposal is not a production deployment claim.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Attempt a strict contract-driven improvement candidate from real live failures.")
    parser.add_argument("--installed", default="secure_code_review")
    parser.add_argument("--base-url", default=os.environ.get("OPENAI_BASE_URL") or "https://api.deepseek.com")
    parser.add_argument("--model", default=os.environ.get("MODEL") or os.environ.get("OPENAI_MODEL") or "deepseek-v4-flash")
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    args = parser.parse_args(argv)

    failures = source_failure_rows()
    base, base_text, active_dir, pointer = load_active(args.installed)
    candidate_id, candidate_package, candidate_text, candidate_dir = write_candidate(base, base_text, failures)
    write_json(candidate_dir / "source_failures.json", {"failure_rows": failures})
    active_spec = mini.VariantSpec("active", base, base_text, active_dir, "active_installed_package")
    candidate_spec = mini.VariantSpec("candidate", candidate_package, candidate_text, candidate_dir, "contract_improvement_candidate")
    rows: list[dict[str, Any]] = []
    for case_payload in validation_cases():
        rows.append(
            run_one(
                case_payload=case_payload,
                spec=active_spec,
                pointer=pointer,
                variant_name="active",
                candidate_dir=candidate_dir,
                base_url=args.base_url,
                model=args.model,
                timeout_seconds=args.timeout_seconds,
            )
        )
        rows.append(
            run_one(
                case_payload=case_payload,
                spec=candidate_spec,
                pointer=pointer,
                variant_name="candidate",
                candidate_dir=candidate_dir,
                base_url=args.base_url,
                model=args.model,
                timeout_seconds=args.timeout_seconds,
            )
        )
    validation, decision = decide(rows)
    promoted = decision["decision"] == "staged_promotion_proposal"
    payload = {
        "run_id": "contract_improvement_demo",
        "generated_at": utc_now(),
        "candidate_id": candidate_id,
        "candidate_dir": str(candidate_dir),
        "candidate_generation": "pass",
        "evolution_safety_gate": "pass" if decision["decision"] in {"staged_promotion_proposal", "not_promoted"} else "fail",
        "evolution_improvement": "demonstrated" if promoted else "not_yet_demonstrated",
        "evolution_maturity": "improvement_demonstrated" if promoted else "safety_gate_pass",
        "validation_result": validation,
        "promotion_decision": decision,
        "rows": rows,
        "claim_boundary": "live contract improvement demo; staged proposal only, no auto promotion",
    }
    write_json(candidate_dir / "validation_result.json", validation)
    write_json(candidate_dir / "promotion_decision.json", decision)
    write_json(OUTPUT_ROOT / "contract_improvement_demo_summary.json", payload)
    write_text(REPORT, render_report(payload))
    print(json.dumps({"summary": str(OUTPUT_ROOT / "contract_improvement_demo_summary.json"), "report": str(REPORT), "decision": decision["decision"], "evolution_improvement": payload["evolution_improvement"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
