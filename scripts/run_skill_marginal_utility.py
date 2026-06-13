from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from skill_deployment import (  # noqa: E402
    CAPABILITY_SPECS,
    RepairContext,
    RunnerContext,
    SCHEMA_VERSION,
    SkillPackage,
    VerifierReport,
    build_marginal_utility_result,
    build_patch_and_gate,
    build_verifier_hash,
    get_backend_runner,
    hash_file_sha256,
    hash_json_file_sha256,
    hash_text_sha256,
    resolve_task_conditioned_activation,
    select_controlled_task_cases,
    score_from_verifier,
    verify_controlled_execution,
    write_evidence_bundle,
)
from skill_deployment.evidence import skill_cost, write_json, write_text  # noqa: E402
from skill_deployment.install_state import load_active_pointer, load_registry, read_skill_version, skill_version_dir  # noqa: E402


DATA_ROOT = ROOT / "data" / "task_cases"
OUTPUT_ROOT = ROOT / "outputs" / "validation" / "skill_marginal_utility"


@dataclass(frozen=True)
class VariantSpec:
    name: str
    skill: SkillPackage | None
    defect: str | None = None
    skill_text: str = ""
    skill_dir: Path | None = None
    runtime_source: str = "variant_skill_package"
    active_pointer_snapshot: dict[str, Any] | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_repair_policy() -> dict[str, str]:
    payload = json.loads((ROOT / "revision" / "repair_policy.json").read_text(encoding="utf-8"))
    return {str(key): str(value) for key, value in payload.get("repair_actions", {}).items()}


def render_skill(case_id: str, task_family: str, capabilities: tuple[str, ...], version: str) -> str:
    lines = [
        f"# Defensive Secure Review Skill {case_id} {version}",
        "",
        "Safety boundary: defensive review only. Do not generate exploits, attack chains, or real-target automation.",
        "",
        f"Task family: `{task_family}`",
        "",
        "## Capabilities",
        "",
    ]
    for capability_id in capabilities:
        cap = CAPABILITY_SPECS[capability_id]
        lines.extend([f"### {cap.capability_id}: {cap.title}", f"- Evidence: {cap.evidence_hint}", f"- Fix: {cap.fix_hint}", ""])
    return "\n".join(lines)


def verify_case(case, report: dict[str, Any]) -> dict[str, Any]:
    return verify_controlled_execution(
        case.expected_capabilities,
        report,
        feedback_overrides=case.verifier_contract.get("feedback_overrides", {}),
        target_text=case.target_asset,
    ).to_dict()


def build_run_metadata(*, case_id: str, backend: str, variant: str, target_path: Path, skill_path: Path | None, manifest_path: Path | None, verifier: dict[str, Any], cost: float | None, tokens: int | None, model: str, task_family: str, activated_capability_group: str, out_of_scope: bool, unsupported_task_family: str | None, prompt_hash: str = "none", active_pointer_snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "run_id": f"{case_id}::{backend}::{variant}",
        "case_id": case_id,
        "backend": backend,
        "variant": variant,
        "task_family": task_family,
        "activated_capability_group": activated_capability_group,
        "out_of_scope": out_of_scope,
        "unsupported_task_family": unsupported_task_family,
        "skill_package_path": str(skill_path.parent) if skill_path is not None and skill_path.exists() else "none",
        "target_hash": hash_file_sha256(target_path),
        "skill_hash": hash_file_sha256(skill_path) if skill_path is not None and skill_path.exists() else "none",
        "manifest_hash": hash_json_file_sha256(manifest_path) if manifest_path is not None and manifest_path.exists() else "none",
        "prompt_hash": prompt_hash,
        "model": model,
        "verifier_hash": build_verifier_hash(),
        "schema_version": SCHEMA_VERSION,
        "timestamp": utc_now(),
        "cost": cost,
        "tokens": tokens,
        "cost_reason": "offline prototype does not compute monetary billing" if cost is None else "measured",
        "tokens_reason": "estimated from skill text only" if tokens is not None else "no token source available",
        "verifier_feedback_type": verifier.get("feedback_type"),
        "active_pointer_snapshot": dict(active_pointer_snapshot or {}),
    }


