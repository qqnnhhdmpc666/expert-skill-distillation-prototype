from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


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
from scripts.run_live_contract_validation import ambiguous_case, selected_cases as live_contract_cases  # noqa: E402


OUTPUT_ROOT = ROOT / "outputs" / "mechanism_ablation" / "live_contract"
REPORT = ROOT / "reports" / "LIVE_MECHANISM_ABLATION_STATUS.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def api_key_present() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


def load_active(installed: str) -> tuple[SkillPackage, str, Path, dict[str, Any]]:
    pointer = load_active_pointer(ROOT, installed)
    version = str(pointer.get("active_version") or "v2")
    path = Path(str(pointer.get("skill_dir") or skill_version_dir(ROOT, installed, version))).resolve()
    package, text, _manifest = read_skill_version(path)
    return package, text, path, pointer


def clone(base: SkillPackage, version: str, metadata: dict[str, Any]) -> SkillPackage:
    return SkillPackage(
        skill_id=base.skill_id,
        version=version,
        task_family=base.task_family,
        capabilities=base.capabilities,
        output_contract=base.output_contract,
        trace_contract=base.trace_contract,
        metadata=metadata,
    )


def write_package_variant(name: str, package: SkillPackage, base_text: str) -> tuple[Path, str]:
    path = OUTPUT_ROOT / "variant_packages" / name
    text = base_text.rstrip() + f"\n\n## Live Mechanism Ablation Variant\n\n- Variant: `{name}`\n- Temporary package used only for live mechanism ablation.\n"
    write_text(path / "SKILL.md", text)
    write_json(path / "manifest.json", package.to_dict())
    return path, text


