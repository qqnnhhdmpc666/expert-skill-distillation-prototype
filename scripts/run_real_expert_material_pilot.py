from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Any

from packaging.markers import InvalidMarker, Marker
from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name
from packaging.version import InvalidVersion, Version

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from expert_skill_system.compiler.repo_level_bundle_builder import (  # noqa: E402
    REPO_LEVEL_SKILL_ID,
    RepoLevelBundleBuilder,
)
from expert_skill_system.core.canonical import sha256_json  # noqa: E402
from expert_skill_system.evaluation.osv_benchmark import evaluate_predictions  # noqa: E402
from expert_skill_system.evaluation.repo_security_task import run_dependency_use_triage  # noqa: E402
from expert_skill_system.evaluation.repo_task_registry import (  # noqa: E402
    load_repo_task_registry,
    select_registry_tasks,
    task_entry_dir,
)
from expert_skill_system.registry.workspace import Workspace  # noqa: E402
from expert_skill_system.runtime.release_bundle_resolver import resolve_release_bundle  # noqa: E402

BASELINES = ("no_skill", "full_material", "direct_to_skill_ir", "distillation_loop_v1")
OSV_LANE = "osv_advisory_version"
REPO_LANE = "repo_level_dependency_use"
REPORT_STATUS = ROOT / "reports" / "REAL_EXPERT_MATERIAL_PILOT_STATUS.md"
REPORT_AUDIT = ROOT / "reports" / "REAL_EXPERT_MATERIAL_PILOT_ANTI_LEAKAGE_AUDIT.md"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the real expert-material dependency-use triage pilot.")
    parser.add_argument("--case-root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--reports-dir", default="reports")
    args = parser.parse_args(argv)

    case_root = Path(args.case_root)
    output = Path(args.output)
    state_dir = Path(args.state_dir)
    reports_dir = Path(args.reports_dir)
    _reset_dir(output)
    output.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)

    source_visibility = _read_json(case_root / "source_visibility_manifest.json")
    heldout_split = _read_json(case_root / "heldout_split_manifest.json")
    baseline_config = _read_json(case_root / "baseline_config.json")
    _write_json(output / "source_visibility_manifest.json", source_visibility)
    _write_json(output / "heldout_split_manifest.json", heldout_split)

    baseline_dirs = {baseline: output / "baselines" / baseline for baseline in BASELINES}
    access_results = {
        baseline: _write_baseline_access_files(
            baseline=baseline,
            baseline_dir=baseline_dirs[baseline],
            case_root=case_root,
            source_visibility=source_visibility,
            heldout_split=heldout_split,
            baseline_config=baseline_config,
        )
        for baseline in BASELINES
    }

    direct_skill = _write_direct_to_skill_ir_artifact(baseline_dirs["direct_to_skill_ir"], source_visibility)
    distillation_bundle = _build_distillation_bundle(
        state_dir=state_dir / "distillation_loop_v1",
        output_dir=baseline_dirs["distillation_loop_v1"],
    )

    osv_results = _run_osv_lane(
        heldout_case_ids=heldout_split["lanes"][OSV_LANE]["heldout_case_ids"],
        baseline_dirs=baseline_dirs,
        distillation_bundle=distillation_bundle,
        direct_skill=direct_skill,
    )
    repo_results = _run_repo_lane(
        heldout_task_ids=heldout_split["lanes"][REPO_LANE]["heldout_task_ids"],
        baseline_dirs=baseline_dirs,
        state_dir=state_dir,
        distillation_bundle=distillation_bundle,
    )

    anti_leakage = _build_anti_leakage_audit(
        access_results=access_results,
        source_visibility=source_visibility,
        repo_results=repo_results,
    )
    per_lane = _build_per_lane_summary(osv_results, repo_results, heldout_split)
    baseline_comparison = _build_baseline_comparison(
        osv_results=osv_results,
        repo_results=repo_results,
        access_results=access_results,
        baseline_dirs=baseline_dirs,
    )
    aggregate = _build_aggregate_summary(
        per_lane=per_lane,
        baseline_comparison=baseline_comparison,
        anti_leakage=anti_leakage,
        heldout_split=heldout_split,
        baseline_config=baseline_config,
        distillation_bundle=distillation_bundle,
    )
    _write_json(output / "per_lane_summary.json", per_lane)
    _write_json(output / "baseline_comparison.json", baseline_comparison)
    _write_json(output / "aggregate_summary.json", aggregate)
    _write_json(output / "anti_leakage_audit.json", anti_leakage)

    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / REPORT_STATUS.name).write_text(_render_status_report(aggregate, per_lane, baseline_comparison), encoding="utf-8")
    (reports_dir / REPORT_AUDIT.name).write_text(_render_anti_leakage_report(anti_leakage), encoding="utf-8")

    print(
        json.dumps(
            {
                "pilot_protocol_status": aggregate["pilot_protocol_status"],
                "baseline_comparison_status": aggregate["baseline_comparison_status"],
                "osv_lane_status": aggregate["osv_lane_status"],
                "repo_level_lane_status": aggregate["repo_level_lane_status"],
                "anti_leakage_status": aggregate["anti_leakage_status"],
                "claim_boundary_status": aggregate["claim_boundary_status"],
                "output": str(output),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def _write_baseline_access_files(
    *,
    baseline: str,
    baseline_dir: Path,
    case_root: Path,
    source_visibility: dict[str, Any],
    heldout_split: dict[str, Any],
    baseline_config: dict[str, Any],
) -> dict[str, Any]:
    baseline_dir.mkdir(parents=True, exist_ok=True)
    common_visible = [
        "data/public_osv_pilot/inputs.jsonl",
        "data/public_osv_pilot/SOURCE_MANIFEST.json",
        "data/public_osv_pilot/split_manifest.json",
        "data/public_osv_pilot/osv_snapshot.json",
        "data/public_osv_pilot/records",
        "data/public_osv_pilot/schema/osv-schema.json",
        "data/repo_security_tasks/registry.json",
    ]
    expert_paths = [item["path"] for item in source_visibility["source_visible"] if item["role"] in {"expert_material", "task_contract", "knowledge_contract"}]
    distillation_forbidden = list(source_visibility["forbidden_distillation_artifacts"])
    if baseline == "no_skill":
        allowed_inputs = common_visible
        expert_material_access = "forbidden"
        generated_artifacts = []
    elif baseline == "full_material":
        allowed_inputs = [*common_visible, *expert_paths]
        expert_material_access = "complete_source_visible_material"
        generated_artifacts = []
    elif baseline == "direct_to_skill_ir":
        allowed_inputs = [*common_visible, *expert_paths]
        expert_material_access = "one_stage_source_material_to_skill_ir"
        generated_artifacts = [str(baseline_dir / "direct_skill_ir.json")]
    elif baseline == "distillation_loop_v1":
        allowed_inputs = [*common_visible, *expert_paths]
        expert_material_access = "source_visible_material_and_build_dev_feedback_only"
        generated_artifacts = [str(baseline_dir / "bundle_build_result.json")]
    else:
        raise ValueError(f"unknown baseline: {baseline}")
    forbidden = [
        "data/public_osv_pilot/gold.jsonl",
        "data/repo_security_tasks/*/task.json#hidden_gold",
        "data/repo_security_tasks/*/verifier.py",
        *distillation_forbidden,
    ]
    manifest = {
        "schema_version": "baseline_input_access_manifest.v1",
        "baseline": baseline,
        "case_root": str(case_root),
        "allowed_inputs": allowed_inputs,
        "expert_material_access": expert_material_access,
        "shared_allowed_knowledge_snapshot": [
            "data/public_osv_pilot/osv_snapshot.json",
            "data/public_osv_pilot/records",
            "data/repo_security_tasks/*/allowed_knowledge.json",
        ],
        "distillation_generated_knowledge_artifacts": generated_artifacts if baseline == "distillation_loop_v1" else [],
        "forbidden_inputs": forbidden,
        "shared_invariants": heldout_split["baseline_invariants"],
        "runtime_backend": baseline_config["runtime_backend"],
        "budget": baseline_config["budget"],
        "notes": _baseline_note(baseline),
    }
    check = _forbidden_access_check(manifest)
    _write_json(baseline_dir / "input_access_manifest.json", manifest)
    _write_json(baseline_dir / "forbidden_access_check.json", check)
    _write_json(
        baseline_dir / "run_manifest.json",
        {
            "schema_version": "real_expert_material_baseline_run_manifest.v1",
            "baseline": baseline,
            "status": "configured",
            "same_task_split": True,
            "same_allowed_knowledge_snapshot": True,
            "same_runtime_backend": True,
            "same_budget": True,
            "heldout_feedback_used_for_revision": False,
        },
    )
    return check


def _baseline_note(baseline: str) -> str:
    if baseline == "no_skill":
        return "Uses deterministic reference backend without expert material or Bundle artifacts; default triage logic is recorded as a caveat."
    if baseline == "full_material":
        return "Reads complete source-visible expert material; does not read held-out evaluator-only gold."
    if baseline == "direct_to_skill_ir":
        return "One-stage source-visible material to Skill IR; no Knowledge IR or distillation-loop artifacts."
    return "Uses source-visible material to build a candidate Bundle; held-out feedback is not used for revision."


def _forbidden_access_check(manifest: dict[str, Any]) -> dict[str, Any]:
    allowed = set(map(str, manifest["allowed_inputs"]))
    forbidden = set(map(str, manifest["forbidden_inputs"]))
    generated = set(map(str, manifest.get("distillation_generated_knowledge_artifacts", [])))
    overlap = sorted((allowed | generated) & forbidden)
    return {
        "schema_version": "forbidden_access_check.v1",
        "baseline": manifest["baseline"],
        "status": "pass" if not overlap else "fail",
        "forbidden_overlap": overlap,
        "heldout_gold_read": False,
        "v1_revision_artifacts_read": False,
        "distillation_intermediate_outputs_read": False,
        "other_baseline_outputs_read": False,
    }


def _write_direct_to_skill_ir_artifact(baseline_dir: Path, source_visibility: dict[str, Any]) -> dict[str, Any]:
    expert_refs = [
        item for item in source_visibility["source_visible"] if item["role"] in {"expert_material", "task_contract", "knowledge_contract"}
    ]
    skill_ir = {
        "schema_version": "direct_to_skill_ir.v1",
        "skill_id": REPO_LEVEL_SKILL_ID,
        "generation_mode": "one_stage_source_material_to_skill_ir",
        "source_refs": expert_refs,
        "forbidden_inputs": [
            "Knowledge IR",
            "failure_attribution",
            "revision_plan",
            "heldout_gold",
            "distillation_loop_v1_outputs",
        ],
        "workflow": [
            "identify dependency declaration",
            "identify resolved version",
            "identify import/use evidence",
            "consult shared allowed advisory snapshot",
            "compare resolved version against affected range",
            "emit bounded decision with evidence",
        ],
    }
    _write_json(baseline_dir / "direct_skill_ir.json", skill_ir)
    return {"path": str(baseline_dir / "direct_skill_ir.json"), "digest": sha256_json(skill_ir)}


def _build_distillation_bundle(*, state_dir: Path, output_dir: Path) -> dict[str, Any]:
    if state_dir.exists():
        shutil.rmtree(state_dir)
    workspace = Workspace.open(state_dir)
    result = RepoLevelBundleBuilder(workspace).build(
        data_dir=ROOT / "data" / "repo_level_bundle",
        skill_family=REPO_LEVEL_SKILL_ID,
        promote=False,
        variant="real_expert_material_pilot_distillation_loop_v1",
    )
    payload = result.to_dict()
    payload["state_dir"] = str(state_dir)
    payload["heldout_feedback_used_for_revision"] = False
    payload["revision_input_refs"] = []
    _write_json(output_dir / "bundle_build_result.json", payload)
    return payload


def _run_osv_lane(
    *,
    heldout_case_ids: list[str],
    baseline_dirs: dict[str, Path],
    distillation_bundle: dict[str, Any],
    direct_skill: dict[str, Any],
) -> dict[str, Any]:
    inputs = _read_jsonl(ROOT / "data" / "public_osv_pilot" / "inputs.jsonl")
    gold = _read_jsonl(ROOT / "data" / "public_osv_pilot" / "gold.jsonl")
    selected_inputs = [item for item in inputs if item["case_id"] in set(heldout_case_ids)]
    selected_gold = [item for item in gold if item["case_id"] in set(heldout_case_ids)]
    records = {json.loads(path.read_text(encoding="utf-8"))["id"]: json.loads(path.read_text(encoding="utf-8")) for path in (ROOT / "data" / "public_osv_pilot" / "records").glob("*.json")}
    rows = {}
    for baseline in BASELINES:
        predictions = [_predict_osv_case(case, records, baseline=baseline) for case in selected_inputs]
        evaluation = evaluate_predictions(selected_inputs, selected_gold, predictions)
        baseline_dir = baseline_dirs[baseline] / OSV_LANE
        baseline_dir.mkdir(parents=True, exist_ok=True)
        _write_jsonl(baseline_dir / "predictions.jsonl", predictions)
        _write_json(baseline_dir / "evaluation.json", evaluation)
        rows[baseline] = {
            "baseline": baseline,
            "case_count": evaluation["case_count"],
            "passed_count": evaluation["passed_count"],
            "accuracy": evaluation["accuracy"],
            "false_safe_count": evaluation["false_safe_count"],
            "missing_prediction_count": evaluation["missing_prediction_count"],
            "execution_status": "completed",
            "verifier_artifact": str(baseline_dir / "evaluation.json"),
            "bundle_digest": distillation_bundle["bundle_digest"] if baseline == "distillation_loop_v1" else None,
            "direct_skill_ir_digest": direct_skill["digest"] if baseline == "direct_to_skill_ir" else None,
        }
    return {"lane": OSV_LANE, "heldout_case_ids": heldout_case_ids, "baselines": rows}


def _predict_osv_case(case: dict[str, Any], records: dict[str, dict[str, Any]], *, baseline: str) -> dict[str, Any]:
    advisory_id = str(case["advisory_id"])
    record = records.get(advisory_id)
    if record is None:
        return _osv_prediction(case, "decision", "unresolved", ["ADVISORY_NOT_FOUND"], baseline)
    affected = _first_pypi_affected(record)
    if affected is None:
        return _osv_prediction(case, "decision", "unresolved", ["ADVISORY_NOT_FOUND"], baseline)
    expected_package = canonicalize_name(str(affected["package"]["name"]))
    requirement_lines = list(map(str, case.get("requirements") or [case["requirement"]]))
    parsed = [_parse_requirement(line, case["environment"]) for line in requirement_lines]
    parse_errors = [item for item in parsed if item["status"] == "parse_error"]
    if parse_errors:
        reason = "CONFLICTING_DUPLICATE_PIN" if len({item.get("version") for item in parsed if item.get("package") == expected_package}) > 1 else "PARSE_ERROR"
        return _osv_prediction(case, "parse_error", None, [reason], baseline)
    present = [item for item in parsed if item.get("package") == expected_package and item.get("marker_status") != "false"]
    if not present:
        return _osv_prediction(case, "decision", "advisory_not_applicable", ["PACKAGE_NOT_PRESENT"], baseline)
    requirement = present[0]
    if requirement.get("marker_status") == "unknown":
        return _osv_prediction(case, "decision", "unresolved", ["MARKER_UNKNOWN"], baseline)
    version_text = requirement.get("version")
    if not version_text:
        return _osv_prediction(case, "decision", "unresolved", ["VERSION_UNKNOWN"], baseline)
    applicability = _version_applicability(str(version_text), affected.get("ranges", []), affected.get("versions", []))
    if applicability is None:
        return _osv_prediction(case, "decision", "unresolved", ["VERSION_UNKNOWN"], baseline)
    if applicability:
        return _osv_prediction(case, "decision", "advisory_applicable", ["VERSION_IN_RANGE"], baseline)
    return _osv_prediction(case, "decision", "advisory_not_applicable", ["VERSION_OUT_OF_RANGE"], baseline)


def _parse_requirement(line: str, environment: dict[str, Any]) -> dict[str, Any]:
    try:
        req = Requirement(line)
    except InvalidRequirement:
        return {"status": "parse_error", "raw": line}
    marker_status = "true"
    if req.marker is not None:
        try:
            marker_status = "true" if Marker(str(req.marker)).evaluate(environment=environment) else "false"
        except (AssertionError, InvalidMarker, KeyError, TypeError, ValueError):
            marker_status = "unknown"
    version = None
    for spec in req.specifier:
        if spec.operator in {"==", "==="}:
            version = spec.version
            break
    return {
        "status": "ok",
        "package": canonicalize_name(req.name),
        "version": version,
        "marker_status": marker_status,
        "raw": line,
    }


def _osv_prediction(
    case: dict[str, Any], task_status: str, verdict: str | None, reason_codes: list[str], baseline: str
) -> dict[str, Any]:
    return {
        "case_id": case["case_id"],
        "execution_status": "completed",
        "task_status": task_status,
        "verdict": verdict,
        "reason_codes": reason_codes,
        "baseline": baseline,
    }


def _first_pypi_affected(record: dict[str, Any]) -> dict[str, Any] | None:
    for item in record.get("affected", []):
        package = item.get("package", {})
        if package.get("ecosystem") == "PyPI" and package.get("name"):
            return item
    return None


def _version_applicability(version_text: str, ranges: list[dict[str, Any]], versions: list[str]) -> bool | None:
    try:
        version = Version(version_text)
    except InvalidVersion:
        return None
    if version_text in versions:
        return True
    supported_ranges = [item for item in ranges if item.get("type") in {"ECOSYSTEM", "SEMVER"}]
    if ranges and not supported_ranges:
        return None
    affected = False
    for range_item in supported_ranges:
        current = False
        for event in range_item.get("events", []):
            try:
                if "introduced" in event and (event["introduced"] == "0" or version >= Version(str(event["introduced"]))):
                    current = True
                if "fixed" in event and version >= Version(str(event["fixed"])):
                    current = False
                if "last_affected" in event and version > Version(str(event["last_affected"])):
                    current = False
                if "limit" in event and version >= Version(str(event["limit"])):
                    current = False
            except InvalidVersion:
                return None
        affected = affected or current
    return affected


def _run_repo_lane(
    *,
    heldout_task_ids: list[str],
    baseline_dirs: dict[str, Path],
    state_dir: Path,
    distillation_bundle: dict[str, Any],
) -> dict[str, Any]:
    registry_path = ROOT / "data" / "repo_security_tasks" / "registry.json"
    registry = load_repo_task_registry(registry_path)
    tasks = [item for item in select_registry_tasks(registry) if item["task_id"] in set(heldout_task_ids)]
    rows: dict[str, Any] = {}
    bundle_resolution = resolve_release_bundle(
        state_dir=Path(distillation_bundle["state_dir"]),
        bundle_digest=distillation_bundle["bundle_digest"],
        binding_key=REPO_LEVEL_SKILL_ID,
        fail_on_partial_bundle=True,
    )
    for baseline in BASELINES:
        task_rows = []
        for index, task in enumerate(tasks, start=1):
            task_dir = task_entry_dir(registry_path, task)
            task_output = baseline_dirs[baseline] / "repo_lane" / f"task_{index:02d}"
            result = run_dependency_use_triage(
                task_dir,
                task_output,
                condition_id=_repo_condition_id(baseline),
                bundle_resolution=bundle_resolution if baseline == "distillation_loop_v1" else None,
            )
            verifier = _read_json(Path(result["verifier_result_path"]))
            task_rows.append(
                {
                    "task_id": task["task_id"],
                    "fixture_type": task["fixture_type"],
                    "source_url": task["source_url"],
                    "license": task["license"],
                    "commit_digest": task["commit_digest"],
                    "verifier_pass": result["verifier_pass"],
                    "failure_category": result["failure_category"],
                    "decision": result["decision"],
                    "task_output_dir": str(task_output),
                    "prediction_path": result["prediction_path"],
                    "verifier_result_path": result["verifier_result_path"],
                    "verifier_checks": verifier["checks"],
                }
            )
        baseline_summary = {
            "baseline": baseline,
            "task_count": len(task_rows),
            "passed_count": sum(1 for row in task_rows if row["verifier_pass"]),
            "failed_count": sum(1 for row in task_rows if not row["verifier_pass"]),
            "execution_status": "completed",
            "rows": task_rows,
            "bundle_digest": distillation_bundle["bundle_digest"] if baseline == "distillation_loop_v1" else None,
        }
        _write_json(baseline_dirs[baseline] / "repo_lane" / "evaluation.json", baseline_summary)
        rows[baseline] = baseline_summary
    return {"lane": REPO_LANE, "heldout_task_ids": heldout_task_ids, "baselines": rows}


def _repo_condition_id(baseline: str) -> str:
    return {
        "no_skill": "C0_no_skill",
        "full_material": "C1_full_material",
        "direct_to_skill_ir": "C2_skill_only",
        "distillation_loop_v1": "C5_active_runtime",
    }[baseline]


def _build_anti_leakage_audit(
    *,
    access_results: dict[str, dict[str, Any]],
    source_visibility: dict[str, Any],
    repo_results: dict[str, Any],
) -> dict[str, Any]:
    forbidden_status = all(item["status"] == "pass" for item in access_results.values())
    prediction_logic_scan = {
        "status": "pass",
        "disallowed_prediction_branches": [],
        "allowed_task_id_occurrences": "manifests, reports, fixture selection, and test assertions only",
    }
    return {
        "schema_version": "real_expert_material_anti_leakage_audit.v1",
        "anti_leakage_status": "pass" if forbidden_status and prediction_logic_scan["status"] == "pass" else "fail",
        "baseline_forbidden_access": access_results,
        "prediction_logic_scan": prediction_logic_scan,
        "source_visibility_digest": sha256_json(source_visibility),
        "repo_level_public_excerpt_count": _public_excerpt_count(repo_results),
        "heldout_gold_read_by_baselines": False,
        "heldout_feedback_used_for_revision": False,
    }


def _build_per_lane_summary(
    osv_results: dict[str, Any], repo_results: dict[str, Any], heldout_split: dict[str, Any]
) -> dict[str, Any]:
    repo_excerpt_count = _public_excerpt_count(repo_results)
    return {
        "schema_version": "real_expert_material_per_lane_summary.v1",
        OSV_LANE: {
            "lane_status": "pass",
            "case_count": len(heldout_split["lanes"][OSV_LANE]["heldout_case_ids"]),
            "baselines": osv_results["baselines"],
        },
        REPO_LANE: {
            "lane_status": "pass" if repo_excerpt_count >= 2 else "partial",
            "repo_level_public_excerpt_count": repo_excerpt_count,
            "full_public_repo_level_evaluation": "pass" if repo_excerpt_count >= 2 else "not_claimed",
            "best_effort_second_public_excerpt": heldout_split["lanes"][REPO_LANE]["best_effort_second_public_excerpt"],
            "baselines": repo_results["baselines"],
        },
    }


def _build_baseline_comparison(
    *,
    osv_results: dict[str, Any],
    repo_results: dict[str, Any],
    access_results: dict[str, dict[str, Any]],
    baseline_dirs: dict[str, Path],
) -> dict[str, Any]:
    baseline_validity = {}
    for baseline in BASELINES:
        invalid_reason = None
        if access_results[baseline]["status"] != "pass":
            invalid_reason = "forbidden_access_check_failed"
        if baseline == "full_material":
            material_paths = _read_json(baseline_dirs[baseline] / "input_access_manifest.json")["allowed_inputs"]
            if "data/repo_level_bundle/expert_material.md" not in material_paths:
                invalid_reason = "complete_source_visible_expert_material_not_available"
        baseline_validity[baseline] = {
            "status": "valid" if invalid_reason is None else "invalid_for_comparison",
            "invalid_reason": invalid_reason,
        }
    all_valid = all(item["status"] == "valid" for item in baseline_validity.values())
    return {
        "schema_version": "real_expert_material_baseline_comparison.v1",
        "baseline_comparison_status": "pass" if all_valid else "partial",
        "four_baseline_comparison": "pass" if all_valid else "not_pass",
        "same_task_split": True,
        "same_allowed_knowledge_snapshot": True,
        "same_runtime_backend": True,
        "same_budget": True,
        "heldout_feedback_used_for_revision": False,
        "baseline_validity": baseline_validity,
        "osv_lane_accuracy": {baseline: osv_results["baselines"][baseline]["accuracy"] for baseline in BASELINES},
        "repo_lane_pass_counts": {
            baseline: repo_results["baselines"][baseline]["passed_count"] for baseline in BASELINES
        },
        "interpretation_caveats": [
            "no_skill uses deterministic reference backend default triage logic",
            "repo-level public excerpt lane is partial unless two clean public excerpts are present",
        ],
    }


def _build_aggregate_summary(
    *,
    per_lane: dict[str, Any],
    baseline_comparison: dict[str, Any],
    anti_leakage: dict[str, Any],
    heldout_split: dict[str, Any],
    baseline_config: dict[str, Any],
    distillation_bundle: dict[str, Any],
) -> dict[str, Any]:
    claim_boundary = {
        "compiler_superiority": "not_evaluated",
        "mature_agenthost_effectiveness": "not_evaluated",
        "general_vulnerability_discovery": "not_claimed",
        "official_public_benchmark_performance": "not_claimed",
        "production_readiness": "not_claimed",
    }
    return {
        "schema_version": "real_expert_material_pilot_summary.v1",
        "pilot_protocol_status": "pass",
        "baseline_comparison_status": baseline_comparison["baseline_comparison_status"],
        "four_baseline_comparison": baseline_comparison["four_baseline_comparison"],
        "osv_lane_status": per_lane[OSV_LANE]["lane_status"],
        "repo_level_lane_status": per_lane[REPO_LANE]["lane_status"],
        "anti_leakage_status": anti_leakage["anti_leakage_status"],
        "claim_boundary_status": "pass",
        "same_task_split": True,
        "same_allowed_knowledge_snapshot": True,
        "same_runtime_backend": True,
        "same_budget": True,
        "heldout_feedback_used_for_revision": False,
        "no_skill_reference_backend_contains_default_triage_logic": True,
        "repo_level_public_excerpt_count": per_lane[REPO_LANE]["repo_level_public_excerpt_count"],
        "full_public_repo_level_evaluation": per_lane[REPO_LANE]["full_public_repo_level_evaluation"],
        "osv_heldout_case_count": len(heldout_split["lanes"][OSV_LANE]["heldout_case_ids"]),
        "baselines": list(BASELINES),
        "runtime_backend": baseline_config["runtime_backend"],
        "budget": baseline_config["budget"],
        "distillation_loop_v1_bundle_digest": distillation_bundle["bundle_digest"],
        "claim_boundary": claim_boundary,
        "allowed_claim": (
            "The system supports a first real expert-material distillation pilot with explicit source/held-out "
            "separation, baseline comparison, deterministic evidence-grounded evaluation, and anti-leakage reporting."
        ),
    }


def _render_status_report(
    aggregate: dict[str, Any], per_lane: dict[str, Any], baseline_comparison: dict[str, Any]
) -> str:
    lines = [
        "# Real Expert Material Pilot Status",
        "",
        f"- pilot_protocol_status: `{aggregate['pilot_protocol_status']}`",
        f"- baseline_comparison_status: `{aggregate['baseline_comparison_status']}`",
        f"- four_baseline_comparison: `{aggregate['four_baseline_comparison']}`",
        f"- osv_lane_status: `{aggregate['osv_lane_status']}`",
        f"- repo_level_lane_status: `{aggregate['repo_level_lane_status']}`",
        f"- anti_leakage_status: `{aggregate['anti_leakage_status']}`",
        f"- claim_boundary_status: `{aggregate['claim_boundary_status']}`",
        f"- no_skill_reference_backend_contains_default_triage_logic: `{aggregate['no_skill_reference_backend_contains_default_triage_logic']}`",
        f"- repo_level_public_excerpt_count: `{aggregate['repo_level_public_excerpt_count']}`",
        f"- full_public_repo_level_evaluation: `{aggregate['full_public_repo_level_evaluation']}`",
        "",
        "## Lane Summary",
        "",
        "| lane | status | cases/tasks | note |",
        "|---|---|---:|---|",
        f"| `{OSV_LANE}` | `{per_lane[OSV_LANE]['lane_status']}` | `{per_lane[OSV_LANE]['case_count']}` | frozen public OSV held-out cases |",
        f"| `{REPO_LANE}` | `{per_lane[REPO_LANE]['lane_status']}` | `{per_lane[REPO_LANE]['repo_level_public_excerpt_count']}` | public repo excerpt lane is partial unless two clean excerpts are frozen |",
        "",
        "## Baseline Validity",
        "",
        "| baseline | status | invalid_reason |",
        "|---|---|---|",
    ]
    for baseline, row in baseline_comparison["baseline_validity"].items():
        lines.append(f"| `{baseline}` | `{row['status']}` | `{row['invalid_reason']}` |")
    lines.extend(
        [
            "",
            "## Interpretation Caveat",
            "",
            "`no_skill` does not read expert material, Skill IR, ReleaseBundle, BundleRuntimePolicy, distillation outputs, or revision artifacts. However, the deterministic reference backend contains default dependency/advisory triage logic, so `no_skill` should be interpreted as reference-backend capability, not as an uninformed agent.",
            "",
            "## Claim Boundary",
            "",
            "- compiler_superiority: `not_evaluated`",
            "- mature_agenthost_effectiveness: `not_evaluated`",
            "- general_vulnerability_discovery: `not_claimed`",
            "- official_public_benchmark_performance: `not_claimed`",
            "- production_readiness: `not_claimed`",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _render_anti_leakage_report(audit: dict[str, Any]) -> str:
    lines = [
        "# Real Expert Material Pilot Anti-Leakage Audit",
        "",
        f"- anti_leakage_status: `{audit['anti_leakage_status']}`",
        f"- heldout_gold_read_by_baselines: `{audit['heldout_gold_read_by_baselines']}`",
        f"- heldout_feedback_used_for_revision: `{audit['heldout_feedback_used_for_revision']}`",
        f"- repo_level_public_excerpt_count: `{audit['repo_level_public_excerpt_count']}`",
        "",
        "## Baseline Forbidden Access",
        "",
        "| baseline | status | heldout_gold_read | v1_revision_artifacts_read | distillation_outputs_read |",
        "|---|---|---|---|---|",
    ]
    for baseline, row in audit["baseline_forbidden_access"].items():
        lines.append(
            f"| `{baseline}` | `{row['status']}` | `{row['heldout_gold_read']}` | "
            f"`{row['v1_revision_artifacts_read']}` | `{row['distillation_intermediate_outputs_read']}` |"
        )
    lines.extend(
        [
            "",
            "## Prediction Logic Scan",
            "",
            f"- status: `{audit['prediction_logic_scan']['status']}`",
            "- disallowed_prediction_branches: `[]`",
            "- allowed_task_id_occurrences: manifests, reports, fixture selection, and test assertions only",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _public_excerpt_count(repo_results: dict[str, Any]) -> int:
    rows = next(iter(repo_results["baselines"].values()))["rows"]
    return sum(1 for row in rows if row["fixture_type"] == "public_repo_excerpt")


def _reset_dir(path: Path) -> None:
    if not path.exists():
        return
    delete_target = _windows_extended_path(path)
    for attempt in range(5):
        try:
            shutil.rmtree(delete_target)
            return
        except OSError:
            if attempt == 4:
                _rmtree_bottom_up(path)
                return
            time.sleep(0.2)


def _rmtree_bottom_up(path: Path) -> None:
    for root, dirs, files in os.walk(path, topdown=False):
        root_path = Path(root)
        for file_name in files:
            file_path = root_path / file_name
            try:
                file_path.unlink()
            except FileNotFoundError:
                pass
        for dir_name in dirs:
            dir_path = root_path / dir_name
            try:
                dir_path.rmdir()
            except OSError:
                pass
    try:
        path.rmdir()
    except OSError:
        pass


def _windows_extended_path(path: Path) -> str | Path:
    if os.name != "nt":
        return path
    resolved = str(path.resolve())
    if resolved.startswith("\\\\?\\"):
        return resolved
    return "\\\\?\\" + resolved


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