def run_variant(case, backend: str, spec: VariantSpec, out_dir: Path) -> tuple[dict[str, Any], int, dict[str, Any]]:
    runner = get_backend_runner(backend, project_root=ROOT)
    skill_text = spec.skill_text
    skill_dir = spec.skill_dir
    if spec.skill is not None and not skill_text:
        skill_text = render_skill(case.case_id, case.task_family, spec.skill.capabilities, spec.skill.version)
    if spec.skill is not None and skill_dir is None:
        skill_dir = out_dir / "skill"
        write_text(skill_dir / "SKILL.md", skill_text)
        write_json(skill_dir / "manifest.json", spec.skill.to_dict())
    target_path = out_dir / "target" / "target.md"
    write_text(target_path, case.target_asset)
    activation = resolve_task_conditioned_activation(spec.skill, case) if spec.skill is not None else {
        "task_family": case.task_family,
        "activated_capability_group": "no_skill",
        "out_of_scope": False,
        "unsupported_task_family": None,
        "supported_task_families": [],
    }
    context = RunnerContext(
        scenario_id=case.case_id,
        backend=backend,
        target_dir=out_dir / "target",
        output_dir=out_dir / "agent",
        attempt_id=spec.name,
        skill_package=spec.skill,
        task_case=case,
        metadata={
            "defect": spec.defect,
            "skill_dir": skill_dir,
            "task_family": case.task_family,
            "activated_capability_group": activation["activated_capability_group"],
            "supported_task_families": activation["supported_task_families"],
            "out_of_scope": activation["out_of_scope"],
            "unsupported_task_family": activation["unsupported_task_family"],
        } if skill_dir else {"defect": spec.defect},
    )
    result = runner.run(context)
    execution = result.report.to_dict()
    verifier = verify_case(case, execution)
    write_json(out_dir / "verifier_report.json", verifier)
    cost_tokens = skill_cost(spec.skill, skill_text) if spec.skill is not None else 0
    metadata = build_run_metadata(
        case_id=case.case_id,
        backend=backend,
        variant=spec.name,
        target_path=target_path,
        skill_path=skill_dir / "SKILL.md" if skill_dir else None,
        manifest_path=skill_dir / "manifest.json" if skill_dir else None,
        verifier=verifier,
        cost=None,
        tokens=cost_tokens if spec.skill is not None else None,
        model=backend if backend != "live_llm_text" else "llm",
        task_family=case.task_family,
        activated_capability_group=activation["activated_capability_group"],
        out_of_scope=bool(activation["out_of_scope"]),
        unsupported_task_family=activation["unsupported_task_family"],
        active_pointer_snapshot=spec.active_pointer_snapshot,
    )
    write_json(out_dir / "run_metadata.json", metadata)
    write_evidence_bundle(
        out_dir / "evidence_bundle",
        case_id=case.case_id,
        backend=backend,
        variant=spec.name,
        target_text=case.target_asset,
        skill=spec.skill,
        skill_text=skill_text,
        execution=execution,
        verifier=verifier,
        status="completed",
        provenance={
            "runtime_source": "no_skill" if spec.skill is None else spec.runtime_source,
            "skill_package_path": str(skill_dir) if skill_dir else "none",
            "skill_version": spec.skill.version if spec.skill is not None else "none",
            "manifest_hash": metadata["manifest_hash"],
            "skill_hash": metadata["skill_hash"],
            "run_id": metadata["run_id"],
            "schema_version": metadata["schema_version"],
            "task_family": case.task_family,
            "activated_capability_group": activation["activated_capability_group"],
            "out_of_scope": activation["out_of_scope"],
            "unsupported_task_family": activation["unsupported_task_family"],
        },
    )
    return verifier, cost_tokens, metadata


