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

from skill_deployment import resolve_installed_skill, score_from_verifier  # noqa: E402
from skill_deployment.evidence import false_positive_count, write_json, write_text  # noqa: E402
from skill_deployment.install_state import load_active_pointer  # noqa: E402
from skill_deployment.schemas import SkillPackage  # noqa: E402

import scripts.run_defensive_security_mini_suite as mini  # noqa: E402
from scripts.run_external_generalization_validation import download_sources, materialize_cases  # noqa: E402
from scripts.run_open_world_distillation_validation import select_validation_cases  # noqa: E402


OUTPUT_ROOT = ROOT / "outputs" / "open_world_closed_loop"
SUMMARY_PATH = OUTPUT_ROOT / "open_world_closed_loop_summary.json"
REPORT = ROOT / "reports" / "OPEN_WORLD_CLOSED_LOOP_STATUS.md"
OPEN_WORLD_SUMMARY = ROOT / "outputs" / "open_world_distillation_validation" / "open_world_distillation_validation_summary.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def api_key_present() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def source_failure_rows() -> list[dict[str, Any]]:
    summary = read_json(OPEN_WORLD_SUMMARY, {})
    return [row for row in summary.get("distilled_rows", []) if not row.get("effective_pass")]


def load_cases() -> list[dict[str, Any]]:
    source_status = download_sources(OUTPUT_ROOT / "validation_sources")
    return select_validation_cases(materialize_cases(source_status))


def clone_package(base: SkillPackage, *, version: str) -> SkillPackage:
    metadata = json.loads(json.dumps(dict(base.metadata or {})))
    metadata["open_world_closed_loop"] = True
    metadata["candidate_generation_sources"] = ["open-world failure feedback", "public-material distilled skill text", "verifier feedback", "evidence summary"]
    metadata["verifier_only_oracle_fields_read"] = False
    return SkillPackage(
        skill_id=base.skill_id,
        version=version,
        task_family=base.task_family,
        capabilities=base.capabilities,
        output_contract=base.output_contract,
        trace_contract=base.trace_contract,
        metadata=metadata,
    )


def candidate_addition(rows: list[dict[str, Any]]) -> str:
    sections = [
        "## Open-World Closed-Loop Candidate",
        "",
        "This candidate is generated from the remaining bounded open-world failure rows.",
        "Keep dependency/version-risk, regex DoS, and server-side execution review out of scope.",
        "",
    ]
    families = {str(row.get("task_family") or "") for row in rows}
    if "config_security" in families:
        sections.extend(
            [
                "### Config Security Completion",
                "",
                "- Emit `CONFIG_AUDIT_EXPORT` when a production-facing audit block is enabled but `retention_days`, `export_sink`, or equivalent review destination is empty or missing.",
                "- Emit `CONFIG_ENV_GUARD` when a configuration file contains hardcoded API keys, session secrets, credentials, or debug-style defaults that should not live in committed application config.",
                "- Hardcoded secrets remain concrete findings even if a file is named `development` when the committed config is still reachable, shared, or treated as an application default in the target task.",
                "- Do not suppress concrete hardcoded-secret evidence as merely contextual noise.",
                "",
            ]
        )
    if "auth_access_control" in families:
        sections.extend(
            [
                "### Auth Scope Matrix Completion",
                "",
                "- Emit `AUTH_SCOPE_MATRIX` when the exact target line shows only `is_authenticated` or login-state gating before a protected read or mutation.",
                "- Emit `AUTH_OBJECT_OWNERSHIP` when the same target line loads an object by id without tenant, owner, account, or relationship filtering.",
                "- Emit `AUTH_ERROR_ENVELOPE` when denial output reveals a stable object id, invoice id, or business identifier instead of a neutral request id.",
                "- If one exact target line supports all three auth defects, emit three separate findings with the same evidence span.",
                "",
            ]
        )
    if "upload_security" in families:
        sections.extend(
            [
                "### Upload Completion",
                "",
                "- Emit `UPLOAD_TYPE_MAGIC` when extension-only or Content-Type-only validation is used without file-signature or magic-byte checks.",
                "- Emit `UPLOAD_PATH_ISOLATION` when user-controlled names are written directly or uploads remain under a public/executable root.",
                "- Emit `UPLOAD_AUDIT_RETENTION` when upload events lack attributable retention/export evidence.",
                "",
            ]
        )
    return "\n".join(sections).strip()


