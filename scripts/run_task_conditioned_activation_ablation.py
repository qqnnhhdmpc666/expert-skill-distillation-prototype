from __future__ import annotations

import argparse
import json
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
from skill_deployment.evidence import write_json, write_text  # noqa: E402
from skill_deployment.install_state import load_active_pointer, read_skill_version, skill_version_dir  # noqa: E402

import scripts.run_defensive_security_mini_suite as mini  # noqa: E402


SUITE_PATH = ROOT / "data" / "external_security_mini_suite" / "holdout_cases.json"
OUTPUT_ROOT = ROOT / "outputs" / "ablation" / "task_conditioned_activation"
REPORT = ROOT / "reports" / "TASK_CONDITIONED_ACTIVATION_ABLATION_STATUS.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def selected_cases() -> list[dict[str, Any]]:
    suite = read_json(SUITE_PATH, {})
    families = [
        "upload_security",
        "config_security",
        "auth_access_control",
        "api_or_code_review",
        "clean_business_logic_review",
        "dependency_version_risk",
    ]
    rows = []
    for family in families:
        match = next((case for case in suite.get("cases", []) if case["agent_visible"]["task_family"] == family), None)
        if match is not None:
            rows.append(match)
    return rows


def load_active_package(installed: str) -> tuple[SkillPackage, str, Path, dict[str, Any]]:
    pointer = load_active_pointer(ROOT, installed)
    version = str(pointer.get("active_version") or "v2")
    path = Path(str(pointer.get("skill_dir") or skill_version_dir(ROOT, installed, version))).resolve()
    package, text, _manifest = read_skill_version(path)
    return package, text, path, pointer


def clone_package(base: SkillPackage, *, version: str, metadata: dict[str, Any]) -> SkillPackage:
    return SkillPackage(
        skill_id=base.skill_id,
        version=version,
        task_family=base.task_family,
        capabilities=base.capabilities,
        output_contract=base.output_contract,
        trace_contract=base.trace_contract,
        metadata=metadata,
    )


def write_variant_package(name: str, package: SkillPackage, base_text: str) -> tuple[Path, str]:
    path = OUTPUT_ROOT / "variants" / name
    text = base_text.rstrip() + f"\n\n## Ablation Variant\n\n- Variant: `{name}`\n- This package is experimental and must not be installed as active runtime state.\n"
    write_text(path / "SKILL.md", text)
    write_json(path / "manifest.json", package.to_dict())
    return path, text