def build_repaired_skill(case, v1_report: dict[str, Any]) -> tuple[SkillPackage, dict[str, Any], dict[str, Any]]:
    context = RepairContext(
        scenario_id=case.case_id,
        task_family=case.task_family,
        current_capabilities=case.v1_capabilities,
        expected_capabilities=case.expected_capabilities,
        verifier_report=VerifierReport.from_dict(v1_report),
        repair_policy=load_repair_policy(),
    )
    after_capabilities, patch, gate = build_patch_and_gate(context)
    skill = SkillPackage(
        skill_id=case.case_id,
        version="v2",
        task_family=case.task_family,
        capabilities=after_capabilities,
        output_contract=("capability_id", "evidence_span", "recommended_fix"),
        trace_contract=("trajectory.jsonl", "target_reads.json", "skill_reads.json"),
        metadata={"repair_action": patch.repair_action},
    )
    return skill, patch.to_dict(), gate.to_dict()


def default_variant_specs(case) -> list[VariantSpec]:
    v1 = SkillPackage(
        skill_id=case.case_id,
        version="v1",
        task_family=case.task_family,
        capabilities=case.v1_capabilities,
        output_contract=("capability_id", "evidence_span", "recommended_fix"),
        trace_contract=("trajectory.jsonl", "target_reads.json", "skill_reads.json"),
    )
    verifier_v1 = verify_case(case, {"attempt": "skill_v1", "backend": "offline_deterministic", "findings": []})
    v2_skill, _, _ = build_repaired_skill(case, verifier_v1)
    upper = SkillPackage(
        skill_id=case.case_id,
        version="upper_bound",
        task_family=case.task_family,
        capabilities=case.expected_capabilities,
        output_contract=("capability_id", "evidence_span", "recommended_fix"),
        trace_contract=("trajectory.jsonl", "target_reads.json", "skill_reads.json"),
        metadata={"upper_bound": True},
    )
    return [
        VariantSpec(name="no_skill", skill=None, runtime_source="no_skill"),
        VariantSpec(name="skill_v1", skill=v1, defect=case.a1_defect, runtime_source="variant_skill_package"),
        VariantSpec(name="skill_v2", skill=v2_skill, runtime_source="variant_skill_package"),
        VariantSpec(name="upper_bound", skill=upper, runtime_source="variant_skill_package"),
    ]


def candidate_package_dir_for_case(case_id: str) -> Path | None:
    candidate_dir = ROOT / "outputs" / "skill_evolution_lab" / "secure_code_review" / "candidates" / f"{case_id}__v3_candidate_001"
    if (candidate_dir / "manifest.json").exists() and (candidate_dir / "SKILL.md").exists():
        return candidate_dir
    return None


def installed_variant_specs(case, installed_skill_id: str) -> tuple[list[VariantSpec], list[dict[str, Any]]]:
    registry = load_registry(ROOT)
    pointer = load_active_pointer(ROOT, installed_skill_id)
    unavailable: list[dict[str, Any]] = []
    specs: list[VariantSpec] = []
    active_snapshot = dict(pointer)
    for version_name, variant_name in (("v1", "installed_v1"), ("v2", "installed_v2")):
        version_dir = skill_version_dir(ROOT, installed_skill_id, version_name)
        if not version_dir.exists():
            unavailable.append({"variant": variant_name, "reason": f"installed version `{version_name}` is missing"})
            continue
        package, skill_text, _manifest = read_skill_version(version_dir)
        specs.append(
            VariantSpec(
                name=variant_name,
                skill=package,
                skill_text=skill_text,
                skill_dir=version_dir,
                runtime_source="installed_variant_package",
                active_pointer_snapshot=active_snapshot,
            )
        )
    active_version = str(pointer.get("active_version") or "")
    if active_version:
        active_dir = skill_version_dir(ROOT, installed_skill_id, active_version)
        if active_dir.exists():
            package, skill_text, _manifest = read_skill_version(active_dir)
            specs.append(
                VariantSpec(
                    name="active_installed",
                    skill=package,
                    skill_text=skill_text,
                    skill_dir=active_dir,
                    runtime_source="active_installed_package",
                    active_pointer_snapshot=active_snapshot,
                )
            )
        else:
            unavailable.append({"variant": "active_installed", "reason": f"active version `{active_version}` directory is missing"})
    else:
        unavailable.append({"variant": "active_installed", "reason": "active pointer is empty"})
    candidate_dir = candidate_package_dir_for_case(case.case_id)
    if candidate_dir is not None:
        package, skill_text, _manifest = read_skill_version(candidate_dir)
        specs.append(
            VariantSpec(
                name="candidate_v3_package",
                skill=package,
                skill_text=skill_text,
                skill_dir=candidate_dir,
                runtime_source="candidate_package",
                active_pointer_snapshot=active_snapshot,
            )
        )
    else:
        unavailable.append({"variant": "candidate_v3_package", "reason": f"no candidate package exists for `{case.case_id}`"})
    return specs, unavailable