def write_candidate(base: SkillPackage, base_text: str, candidate_dir: Path, source_rows: list[dict[str, Any]]) -> tuple[SkillPackage, str]:
    package = clone_package(base, version="v3_candidate_auth_scope")
    candidate_text = base_text.rstrip() + "\n\n" + candidate_addition(source_rows) + "\n"
    write_text(candidate_dir / "SKILL.md", candidate_text)
    write_json(candidate_dir / "manifest.json", package.to_dict())
    diff = "\n".join(
        difflib.unified_diff(
            base_text.splitlines(),
            candidate_text.splitlines(),
            fromfile="open_world_v2_SKILL.md",
            tofile="open_world_v3_candidate_auth_scope.md",
            lineterm="",
        )
    )
    write_text(candidate_dir / "skill_diff.md", diff + "\n")
    write_json(
        candidate_dir / "candidate_generation_inputs.json",
        {
            "allowed_sources": ["open-world failure feedback", "public-material distilled skill text", "verifier feedback", "evidence summary"],
            "forbidden_sources": ["verifier-only expected finding", "verifier-only expected evidence span", "verifier-only clean/negative answer label"],
            "verifier_only_oracle_fields_read": False,
            "source_summary": str(OPEN_WORLD_SUMMARY),
            "source_failure_rows": source_rows,
        },
    )
    return package, candidate_text


def run_variant(
    *,
    case_payload: dict[str, Any],
    spec: mini.VariantSpec,
    pointer: dict[str, Any],
    output_dir: Path,
    base_url: str,
    model: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    out_dir = output_dir / str(case_payload["case_id"]) / spec.name
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
                "task_label": f"{spec.name}:{case_payload['agent_visible']['task_family']}",
                "contract_mode": "strict",
                "enable_evidence_normalizer": True,
                "prompt_addendum": (
                    "Open-world closed-loop validation: quote exact target lines; emit no findings for unsupported or clean cases. "
                    "Defensive review only. Do not invent capabilities beyond the active Skill package."
                ),
            },
        )
        verifier = summary.get("post_normalization_verifier") or read_json(out_dir / "verifier_report.json", {})
        return {
            "case_id": case_payload["case_id"],
            "task_family": case_payload["agent_visible"]["task_family"],
            "variant": spec.name,
            "status": "completed",
            "verifier_result": "pass" if verifier.get("pass") else "fail",
            "feedback_type": verifier.get("feedback_type"),
            "score": score_from_verifier(verifier),
            "effective_pass": bool(verifier.get("pass")) and bool(summary.get("capability_group_correct")),
            "activated_capability_group": summary.get("activated_capability_group"),
            "expected_capability_group": summary.get("expected_capability_group"),
            "capability_group_correct": summary.get("capability_group_correct"),
            "false_positive_count": false_positive_count(verifier),
            "out_of_scope_correct": summary.get("out_of_scope_correct"),
            "clean_or_negative": bool(case_payload["verifier_only"].get("clean_or_negative")),
            "unsupported_limitation": bool(case_payload["verifier_only"].get("unsupported_limitation")),
            "artifact_dir": str(out_dir),
        }
    except Exception as exc:  # noqa: BLE001
        write_text(out_dir / "blocked_or_failed_trace.txt", traceback.format_exc())
        return {
            "case_id": case_payload["case_id"],
            "task_family": case_payload["agent_visible"]["task_family"],
            "variant": spec.name,
            "status": "failed",
            "failure_reason": str(exc),
            "artifact_dir": str(out_dir),
        }