def build_variants(base: SkillPackage, base_text: str, active_dir: Path, task_families: list[str]) -> dict[str, mini.VariantSpec]:
    base_meta = json.loads(json.dumps(dict(base.metadata or {})))
    variants = {
        "active_contract_system": mini.VariantSpec("active_contract_system", base, base_text, active_dir, "active_contract_system"),
        "no_evidence_normalizer": mini.VariantSpec("no_evidence_normalizer", base, base_text, active_dir, "active_no_normalizer"),
    }

    def install(name: str, updater: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
        meta = updater(json.loads(json.dumps(base_meta)))
        package = clone(base, f"live_ablation_{name}", meta)
        path, text = write_package_variant(name, package, base_text)
        variants[name] = mini.VariantSpec(name, package, text, path, "live_ablation_package")

    def no_out_of_scope_guard(meta: dict[str, Any]) -> dict[str, Any]:
        groups = list(meta.get("capability_groups", []))
        for group in groups:
            if group.get("name") == "upload_security":
                group["task_families"] = sorted(set(group.get("task_families", []) + ["clean_business_logic_review", "dependency_version_risk"]))
        meta["capability_groups"] = groups
        meta["out_of_scope_group"] = "disabled_out_of_scope_guard"
        return meta

    def all_caps(meta: dict[str, Any]) -> dict[str, Any]:
        meta["capability_groups"] = [
            {
                "name": "all_capabilities_always_on",
                "task_families": sorted(set(task_families)),
                "capabilities": list(base.capabilities),
            }
        ]
        meta["out_of_scope_group"] = "disabled_out_of_scope_guard"
        return meta

    def no_router(meta: dict[str, Any]) -> dict[str, Any]:
        meta["capability_groups"] = []
        meta["supported_task_families"] = []
        meta["out_of_scope_group"] = "out_of_scope_guard"
        return meta

    install("no_out_of_scope_guard", no_out_of_scope_guard)
    install("all_capabilities_always_on", all_caps)
    install("no_task_router", no_router)
    install("simple_prompt_baseline", all_caps)
    return variants


def selected_cases() -> list[dict[str, Any]]:
    rows = live_contract_cases()
    desired = {
        "holdout_upload_double_extension_001",
        "holdout_config_prod_secret_001",
        "holdout_auth_project_ownership_001",
        "holdout_api_overbroad_schema_001",
        "holdout_clean_tax_math_001",
        "holdout_dependency_no_advisory_001",
        "holdout_ambiguous_debug_path_001",
    }
    return [case for case in rows if case["case_id"] in desired]


def scope_violation(summary: dict[str, Any], expected_group: str) -> bool:
    activated = str(summary.get("activated_capability_group") or "")
    if expected_group == "out_of_scope_guard":
        return activated != "out_of_scope_guard" or int(summary.get("false_positive_count") or 0) > 0
    return activated != expected_group


def run_variant(
    *,
    case_payload: dict[str, Any],
    spec: mini.VariantSpec,
    variant_name: str,
    pointer: dict[str, Any],
    base_url: str,
    model: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    out_dir = OUTPUT_ROOT / "cases" / str(case_payload["case_id"]) / variant_name
    if not api_key_present():
        return {"case_id": case_payload["case_id"], "variant": variant_name, "status": "blocked", "blocked_reason": "missing_env:OPENAI_API_KEY", "artifact_dir": str(out_dir)}
    enable_normalizer = variant_name in {"active_contract_system", "no_out_of_scope_guard", "all_capabilities_always_on", "no_task_router"}
    if variant_name == "simple_prompt_baseline":
        addendum = "Return JSON findings only. Defensive review only."
    else:
        addendum = "Ablation contract: quote exact target lines; emit no concrete finding for unsupported, clean, or ambiguous claims. Defensive review only."
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
                "enable_evidence_normalizer": enable_normalizer,
                "prompt_addendum": addendum,
            },
        )
        verifier = summary.get("post_normalization_verifier") or summary.get("pre_normalization_verifier") or {}
        if not verifier:
            verifier = json.loads((out_dir / "verifier_report.json").read_text(encoding="utf-8"))
        expected_group = str(case_payload["verifier_only"].get("expected_capability_group") or "")
        trace = summary.get("normalization_trace") or {}
        return {
            "case_id": case_payload["case_id"],
            "task_family": case_payload["agent_visible"]["task_family"],
            "variant": variant_name,
            "status": "completed",
            "verifier_result": "pass" if verifier.get("pass") else "fail",
            "feedback_type": verifier.get("feedback_type"),
            "score": score_from_verifier(verifier),
            "false_positive_count": false_positive_count(verifier),
            "unsupported_evidence_count": len(verifier.get("unsupported_evidence_capabilities", [])),
            "schema_error_count": len(verifier.get("schema_errors", [])),
            "activated_capability_group": summary.get("activated_capability_group"),
            "expected_capability_group": expected_group,
            "scope_violation": scope_violation(summary, expected_group),
            "evidence_exact_match_rate": trace.get("evidence_exact_match_rate"),
            "normalizer_enabled": enable_normalizer,
            "artifact_dir": str(out_dir),
        }
    except Exception as exc:  # noqa: BLE001 - ablation failures are evidence.
        write_text(out_dir / "blocked_or_failed_trace.txt", str(exc))
        return {"case_id": case_payload["case_id"], "variant": variant_name, "status": "failed", "failure_reason": str(exc), "artifact_dir": str(out_dir)}