def run_variant_set(case, backend: str, variant_specs: list[VariantSpec], output_root: Path) -> tuple[dict[str, dict[str, Any]], dict[str, int], dict[str, dict[str, Any]]]:
    case_dir = output_root / case.case_id
    reports: dict[str, dict[str, Any]] = {}
    costs: dict[str, int] = {}
    metadata: dict[str, dict[str, Any]] = {}
    for spec in variant_specs:
        reports[spec.name], costs[spec.name], metadata[spec.name] = run_variant(case, backend, spec, case_dir / spec.name)
    return reports, costs, metadata


def run_case(case, backend: str, output_root: Path) -> dict[str, Any]:
    case_dir = output_root / case.case_id
    specs = default_variant_specs(case)
    reports, costs, metadata = run_variant_set(case, backend, specs, output_root)
    _, patch, gate = build_repaired_skill(case, reports["skill_v1"])
    write_json(case_dir / "repair_patch.json", patch)
    write_json(case_dir / "qualification_decision.json", gate)
    result = build_marginal_utility_result(
        case_id=case.case_id,
        backend=backend,
        variant_reports=reports,
        variant_costs=costs,
        artifact_dir=case_dir,
        variant_metadata=metadata,
    )
    payload = result.to_dict()
    payload["safety_boundary"] = {
        "allowed": ["defensive_detection", "explanation", "fix_recommendation", "patch_validation"],
        "forbidden": ["exploit_generation", "attack_chain_execution", "unauthorized_target_testing"],
    }
    write_json(case_dir / "skill_marginal_utility.json", payload)
    return payload


def run_installed_case(case, backend: str, output_root: Path, installed_skill_id: str) -> dict[str, Any]:
    case_dir = output_root / case.case_id
    specs, unavailable = installed_variant_specs(case, installed_skill_id)
    if not specs:
        raise SystemExit(f"no installed variants are available for `{installed_skill_id}`")
    reports, costs, metadata = run_variant_set(case, backend, specs, output_root)
    scores = {name: score_from_verifier(report) for name, report in reports.items()}
    false_positives = {name: len(report.get("false_positive_capabilities", [])) for name, report in reports.items()}
    metrics: dict[str, float] = {}
    if "installed_v1" in scores and "installed_v2" in scores:
        metrics["installed_v2_over_installed_v1_gain"] = round(scores["installed_v2"] - scores["installed_v1"], 4)
    if "active_installed" in scores and "installed_v1" in scores:
        metrics["active_installed_over_installed_v1_gain"] = round(scores["active_installed"] - scores["installed_v1"], 4)
    if "active_installed" in scores and "installed_v2" in scores:
        metrics["active_installed_over_installed_v2_gain"] = round(scores["active_installed"] - scores["installed_v2"], 4)
    if "candidate_v3_package" in scores and "active_installed" in scores:
        metrics["candidate_v3_package_over_active_installed_gain"] = round(scores["candidate_v3_package"] - scores["active_installed"], 4)
    payload = {
        "case_id": case.case_id,
        "backend": backend,
        "source": "installed",
        "installed_skill_id": installed_skill_id,
        "variants": [spec.name for spec in specs],
        "scores": scores,
        "costs": costs,
        "false_positives": false_positives,
        "metrics": metrics,
        "run_metadata": metadata,
        "artifact_dir": str(case_dir),
        "unavailable_variants": unavailable,
    }
    write_json(case_dir / "installed_package_marginal_utility.json", payload)
    return payload