def build_variants(base: SkillPackage, base_text: str, active_dir: Path, pointer: dict[str, Any], task_families: list[str]) -> list[mini.VariantSpec]:
    base_meta = dict(base.metadata or {})
    all_caps = list(base.capabilities)
    variants: list[mini.VariantSpec] = [
        mini.VariantSpec("active_installed", base, base_text, active_dir, "active_installed_package"),
    ]

    def install_variant(name: str, updater: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
        metadata = updater(json.loads(json.dumps(base_meta)))
        package = clone_package(base, version=f"ablation_{name}", metadata=metadata)
        path, text = write_variant_package(name, package, base_text)
        variants.append(mini.VariantSpec(name, package, text, path, "ablation_experiment_package"))

    def no_out_of_scope_guard(meta: dict[str, Any]) -> dict[str, Any]:
        groups = list(meta.get("capability_groups", []))
        for group in groups:
            if group.get("name") == "upload_security":
                group["task_families"] = sorted(set(group.get("task_families", []) + ["clean_business_logic_review", "dependency_version_risk"]))
        meta["capability_groups"] = groups
        meta["out_of_scope_group"] = "disabled_out_of_scope_guard"
        return meta

    def all_capabilities_always_on(meta: dict[str, Any]) -> dict[str, Any]:
        meta["capability_groups"] = [
            {
                "name": "all_capabilities_always_on",
                "task_families": sorted(set(task_families)),
                "capabilities": all_caps,
            }
        ]
        meta["out_of_scope_group"] = "disabled_out_of_scope_guard"
        return meta

    def no_task_router(meta: dict[str, Any]) -> dict[str, Any]:
        meta["capability_groups"] = []
        meta["supported_task_families"] = []
        meta["out_of_scope_group"] = "out_of_scope_guard"
        return meta

    install_variant("ablated_no_out_of_scope_guard", no_out_of_scope_guard)
    install_variant("ablated_all_capabilities_always_on", all_capabilities_always_on)
    install_variant("ablated_no_task_router", no_task_router)
    return variants


def scope_violation(summary: dict[str, Any], expected_group: str) -> bool:
    activated = str(summary.get("activated_capability_group") or "")
    if expected_group == "out_of_scope_guard":
        return activated != "out_of_scope_guard" or not summary.get("out_of_scope_correct")
    return activated != expected_group


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Task-Conditioned Activation Ablation Status",
        "",
        f"Generated at: `{payload['generated_at']}`",
        "",
        "Ablation variants are temporary experiment packages. They do not overwrite the installed active package.",
        "",
        "## Summary",
        "",
        f"- Sample count: `{payload['sample_count']}`",
        f"- Mechanism status: `{payload['mechanism_status']}`",
        "",
        "| Variant | Case | Expected group | Activated group | Score delta | FP count | Scope violation |",
        "|---|---|---|---|---:|---:|---:|",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['variant']} | {row['case_id']} | {row['expected_capability_group']} | {row['activated_capability_group']} | "
            f"{row['score_delta_vs_active']} | {row['false_positive_count']} | {row['scope_violation']} |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run task-conditioned activation ablation without changing active installed package.")
    parser.add_argument("--installed", default="secure_code_review")
    parser.add_argument("--backend", default="offline_deterministic")
    args = parser.parse_args(argv)

    cases = selected_cases()
    active_package, active_text, active_dir, pointer = load_active_package(args.installed)
    task_families = [case["agent_visible"]["task_family"] for case in cases]
    variants = build_variants(active_package, active_text, active_dir, pointer, task_families)
    rows: list[dict[str, Any]] = []
    by_case_active: dict[str, dict[str, Any]] = {}
    for case_payload in cases:
        agent_case = mini.make_agent_visible_case(case_payload)
        expected_group = str(case_payload["verifier_only"].get("expected_capability_group") or "")
        for spec in variants:
            out_dir = OUTPUT_ROOT / "cases" / str(case_payload["case_id"]) / spec.name
            summary = mini.run_variant(
                case_payload=case_payload,
                agent_case=agent_case,
                verifier_only=case_payload["verifier_only"],
                spec=spec,
                backend=args.backend,
                output_dir=out_dir,
                active_pointer_snapshot=pointer,
            )
            if spec.name == "active_installed":
                by_case_active[str(case_payload["case_id"])] = summary
            active_score = score_from_verifier(by_case_active.get(str(case_payload["case_id"]), summary))
            current_score = score_from_verifier(summary)
            rows.append(
                {
                    "case_id": case_payload["case_id"],
                    "task_family": agent_case.task_family,
                    "variant": spec.name,
                    "expected_capability_group": expected_group,
                    "activated_capability_group": summary.get("activated_capability_group"),
                    "verifier_result": "pass" if summary.get("pass") else "fail",
                    "verifier_feedback_type": summary.get("feedback_type"),
                    "false_positive_count": summary.get("false_positive_count"),
                    "scope_violation": scope_violation(summary, expected_group),
                    "score": current_score,
                    "score_delta_vs_active": round(current_score - active_score, 4),
                    "schema_error_delta": 0,
                    "artifact_dir": str(out_dir),
                }
            )
    active_violations = sum(1 for row in rows if row["variant"] == "active_installed" and row["scope_violation"])
    ablated_violations = sum(1 for row in rows if row["variant"] != "active_installed" and row["scope_violation"])
    ablated_score_regressions = sum(1 for row in rows if row["variant"] != "active_installed" and row["score_delta_vs_active"] < 0)
    payload = {
        "run_id": "task_conditioned_activation_ablation",
        "generated_at": utc_now(),
        "installed_skill": args.installed,
        "backend": args.backend,
        "sample_count": len(cases),
        "variants": [spec.name for spec in variants],
        "rows": rows,
        "active_scope_violations": active_violations,
        "ablated_scope_violations": ablated_violations,
        "ablated_score_regressions": ablated_score_regressions,
        "mechanism_status": "supports_mechanism" if active_violations == 0 and (ablated_violations or ablated_score_regressions) else "inconclusive",
        "claim_boundary": "Ablation supports or challenges the activation mechanism only in local controlled evidence.",
    }
    write_json(OUTPUT_ROOT / "activation_ablation_summary.json", payload)
    write_text(REPORT, render_report(payload))
    print(json.dumps({"summary": str(OUTPUT_ROOT / "activation_ablation_summary.json"), "report": str(REPORT), "mechanism_status": payload["mechanism_status"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