def summarize(rows: list[dict[str, Any]], variants: list[str]) -> dict[str, Any]:
    by_variant: dict[str, dict[str, Any]] = {}
    for variant in variants:
        vrows = [row for row in rows if row.get("variant") == variant]
        completed = [row for row in vrows if row.get("status") == "completed"]
        by_variant[variant] = {
            "completed_count": len(completed),
            "pass_count": sum(1 for row in completed if row.get("verifier_result") == "pass"),
            "false_positive_count": sum(int(row.get("false_positive_count") or 0) for row in completed),
            "scope_violation_count": sum(1 for row in completed if row.get("scope_violation")),
            "unsupported_evidence_count": sum(int(row.get("unsupported_evidence_count") or 0) for row in completed),
            "schema_error_count": sum(int(row.get("schema_error_count") or 0) for row in completed),
            "avg_score": round(sum(float(row.get("score") or 0.0) for row in completed) / len(completed), 4) if completed else 0.0,
        }
    active = by_variant.get("active_contract_system", {})
    regressions = {
        variant: {
            "fp_delta": metrics["false_positive_count"] - int(active.get("false_positive_count") or 0),
            "scope_violation_delta": metrics["scope_violation_count"] - int(active.get("scope_violation_count") or 0),
            "score_delta": round(metrics["avg_score"] - float(active.get("avg_score") or 0.0), 4),
        }
        for variant, metrics in by_variant.items()
        if variant != "active_contract_system"
    }
    supports = any(item["fp_delta"] > 0 or item["scope_violation_delta"] > 0 or item["score_delta"] < 0 for item in regressions.values())
    return {
        "variant_metrics": by_variant,
        "regressions_vs_active": regressions,
        "mechanism_ablation": "supports_mechanism" if supports else "inconclusive",
    }


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Live Mechanism Ablation Status",
        "",
        f"Generated at: `{payload['generated_at']}`",
        "",
        "This ablation compares the active contract-grounded runtime against bounded live variants. It is local live evidence, not an official benchmark.",
        "",
        "## Summary",
        "",
        f"- Cases: `{payload['case_count']}`",
        f"- Variants: `{', '.join(payload['variants'])}`",
        f"- `mechanism_ablation`: `{payload['mechanism_ablation']}`",
        "",
        "## Variant Metrics",
        "",
        "| Variant | Completed | Pass | FP | Scope violations | Unsupported evidence | Schema errors | Avg score |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for variant, metrics in payload["variant_metrics"].items():
        lines.append(
            f"| {variant} | {metrics['completed_count']} | {metrics['pass_count']} | {metrics['false_positive_count']} | "
            f"{metrics['scope_violation_count']} | {metrics['unsupported_evidence_count']} | {metrics['schema_error_count']} | {metrics['avg_score']} |"
        )
    lines.extend(
        [
            "",
            "## Rows",
            "",
            "| Variant | Case | Status | Verifier | FP | Scope violation | Score | Artifacts |",
            "|---|---|---|---|---:|---:|---:|---|",
        ]
    )
    for row in payload["rows"]:
        lines.append(
            f"| {row.get('variant')} | {row.get('case_id')} | {row.get('status')} | {row.get('verifier_result')}:{row.get('feedback_type')} | "
            f"{row.get('false_positive_count')} | {row.get('scope_violation')} | {row.get('score')} | `{row.get('artifact_dir')}` |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run bounded live mechanism ablation.")
    parser.add_argument("--installed", default="secure_code_review")
    parser.add_argument("--base-url", default=os.environ.get("OPENAI_BASE_URL") or "https://api.deepseek.com")
    parser.add_argument("--model", default=os.environ.get("MODEL") or os.environ.get("OPENAI_MODEL") or "deepseek-v4-flash")
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    args = parser.parse_args(argv)

    base, text, active_dir, pointer = load_active(args.installed)
    cases = selected_cases()
    variants = build_variants(base, text, active_dir, [case["agent_visible"]["task_family"] for case in cases])
    rows: list[dict[str, Any]] = []
    for case_payload in cases:
        for variant_name, spec in variants.items():
            rows.append(
                run_variant(
                    case_payload=case_payload,
                    spec=spec,
                    variant_name=variant_name,
                    pointer=pointer,
                    base_url=args.base_url,
                    model=args.model,
                    timeout_seconds=args.timeout_seconds,
                )
            )
    metrics = summarize(rows, list(variants))
    payload = {
        "run_id": "live_mechanism_ablation",
        "generated_at": utc_now(),
        "installed_skill": args.installed,
        "model": args.model,
        "api_key_present": api_key_present(),
        "case_count": len(cases),
        "variants": list(variants),
        "rows": rows,
        "claim_boundary": "bounded live ablation evidence; not external benchmark",
        **metrics,
    }
    write_json(OUTPUT_ROOT / "live_mechanism_ablation_summary.json", payload)
    write_text(REPORT, render_report(payload))
    print(json.dumps({"summary": str(OUTPUT_ROOT / "live_mechanism_ablation_summary.json"), "report": str(REPORT), "mechanism_ablation": payload["mechanism_ablation"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