def compare_two_variants(case, backend: str, left: VariantSpec, right: VariantSpec, output_root: Path) -> dict[str, Any]:
    reports, costs, metadata = run_variant_set(case, backend, [left, right], output_root)
    left_score = score_from_verifier(reports[left.name])
    right_score = score_from_verifier(reports[right.name])
    return {
        "case_id": case.case_id,
        "backend": backend,
        "baseline_variant": left.name,
        "candidate_variant": right.name,
        "baseline_score": left_score,
        "candidate_score": right_score,
        "score_delta": round(right_score - left_score, 4),
        "baseline_cost_tokens": costs[left.name],
        "candidate_cost_tokens": costs[right.name],
        "false_positive_delta": float(len(reports[right.name].get("false_positive_capabilities", [])) - len(reports[left.name].get("false_positive_capabilities", []))),
        "schema_error_delta": float(len(reports[right.name].get("schema_errors", [])) - len(reports[left.name].get("schema_errors", []))),
        "artifacts": {
            left.name: str((output_root / case.case_id / left.name).resolve()),
            right.name: str((output_root / case.case_id / right.name).resolve()),
        },
        "run_metadata": metadata,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    if payload.get("source") == "installed":
        lines = [
            "# Installed Package Marginal Utility Report",
            "",
            f"- Backend: `{payload['backend']}`",
            f"- Cases: `{payload['case_count']}`",
            "",
            "| Case | Variants | Key Gains |",
            "|---|---|---|",
        ]
        for row in payload["results"]:
            metric_text = ", ".join(f"{key}={value}" for key, value in row.get("metrics", {}).items()) or "none"
            lines.append(f"| {row['case_id']} | {', '.join(row.get('variants', []))} | {metric_text} |")
        lines.extend(
            [
                "",
                "## Boundary",
                "",
                "This report compares real installed package variants and records active pointer snapshots plus package hashes.",
            ]
        )
        return "\n".join(lines) + "\n"
    lines = [
        "# Skill Marginal Utility Report",
        "",
        f"- Backend: `{payload['backend']}`",
        f"- Cases: `{payload['case_count']}`",
        "",
        "| Case | v2 over v1 | v2 over no skill | Gap to upper | Cost delta | FP delta |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in payload["results"]:
        metrics = row["metrics"]
        lines.append(
            f"| {row['case_id']} | {metrics['v2_over_v1_gain']} | {metrics['v2_over_no_skill_gain']} | "
            f"{metrics['gap_to_upper_bound']} | {metrics['cost_delta']} | {metrics['false_positive_delta']} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This is a ReSkill-style marginal utility comparison over controlled defensive review cases. It does not claim exploit capability or broad real-world vulnerability discovery.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run no-skill/v1/v2/upper-bound marginal utility comparisons.")
    parser.add_argument("--cases", default="upload,data_quality")
    parser.add_argument("--backend", default="offline_deterministic", choices=["offline_deterministic", "non_oracle_local_semantic"])
    parser.add_argument("--source", default="constructed", choices=["constructed", "installed"])
    parser.add_argument("--installed-skill", default="secure_code_review")
    parser.add_argument("--output-dir", default=str(OUTPUT_ROOT))
    args = parser.parse_args(argv)

    selected = select_controlled_task_cases(DATA_ROOT, args.cases)
    output_root = Path(args.output_dir)
    if args.source == "installed":
        results = [run_installed_case(case, args.backend, output_root, args.installed_skill) for case in selected]
    else:
        results = [run_case(case, args.backend, output_root) for case in selected]
    summary = {
        "run_id": f"skill_marginal_utility_{args.source}_{args.backend}",
        "backend": args.backend,
        "source": args.source,
        "installed_skill_id": args.installed_skill if args.source == "installed" else None,
        "case_count": len(results),
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now(),
        "results": results,
        "claim_boundary": "bounded defensive secure-code-review marginal utility evidence",
    }
    summary_name = "installed_package_marginal_utility" if args.source == "installed" else "skill_marginal_utility"
    write_json(output_root / f"{summary_name}.json", summary)
    write_text(output_root / f"{summary_name}.md", render_markdown(summary))
    print(json.dumps({"output": str(output_root / f"{summary_name}.json"), "case_count": len(results), "source": args.source}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