def decide(base_rows: list[dict[str, Any]], candidate_rows: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    base_by_case = {row["case_id"]: row for row in base_rows}
    candidate_by_case = {row["case_id"]: row for row in candidate_rows}
    shared_cases = [case_id for case_id in base_by_case if case_id in candidate_by_case]
    base_score = sum(float(base_by_case[case_id].get("score") or 0.0) for case_id in shared_cases) / len(shared_cases) if shared_cases else 0.0
    candidate_score = sum(float(candidate_by_case[case_id].get("score") or 0.0) for case_id in shared_cases) / len(shared_cases) if shared_cases else 0.0
    fp_delta = sum(int(candidate_by_case[case_id].get("false_positive_count") or 0) - int(base_by_case[case_id].get("false_positive_count") or 0) for case_id in shared_cases)
    positive_regressions = [
        case_id
        for case_id in shared_cases
        if base_by_case[case_id].get("effective_pass") and not candidate_by_case[case_id].get("effective_pass")
    ]
    clean_not_worse = all(
        int(candidate_by_case[case_id].get("false_positive_count") or 0) <= int(base_by_case[case_id].get("false_positive_count") or 0)
        for case_id in shared_cases
        if base_by_case[case_id].get("clean_or_negative")
    )
    unsupported_preserved = all(
        bool(candidate_by_case[case_id].get("out_of_scope_correct")) and int(candidate_by_case[case_id].get("false_positive_count") or 0) == 0
        for case_id in shared_cases
        if base_by_case[case_id].get("unsupported_limitation")
    )
    scope_violation = any(not bool(candidate_by_case[case_id].get("capability_group_correct")) for case_id in shared_cases)
    validation = {
        "base_score": round(base_score, 4),
        "candidate_score": round(candidate_score, 4),
        "score_delta": round(candidate_score - base_score, 4),
        "false_positive_delta": fp_delta,
        "positive_regression_count": len(positive_regressions),
        "positive_regression_cases": positive_regressions,
        "clean_negative_not_worse": clean_not_worse,
        "unsupported_limitation_preserved": unsupported_preserved,
        "scope_violation": scope_violation,
        "shared_case_count": len(shared_cases),
    }
    promoted = (
        validation["score_delta"] > 0
        and fp_delta <= 0
        and validation["positive_regression_count"] == 0
        and clean_not_worse
        and unsupported_preserved
        and not scope_violation
    )
    decision = {
        "decision": "staged_promotion_proposal" if promoted else "not_promoted",
        "reason": "strict_open_world_closed_loop_rule_satisfied" if promoted else "strict_open_world_closed_loop_rule_not_satisfied",
        "auto_installed": False,
        "promotion_rule": "candidate_score > base_score and false_positive_delta<=0 and positive_regression_count==0 and clean negative not worse and unsupported preserved and scope_violation=false",
    }
    return validation, decision


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Open-World Closed-Loop Status",
        "",
        f"Generated at: `{payload['generated_at']}`",
        "",
        "This run continues the bounded open-world story one step further: public-material distillation first, then a narrow auth-scope repair candidate generated from the remaining live failure pattern.",
        "",
        "## Fresh Commands",
        "",
        "```powershell",
        "skill-deploy open-world-distill-validation --version v2 --backend live_llm_text --base-url https://api.deepseek.com --model deepseek-v4-flash",
        "skill-deploy open-world-closed-loop --installed secure_code_review_open_world_distilled --repeats 3 --base-url https://api.deepseek.com --model deepseek-v4-flash",
        "```",
        "",
        "## Summary",
        "",
        f"- Base installed skill: `{payload['installed_skill']}`",
        f"- Base version: `{payload['base_version']}`",
        f"- Repeat count: `{payload['repeat_count']}`",
        f"- Promotion count: `{payload['promotion_count']}` / `{payload['repeat_count']}`",
        f"- Stable improvement: `{payload['stable_open_world_evolution']}`",
        "",
        "## Repeat Decisions",
        "",
        "| Repeat | Decision | Base score | Candidate score | Delta | FP delta | Positive regressions |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for item in payload["repeats"]:
        validation = item["validation_result"]
        decision = item["promotion_decision"]
        lines.append(
            f"| {item['repeat_index']} | {decision['decision']} | {validation['base_score']} | {validation['candidate_score']} | "
            f"{validation['score_delta']} | {validation['false_positive_delta']} | {validation['positive_regression_count']} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- This is bounded evidence for open-world distillation followed by one narrow evolution step.",
            "- It is not proof of unrestricted autonomous search over arbitrary public materials.",
            "- Unsupported dependency/version-risk remains unsupported.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one bounded closed-loop evolution step on top of the open-world distilled skill.")
    parser.add_argument("--installed", default="secure_code_review_open_world_distilled")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--base-url", default=os.environ.get("OPENAI_BASE_URL") or "https://api.deepseek.com")
    parser.add_argument("--model", default=os.environ.get("MODEL") or os.environ.get("OPENAI_MODEL") or "deepseek-v4-flash")
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    args = parser.parse_args(argv)

    base_resolved = resolve_installed_skill(ROOT, args.installed)
    pointer = load_active_pointer(ROOT, args.installed)
    base_spec = mini.VariantSpec("open_world_v2", base_resolved["skill_package"], base_resolved["skill_text"], base_resolved["skill_dir"], "open_world_distilled_package")
    candidate_dir = OUTPUT_ROOT / "candidate_auth_scope"
    failures = source_failure_rows()
    candidate_package, candidate_text = write_candidate(base_resolved["skill_package"], base_resolved["skill_text"], candidate_dir, failures)
    candidate_spec = mini.VariantSpec("open_world_v3_candidate", candidate_package, candidate_text, candidate_dir, "open_world_closed_loop_candidate")
    cases = load_cases()

    repeat_outputs: list[dict[str, Any]] = []
    promotion_count = 0
    for repeat_index in range(1, args.repeats + 1):
        repeat_root = OUTPUT_ROOT / f"repeat_{repeat_index:02d}"
        base_rows = [
            run_variant(
                case_payload=case_payload,
                spec=base_spec,
                pointer=pointer,
                output_dir=repeat_root / "base",
                base_url=args.base_url,
                model=args.model,
                timeout_seconds=args.timeout_seconds,
            )
            for case_payload in cases
        ]
        candidate_rows = [
            run_variant(
                case_payload=case_payload,
                spec=candidate_spec,
                pointer=pointer,
                output_dir=repeat_root / "candidate",
                base_url=args.base_url,
                model=args.model,
                timeout_seconds=args.timeout_seconds,
            )
            for case_payload in cases
        ]
        validation, decision = decide(base_rows, candidate_rows)
        if decision["decision"] == "staged_promotion_proposal":
            promotion_count += 1
        repeat_outputs.append(
            {
                "repeat_index": repeat_index,
                "validation_result": validation,
                "promotion_decision": decision,
                "base_rows": base_rows,
                "candidate_rows": candidate_rows,
            }
        )

    stable = promotion_count == args.repeats and all(item["validation_result"]["score_delta"] > 0 for item in repeat_outputs)
    payload = {
        "generated_at": utc_now(),
        "installed_skill": args.installed,
        "base_version": base_resolved["skill_package"].version,
        "repeat_count": args.repeats,
        "api_key_present": api_key_present(),
        "candidate_dir": str(candidate_dir),
        "promotion_count": promotion_count,
        "stable_open_world_evolution": "pass" if stable else "partial",
        "repeats": repeat_outputs,
    }
    write_json(SUMMARY_PATH, payload)
    write_text(REPORT, render_report(payload))
    print(json.dumps({"status": payload["stable_open_world_evolution"], "promotion_count": promotion_count, "report": str(REPORT)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
